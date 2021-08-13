import argparse
import concurrent.futures
import glob
import json
import os
import sys
import traceback

from bgp import MINIMAL_SEQUENCER, ia

parser = argparse.ArgumentParser(prog='[pipeline]',
                                 description='Automate Open Book Genome Project sequencer')

parser.add_argument('--processes',
                    action='store',
                    metavar='process-count',
                    type=int,
                    help='number of pipeline processes to run concurrently (default is 1)')

parser.add_argument('Path',
                    metavar='source-path',
                    type=str,
                    help='path to the jsonl file with ia identifiers')

args = parser.parse_args()

input_path = args.Path
process_count = args.processes

if not process_count:
    process_count = 1

if not os.path.isfile(input_path):
    print('The path specified does not exist')
    sys.exit()

RESULTS_PATH = 'results/bgp_results/'
books = []


def touch(identifier, record, data=None):
    file_name = '{}{}/{}_{}'.format(RESULTS_PATH, identifier, record, identifier)
    f = open(file_name, 'a')
    if data:
        f.write(data)
    f.close()


def db_isbn_extracted(identifier, isbn):
    touch(identifier, 'ISBN_{}'.format(isbn))


def db_isbn_none(identifier):
    touch(identifier, 'UPDATE_NONE')


def db_update_failed(identifier):
    touch(identifier, 'UPDATE_FAILED')


def db_update_succeed(identifier):
    if os.path.exists('{}{}/UPDATE_FAILED_{}'.format(RESULTS_PATH, identifier, identifier)):
        os.remove('{}{}/UPDATE_FAILED_{}'.format(RESULTS_PATH, identifier, identifier))
    if os.path.exists('{}{}/UPDATE_CONFLICT_{}'.format(RESULTS_PATH, identifier, identifier)):
        os.remove('{}{}/UPDATE_CONFLICT_{}'.format(RESULTS_PATH, identifier, identifier))
    touch(identifier, 'UPDATE_SUCCEED')


def db_update_conflict(identifier):
    touch(identifier, 'UPDATE_CONFLICT')


def db_urls_found(identifier, urls):
    urls_count = len(urls)
    urls_data = ''
    for url in urls:
        urls_data += '{}\n'.format(url)
    touch(identifier, 'URLS_{}'.format(urls_count), data=urls_data)


def db_genome_updated(identifier):
    touch(identifier, 'GENOME_UPDATED')


def db_sequence_success(identifier):
    if os.path.exists('{}{}/SEQUENCE_FAILURE_{}'.format(RESULTS_PATH, identifier, identifier)):
        os.remove('{}{}/SEQUENCE_FAILURE_{}'.format(RESULTS_PATH, identifier, identifier))


def db_sequence_failure(identifier, exception):
    touch(identifier, 'SEQUENCE_FAILURE', data=str(exception))


def get_canonical_isbn(genome):
    c_isbns = None
    b_isbns = None
    if genome['pagetypes']['modules']['copyright_page']['results']:
        # ISBN's extracted from copyright page
        c_isbns = genome['pagetypes']['modules']['copyright_page']['results'][0]['isbns']
    if genome['pagetypes']['modules']['backpage_isbn']['results']:
        # ISBN's extracted from back page
        b_isbns = genome['pagetypes']['modules']['backpage_isbn']['results']

    if c_isbns and b_isbns and any(x in c_isbns for x in b_isbns):
        # Return matching ISBN from copyright page and back page
        return [x for x in c_isbns if x in b_isbns][0]
    elif c_isbns:
        # Return first ISBN on copyright page
        return c_isbns[0]
    elif b_isbns:
        # Return last isbn on back page
        return b_isbns[-1]


def update_isbn(genome):
    """
    Updates the Archive.org metadata for an item to add missing ISBN when possible.
    Considers any ISBN-like identifiers extracted from the book's sequenced genome
    in order to identify a canonical ISBN for this books.
    """
    itemid = genome.get('identifier')
    # Checks if ia item already has isbn
    item = ia.get_item(itemid)
    metadata = item.item_metadata['metadata']
    if 'isbn' in metadata:
        item_isbn = item.item_metadata['metadata']['isbn'][0]
    else:
        item_isbn = False
    genome_isbn = get_canonical_isbn(genome)
    if genome_isbn:
        db_isbn_extracted(itemid, genome_isbn)
        if not item_isbn:
            try:
                update = item.modify_metadata(dict(isbn=genome_isbn))
                if update.status_code == 200:
                    db_update_succeed(itemid)
            except Exception as e:
                db_update_failed(itemid)
                raise e
        else:
            db_update_conflict(itemid)
    else:
        db_isbn_none(itemid)


def extract_urls(genome):
    """
    Save item's extracted urls to database.
    """
    itemid = genome.get('identifier')
    urls = set([url for url in genome['1grams']['modules']['urls']['results'] if 'archive.org' not in url])
    db_urls_found(itemid, urls)


with open(input_path) as fin:
    for line in fin:
        books.append(json.loads(line.replace("\n", ""))['identifier'])
if RESULTS_PATH and not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)


def run_pipeline(book):
    try:
        genome = None
        if not os.path.exists('{}{}/'.format(RESULTS_PATH, book)):
            os.makedirs('{}{}/'.format(RESULTS_PATH, book))
        if not os.path.exists('{}{}/book_genome.json'.format(RESULTS_PATH, book)):
            genome = MINIMAL_SEQUENCER.sequence(book)
            genome.save(path=RESULTS_PATH)
            genome.upload()
            db_genome_updated(book)
            genome = genome.results
        if not genome:
            # Get genome from file if not in memory
            f = open('{}{}/book_genome.json'.format(RESULTS_PATH, book),)
            genome = json.load(f)
        update_failed = os.path.exists('{}{}/UPDATE_FAILED_{}'.format(RESULTS_PATH, book, book))
        isbn_attempted = glob.glob('{}{}/ISBN_*'.format(RESULTS_PATH, book))
        if update_failed or not isbn_attempted:
            update_isbn(genome)
        if not glob.glob('{}{}/URLS_*'.format(RESULTS_PATH, book)):
            extract_urls(genome)
        if not os.path.exists('{}{}/GENOME_UPDATED_{}'.format(RESULTS_PATH, book, book)):
            MINIMAL_SEQUENCER._upload(results=genome)
            db_genome_updated(book)
        db_sequence_success(book)
    except Exception:
        e = traceback.format_exc()
        db_sequence_failure(book, e)


executor = concurrent.futures.ProcessPoolExecutor(process_count)
futures = [executor.submit(run_pipeline, book) for book in books]
concurrent.futures.wait(futures)
