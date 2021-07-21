import argparse
import json
import os
import sys

from bgp import ia, DEFAULT_SEQUENCER

# TODO
# Switch logging to filesystem database
# Each function should be idempotent. What steps are there for each item. Program should be able to resume from any point of failure. If run multiple times won’t cause issues.
# Add documentation to pipeline to make more readable
# For db_* functions, if conflicting record exists, remove.

# Hit OL for ISBN info and save in folder
# Look into sqlite3

parser = argparse.ArgumentParser(prog='[pipeline]',
                                 description='Automate Open Book Genome Project sequencer')

parser.add_argument('Path',
                    metavar='source-path',
                    type=str,
                    help='path to the jsonl file with ia identifiers')

args = parser.parse_args()

input_path = args.Path

if not os.path.isfile(input_path):
    print('The path specified does not exist')
    sys.exit()

RESULTS_PATH = 'results/bgp_results/'
books = []


def touch(identifier, record, data=None):
    file_name = '{}{}/{}_{}'.format(RESULTS_PATH, identifier, record, identifier)
    if os.path.exists(file_name):
        raise Exception('DatabaseRecordConflict')
    else:
        f = open(file_name, 'a')
        if data: f.write(data)
        f.close()


def db_isbn_extracted(identifier, isbn):
    touch(identifier, 'ISBN_{}'.format(isbn))


def db_isbn_none(identifier):
    touch(identifier, 'UPDATE_NONE')


def db_update_failed(identifier):
    touch(identifier, 'UPDATE_FAILED')


def db_update_succeed(identifier):
    touch(identifier, 'UPDATE_SUCCEED')


def db_update_conflict(identifier):
    touch(identifier, 'UPDATE_CONFLICT')


def db_urls_found(identifier, urls):
    urls_count = len(urls)
    urls_data = ''
    for url in urls:
        urls_data += '{}\n'.format(url)
    touch(identifier, 'URLS_{}'.format(urls_count), data=urls_data)


def get_canonical_isbn(result):
    c_isbns = None
    b_isbns = None
    if any(result.results['pagetypes']['modules']['copyright_page']['results']):
        c_isbns = result.results['pagetypes']['modules']['copyright_page']['results'][0]['isbns']
    if any(result.results['pagetypes']['modules']['backpage_isbn']['results']):
        b_isbns = result.results['pagetypes']['modules']['backpage_isbn']['results']

    if c_isbns and b_isbns:
        return [x for x in c_isbns if x in b_isbns][0]
    elif b_isbns:
        return b_isbns[-1]
    elif c_isbns:
        return c_isbns[0]
    else:
        return None


def update_isbn(result):
    itemid = result.book.identifier
    # Checks if ia item already has isbn
    if 'isbn' in result.book.metadata:
        item_isbn = result.book.metadata['isbn'][0]
    else: item_isbn = False
    genome_isbn = get_canonical_isbn(result)
    if genome_isbn:
        db_isbn_extracted(itemid, genome_isbn)
        if not item_isbn:
            try:
                update = result.modify_metadata(dict(isbn=genome_isbn))
                if update.status_code == 200:
                    db_update_succeed(itemid)
            except Exception as e:
                db_update_failed(itemid)
                raise e
        else: db_update_conflict(itemid)
    else: db_isbn_none(itemid)


def extract_urls(result):
    itemid = result.book.identifier
    urls = set([url for url in result.results['1grams']['modules']['urls']['results'] if 'archive.org' not in url])
    db_urls_found(itemid, urls)


with open(input_path) as fin:
    for line in fin:
        books.append(json.loads(line.replace("\n", ""))['identifier'])
if RESULTS_PATH and not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

with open('run.log', 'a') as fout:
    for book in books:
        # done_books is redefined for each book because new books may have been added since sequence began
        done_books = set([iaid for iaid in os.listdir(RESULTS_PATH)])
        if book in done_books:
            print("Skipping: {}\n".format(book))
        else:
            try:
                result = DEFAULT_SEQUENCER.sequence(book)
                if result:
                    result.save(path=RESULTS_PATH)
                    update_isbn(result)
                    extract_urls(result)
                    fout.write("Success: {}\n".format(book))
            except Exception as e:
                fout.write("Failure: {} | {}\n".format(book, e))
        # Force log writing to disk from memory for each book
        fout.flush()
