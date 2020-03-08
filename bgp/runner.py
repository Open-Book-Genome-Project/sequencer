#!/usr/bin/env python
#-*-coding: utf-8 -*-

import copy
import json
import time
import tempfile
from functools import partial
import internetarchive as ia
from bgp.config import S3_KEYS
from bgp.modules.terms import (
    NGramProcessor, WordFreqModule, UrlExtractorModule, IsbnExtractorModule,
    STOP_WORDS
)

IA = ia.get_session({'s3': S3_KEYS})

class Sequencer:

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def get_book_items(self, query, rows=100, page=1):
        """
        :param str query: an search query for selecting/faceting books
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        :return: An `internetarchive` Item
        :rtype: `internetarchive` Item
        """
        params = {'page': page, 'rows': rows, 'scope': 'all'}
        return IA.search_items(query, params=params).iter_as_items()

    def sequence(self, book):
        """
        :param [NGramProcessor] pipeline: a list of NGramProcessors that run modules
        :param  [str|ia.Item] book: an Archive.org book Item or Item.identifier
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        """
        book = book if type(book) is ia.Item else IA.get_item(book)
        fulltext = book.download(
            formats=['DjVuTXT'], return_responses=True)[0].text
        sq = Sequence(copy.deepcopy(self.pipeline), book)
        for p in sq.pipeline:
            sq.pipeline[p].run(fulltext)
        return sq


class Sequence:

    def __init__(self, pipeline, book):
        self.book = book
        self.pipeline = pipeline

    @property
    def results(self):
        return {p: self.pipeline[p].results for p in self.pipeline}

    def write_results_to_item(self, itemid, filename='results.json'):
        with tempfile.NamedTemporaryFile() as tmp:
            json.dump(self.results, tmp)
            ia.upload(
                itemid, {'%s_%s' % (self.book.identifier, filename): tmp},
                access_key=S3_KEYS.get('access'),
                secret_key=S3_KEYS.get('secret')
            )


def test_sequence_item(itemid):
    s = Sequencer({
        '2grams': NGramProcessor(modules={
            'term_freq': WordFreqModule()
        }, n=2, stop_words=STOP_WORDS),
        '1grams': NGramProcessor(modules={
            'term_freq': WordFreqModule(),
            'isbns': IsbnExtractorModule(),
            'urls': UrlExtractorModule()
        }, n=1, stop_words=None)
    })
    return s.sequence(itemid)


if __name__ == "__main__":
    genome = test_sequence_item('hpmor')
