#!/usr/bin/env python
#-*-coding: utf-8 -*-

import copy
import json
import time
import tempfile

from bgp import ia
from bgp.config import S3_KEYS
from bgp.modules.terms import (
    NGramProcessor, WordFreqModule, UrlExtractorModule, IsbnExtractorModule,
    STOP_WORDS
)
   

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
        book = book if type(book) is ia.Item else IA.get_item(book)
        sq = self.Sequence(copy.deepcopy(self.pipeline))
        for p in sq.pipeline:
            sq.pipeline[p].run(book)
        return sq


DEFAULT_SEQUENCER = Sequencer({
    '2grams': NGramProcessor(modules={
        'term_freq': WordFreqModule()
    }, n=2, stop_words=STOP_WORDS),
    '1grams': NGramProcessor(modules={
        'term_freq': WordFreqModule(),
        'isbns': IsbnExtractorModule(),
        'urls': UrlExtractorModule()
    }, n=1, stop_words=None)
})


def test_sequence_item(itemid):
    book = ia.get_item(itemid)
    genome = DEFAULT_SEQUENCER.sequence(book)
    return genome


if __name__ == "__main__":
    genome = test_sequence_item('hpmor')
