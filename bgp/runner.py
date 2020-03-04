#!/usr/bin/env python
#-*-coding: utf-8 -*-

import time
from functools import partial
from internetarchive import get_session, modify_metadata, get_item, search_items
from bgp.modules import terms
from config import S3_KEYS

# A list of tasks/transformations which may be run
TASKS = {
    'frequency': {
        'function': terms.sequence,
        'args': ['fulltext']
    },
    '2-grams': {
        'function': partial(terms.sequence, n=2, include_stopwords=False),
        'args': ['fulltext']
    }
}

def get_fulltext(item):
    filename = item.id
    with open(filename) as book:
        return sequence(book.read(), n=n)


def get_lendable_book_items(page=1, rows=100, collection='printdisabled'):
    s = get_session({'s3': S3_KEYS})
    params = {'page': page, 'rows': rows, 'scope': 'all'}
    q = 'collection:%s' % collection
    return s.search_items(q, params=params).iter_as_items()


def pipeline(tasks=None, page=1, rows=None):
    items = get_lendable_book_items(page=page, rows=rows)
    for i in items:
        if tasks:
            for t in tasks:
                # For now, assume tasks func takes fulltext
                fulltext = i.download(formats=['DjVuTXT'])
                #TASKS[t]['function']()
                
if __name__ == "__main__":
    # Test code
    pipeline('terms', rows=1)


