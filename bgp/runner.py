#!/usr/bin/env python
#-*-coding: utf-8 -*-


import time
from internetarchive import get_session, get_item, search_items
from bgp.config import S3_KEYS
from bgp.modules.terms import (
    NGramProcessor, WordFreqModule, UrlExtractorModule, IsbnExtractorModule,
    STOP_WORDS
)

class Sequencer:

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.ia = get_session({'s3': S3_KEYS})

    def get_book_items(self, query, rows=100, page=1):
        """
        :param str query: an search query for selecting/faceting books
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        :return: An `internetarchive` Item
        :rtype: `internetarchive` Item
        """
        params = {'page': page, 'rows': rows, 'scope': 'all'}
        return self.ia.search_items(query, params=params).iter_as_items()


    def run(self, query='collection:printdisabled', rows=100, page=1):
        """
        :param [NGramProcessor] pipeline: a list of NGramProcessors that run modules
        :param str query: an search query for selecting/faceting books
        :param int rows: limit how many results returned
        :param int page: starting page to offset search results
        """
        items = self.get_book_items(query, rows=rows, page=page)
        for i in items:
            fulltext = i.download(formats=['DjVuTXT'], return_responses=True)[0].text
            for p in self.pipeline:
                self.pipeline[p].run(fulltext)
        return self

    @property
    def results(self):
        return {p: self.pipeline[p].results for p in self.pipeline}

def test_sequencer(itemid='hpmor'):
    return Sequencer({
        '2grams': NGramProcessor(modules={
            'term_freq': WordFreqModule()
        }, n=2, stop_words=STOP_WORDS),
        '1grams': NGramProcessor(modules={
            'term_freq': WordFreqModule(),
            'isbns': IsbnExtractorModule(),
            'urls': UrlExtractorModule()
        }, n=1, stop_words=None)
    }).run(query="identifier:%s" % itemid)

    
if __name__ == "__main__":
    test_sequencer()
