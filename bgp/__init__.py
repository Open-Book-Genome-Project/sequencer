"""
    __init__.py
    ~~~~~~~~~~~

    :copyright: (c) 2020 by OBGP
    :license: see LICENSE for more details.
"""

__title__ = 'bgp'
__version__ = '0.0.36'
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
    KeywordPageDetectorModule,
    PageTypeProcessor
)
from bgp.utils import STOP_WORDS

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
        self._xml = self.download(formats=['Djvu XML'], return_responses=True)[0].text
        _memoize_xml_toc = time.perf_counter()
        self.xml_time = round(_memoize_xml_toc - _memoize_xml_tic, 3)
        self.xml_mem_kb = sys.getsizeof(self._xml)
    return self._xml

def _memoize_plaintext(self):
    """If converts xml to plaintext (only when needed) and memoizes result"""
    if hasattr(self, 'xml'):
        if not hasattr(self, '_plaintext'):
            _memoize_plaintext_tic = time.perf_counter()
            self._plaintext = self.download(formats=['DjVuTXT'], return_responses=True)[0].text
            _memoize_plaintext_toc = time.perf_counter()
            self.plaintext_time = round(_memoize_plaintext_toc - _memoize_plaintext_tic, 3)
            self.plaintext_mem_kb = sys.getsizeof(self._plaintext)
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


ia.get_book_items = get_book_items
ia.Item.xml = property(_memoize_xml)
ia.Item.plaintext = property(_memoize_plaintext)


class Sequencer:

    class Sequence:
        def __init__(self, pipeline):
            self.pipeline = pipeline
            self.total_time = 0

        def save(self, path=""):
            # trailing slash needed for path
            if getattr(self, 'book'):
                if path and not os.path.exists(path):
                    os.makedirs(path)
                with open(f"{path}{self.book.identifier}_genome.json", "w") as txt:
                    txt.write(json.dumps(self.results))

        def upload(self, itemid=None):
            if getattr(self, 'book'):
                itemid = itemid or self.book.identifier
                with tempfile.NamedTemporaryFile() as tmp:
                    tmp.write(json.dumps(self.results).encode())
                    tmp.flush()
                    ia.upload(itemid, {'%s_genome.json' % (itemid): tmp},
                              access_key=s3_keys['access'],
                              secret_key=s3_keys['secret'])

        @property
        def results(self):
            data = {p: self.pipeline[p].results for p in self.pipeline}
            data['total_time'] = self.total_time
            data['_memoize_xml'] = {
                'time': self.book.xml_time,
                'kb': self.book.xml_mem_kb
            }
            data['_memoize_plaintext'] = {
                'time': self.book.plaintext_time,
                'kb': self.book.plaintext_mem_kb
            }
            data['version'] = __version__
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
            sq.book = book if type(book) is ia.Item else ia.get_item(book)
            for p in sq.pipeline:
                sq.pipeline[p].run(sq.book)
            sequence_toc = time.perf_counter()
            sq.total_time = round(sequence_toc - sequence_tic, 3)
            return sq
        except IndexError:
            print(f"{sq.book.identifier} does not have DjvuXML and/or DjvuTXT to be sequenced!")
            logging.error(f"{sq.book.identifier} does not have DjvuXML and/or DjvuTXT to be sequenced!")
        except requests.exceptions.HTTPError:
            print(f"{sq.book.identifier} DjvuXML and/or DjvuTXT is forbidden and can't be sequenced!")
            logging.error(f"{sq.book.identifier} DjvuXML and/or DjvuTXT is forbidden and can't be sequenced!")

DEFAULT_SEQUENCER = Sequencer({
    '2grams': NGramProcessor(modules={
        'term_freq': WordFreqModule()
    }, n=2, threshold=2, stop_words=STOP_WORDS),
    '1grams': NGramProcessor(modules={
        'term_freq': WordFreqModule(),
        'isbns': IsbnExtractorModule(),
        'urls': UrlExtractorModule()
    }, n=1, stop_words=None),
    'fulltext': FulltextProcessor(modules={
        'readinglevel': ReadingLevelModule()
    }),
    'pagetypes': PageTypeProcessor(modules={
        'copyright_page': KeywordPageDetectorModule(keyword='copyright')
    })
})
