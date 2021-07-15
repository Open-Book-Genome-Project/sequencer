import argparse
import json
import os
import sys

from bgp import ia, DEFAULT_SEQUENCER

# TODO
# Switch to 1 folder per book
# genome named book_genome.json
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


def touch(identifier, record):
    file_name = '{}{}/{}_{}'.format(RESULTS_PATH, identifier, record, identifier)
    if os.path.exists(file_name):
        raise Exception('DatabaseRecordConflict')
    else:
        open(file_name, 'a').close()


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


def update_isbn(result):
    itemid = result.book.identifer
    item_isbn = 'isbn' in result.book.metadata and result.book.metadata['isbn'][0]
    c_isbns = result.results['pagetypes']['modules']['copyright_page']['results'][0]['isbns']
    b_isbns = result.results['pagetypes']['modules']['backpage_isbn']['results']

    if c_isbns and b_isbns:
        genome_isbn = [x for x in c_isbns if x in b_isbns]
    elif b_isbns:
        genome_isbn = [b_isbns[-1]]
    elif c_isbns:
        genome_isbn = [c_isbns[0]]

    if genome_isbn:
        db_isbn_extracted(itemid, genome_isbn)
        if not genome_isbn == item_isbn:
            update = result.modify_metadata(dict(isbn=genome_isbn))
            if update.status_code == 200:
                db_update_succeed(itemid)
            else: db_update_failed(itemid)
        else: db_update_conflict(itemid)
    else: db_isbn_none(itemid)


with open(input_path) as fin:
    for line in fin:
        books.append(json.loads(line.replace("\n", ""))['identifier'])
done_books = set([iaid.split('_genome.json')[0] for iaid in os.listdir(RESULTS_PATH)])

with open('run.log', 'a') as fout:
    for book in books:
        if book in done_books:
            print("Skipping: {}\n".format(book))
        else:
            try:
                result = DEFAULT_SEQUENCER.sequence(book)
                if result:
                    fout.write("Success: {}\n".format(book))
                    result.save(path=RESULTS_PATH)
                    update_isbn(result)
            except Exception as e:
                fout.write("Failure: {} | {}\n".format(book, e))
        # Force log writing to disk from memory for each book
        fout.flush()
