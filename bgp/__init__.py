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

import json
import tempfile
import internetarchive as ia
from bs4 import BeautifulSoup
from bgp.config import S3_KEYS
from bgp.runner import Sequencer

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
