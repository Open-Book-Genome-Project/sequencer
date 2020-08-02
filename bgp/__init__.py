#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    __init__.py
    ~~~~~~~~~~~

    :copyright: (c) 2020 by OBGP
    :license: see LICENSE for more details.
"""

__title__ = 'bgp'
__version__ = '0.0.34'
__author__ = 'OBGP'

import copy
import json
import tempfile
import internetarchive as ia
from bs4 import BeautifulSoup
from bgp.config import S3_KEYS
from bgp.utils import STOP_WORDS
from bgp.modules.terms import NGramProcessor, FulltextProcessor
from bgp.modules.terms import (
    WordFreqModule, UrlExtractorModule, IsbnExtractorModule,
    ReadingLevelModule
)
from bgp.modules.pagetypes import PageTypeProcessor
from bgp.modules.pagetypes import KeywordPageDetectorModule

IA = ia.get_session({'s3': S3_KEYS})
ia.get_item = IA.get_item

def _memoize_xml(self):
    if not hasattr(self, '_xml'):
        self._xml = self.download(formats=['Djvu XML'], return_responses=True)[0].text
    return self._xml

def _memoize_plaintext(self):
    """If converts xml to plaintext (only when needed) and memoizes result"""
    if hasattr(self, 'xml'):
        if not hasattr(self, '_plaintext'):
            self._plaintext = BeautifulSoup(self.xml, features="lxml").text
        return self._plaintext

def upload_sequence_to_item(self, itemid, results, filename='results.json'):
    with tempfile.NamedTemporaryFile() as tmp:
        json.dump(results, tmp)
        self.upload(
            itemid, {'%s_%s' % (self.book.identifier, filename): tmp},
            access_key=S3_KEYS.get('access'),
            secret_key=S3_KEYS.get('secret'))
    
def get_book_items(self, query, rows=100, page=1):
    """
    :param str query: an search query for selecting/faceting books
    :param int rows: limit how many results returned
    :param int page: starting page to offset search results
    :return: An `internetarchive` Item
    :rtype: `internetarchive` Item
    """
    params = {'page': page, 'rows': rows, 'scope': 'all'}
    return ia.s.search_items(query, params=params).iter_as_items()


ia.Item.xml = property(_memoize_xml)
ia.Item.plaintext = property(_memoize_plaintext)
ia.Item.get_book_items = get_book_items
ia.Item.upload_sequence_to_item = upload_sequence_to_item

class Sequencer:

    class Sequence:
        def __init__(self, pipeline):
            self.pipeline = pipeline

        @property
        def results(self):
            return {p: self.pipeline[p].results for p in self.pipeline}

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def sequence(self, book):
        """
        :param [NGramProcessor] pipeline: a list of NGramProcessors that run modules
        :param  [str|ia.Item] book: an Archive.org book Item or Item.identifier
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        """
        sq = self.Sequence(copy.deepcopy(self.pipeline))
        sq.book = book if type(book) is ia.Item else ia.get_item(book)
        for p in sq.pipeline:
            sq.pipeline[p].run(sq.book)
        return sq

DEFAULT_SEQUENCER = Sequencer({
    '2grams': NGramProcessor(modules={
        'term_freq': WordFreqModule()
    }, n=2, threshold=2, stop_words=STOP_WORDS),
    '1grams': NGramProcessor(modules={
        'term_freq': WordFreqModule(),
        'isbns': IsbnExtractorModule(),
        'urls': UrlExtractorModule()
    }, n=1, stop_words=None),
    'readinglevel': FulltextProcessor(modules={
        'flesch_kincaid_grade': ReadingLevelModule()
    }),
    'pagetypes': PageTypeProcessor(modules={
        'copyright_page': KeywordPageDetectorModule(keyword='copyright')
    })
})
