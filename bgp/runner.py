#!/usr/bin/env python
#-*-coding: utf-8 -*-

import copy
import json
import time
import tempfile

from bgp import ia
from bgp.utils import STOP_WORDS


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
