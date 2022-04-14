"""
    __init__.py
    ~~~~~~~~~~~

    :copyright: (c) 2020 by OBGP
    :license: see LICENSE for more details.
"""

__title__ = 'bgp'
__author__ = 'OBGP'

import copy
import json
import logging
import os
import requests
import sys
import tempfile
import time

import internetarchive as ia
from bs4 import BeautifulSoup
from internetarchive.config import get_config

from bgp.modules.terms import (
    FulltextProcessor,
    IsbnExtractorModule,
    NGramProcessor,
    ReadingLevelModule,
    UrlExtractorModule,
    WordFreqModule,
    CopyrightPageDetectorModule,
    PageTypeProcessor,
    BackpageIsbnExtractorModule
)
from bgp.utils import STOP_WORDS
from subprocess import PIPE, Popen, STDOUT

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='obgp_errors.log')

s3_keys = get_config().get('s3')

IA = ia.get_session(s3_keys)
ia.get_item = IA.get_item

def _memoize_xml(self):
    if not hasattr(self, '_xml'):
        _memoize_xml_tic = time.perf_counter()
        try:
            self._xml = self.download(formats=['Djvu XML'], return_responses=True)[0].text
        except requests.exceptions.Timeout as e:
            logging.error('Timeout getting xml for item - ' + self.identifier + ' | ' + str(e))
            raise Exception('Timeout getting xml for item - ' + self.identifier)
        _memoize_xml_toc = time.perf_counter()
        self.xml_time = round(_memoize_xml_toc - _memoize_xml_tic, 3)
        self.xml_bytes = sys.getsizeof(self._xml)
    return self._xml

def _memoize_plaintext(self):
    if not hasattr(self, '_plaintext'):
        _memoize_plaintext_tic = time.perf_counter()
        try:
            self._plaintext = self.download(formats=['DjVuTXT'], return_responses=True)[0].text
        except requests.exceptions.Timeout as e:
            logging.error('Timeout getting txt for item - ' + self.identifier + ' | ' + str(e))
            raise Exception('Timeout getting txt for item - ' + self.identifier)
        _memoize_plaintext_toc = time.perf_counter()
        self.plaintext_time = round(_memoize_plaintext_toc - _memoize_plaintext_tic, 3)
        self.plaintext_bytes = sys.getsizeof(self._plaintext)
    return self._plaintext

def get_book_items(query, rows=100, page=1, scope_all=False):
    """
    :param str query: an search query for selecting/faceting books
    :param int rows: limit how many results returned
    :param int page: starting page to offset search results
    :return: An `internetarchive` Item
    :rtype: `internetarchive` Item
    """
    params = {'page': page, 'rows': rows}
    if scope_all:
        params['scope'] = 'all'
    # this may need to get run as a session (priv'd access)
    return ia.search_items(query, params=params).iter_as_items()

def get_software_version():  # -> str:
    cmd = "git rev-parse --short HEAD --".split()
    return str(Popen(cmd, stdout=PIPE, stderr=STDOUT).stdout.read().decode().strip())


ia.get_book_items = get_book_items
ia.Item.xml = property(_memoize_xml)
ia.Item.plaintext = property(_memoize_plaintext)


class Sequencer:

    class Sequence:
        def __init__(self, pipeline):
            self.pipeline = pipeline
            self.sequence_time = 0

        def save(self, path=''):
            item_path = path + self.book.identifier + '/'
            # trailing slash needed for path
            if getattr(self, 'book'):
                if item_path and not os.path.exists(item_path):
                    os.makedirs(item_path)
                with open(item_path + 'book_genome.json', 'w') as txt:
                    txt.write(json.dumps(self.results))

        def upload(self):
            Sequencer._upload(results=self.results)

        @property
        def results(self):
            data = {}
            meta = {}
            processors = {}
            for processor in self.pipeline:
                processor_meta = self.pipeline[processor].results
                # Remove module results from processor metadata dict
                processor_meta.update({'modules': {}})
                processors.update({processor: processor_meta})
                for module in self.pipeline[processor].modules:
                    # Add module results to root level of dict
                    data[module] = self.pipeline[processor].results['modules'][module]['results']
                    module_meta = self.pipeline[processor].results['modules'][module]
                    # Remove module results from module metadata dict
                    module_meta.pop('results')
                    processors[processor]['modules'].update({module: module_meta})
            meta['processors'] = processors
            meta['sequence_time'] = self.sequence_time
            meta['source'] = {
                'xml': {
                    'time': getattr(self.book, 'xml_time', None),
                    'bytes': getattr(self.book, 'xml_bytes', None),
                },
                'txt': {
                    'time': getattr(self.book, 'plaintext_time', None),
                    'bytes': getattr(self.book, 'plaintext_bytes', None),
                }
            }
            meta['version'] = get_software_version()
            meta['timestamp'] = time.time()
            meta['identifier'] = self.book.identifier
            data['metadata'] = meta
            return data

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def sequence(self, book):
        """
        :param [NGramProcessor] pipeline: a list of NGramProcessors that run modules
        :param  [str|ia.Item] book: an Archive.org book Item or Item.identifier
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        """
        try:
            sequence_tic = time.perf_counter()
            sq = self.Sequence(copy.deepcopy(self.pipeline))
            try:
                sq.book = book if type(book) is ia.Item else ia.get_item(book)
            except requests.exceptions.ConnectionError:
                raise Exception('Connection error retrieving metadata for - ' + book)
                logging.error('Connection error retrieving metadata for - ' + book)
            if sq.book.exists:
                for p in sq.pipeline:
                    sq.pipeline[p].run(sq.book)
                sequence_toc = time.perf_counter()
                sq.sequence_time = round(sequence_toc - sequence_tic, 3)
                return sq
            else:
                raise Exception(sq.book.identifier + ' - Item cannot be found.')
                logging.error(sq.book.identifier + ' - Item cannot be found.')
        except IndexError:
            raise Exception(sq.book.identifier + ' - does not have DjvuXML and/or DjvuTXT to be sequenced!')
            logging.error(sq.book.identifier + ' - does not have DjvuXML and/or DjvuTXT to be sequenced!')
        except requests.exceptions.HTTPError:
            raise Exception(sq.book.identifier + ' - DjvuXML and/or DjvuTXT is forbidden and can\'t be sequenced!')
            logging.error(sq.book.identifier + ' - DjvuXML and/or DjvuTXT is forbidden and can\'t be sequenced!')

    @classmethod
    def _upload(cls, results=None):
        itemid = results.get('metadata').get('identifier')
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(json.dumps(results).encode())
            tmp.flush()
            ia.upload(itemid, {'book_genome.json': tmp},
                      access_key=s3_keys['access'],
                      secret_key=s3_keys['secret'])

DEFAULT_SEQUENCER = Sequencer({
    '3gram': NGramProcessor(modules={
        '3grams': WordFreqModule()
    }, n=3, threshold=2, stop_words=None),
    '2gram': NGramProcessor(modules={
        '2grams': WordFreqModule()
    }, n=2, threshold=3, stop_words=STOP_WORDS),
    '1gram': NGramProcessor(modules={
        '1grams': WordFreqModule(),
        'urls': UrlExtractorModule()
    }, n=1, stop_words=None),
    'fulltext': FulltextProcessor(modules={
        'readinglevel': ReadingLevelModule()
    }),
    'pagetypes': PageTypeProcessor(modules={
        'copyright_page': CopyrightPageDetectorModule(),
        'backpage_isbn': BackpageIsbnExtractorModule()
    })
})

MINIMAL_SEQUENCER = Sequencer({
    '2gram': NGramProcessor(modules={
        '2grams': WordFreqModule()
    }, n=2, threshold=2, stop_words=STOP_WORDS),
    '1gram': NGramProcessor(modules={
        '1grams': WordFreqModule(),
        'urls': UrlExtractorModule()
    }, n=1, stop_words=None),
    'pagetypes': PageTypeProcessor(modules={
        'copyright_page': CopyrightPageDetectorModule(),
        'backpage_isbn': BackpageIsbnExtractorModule()
    })
})
