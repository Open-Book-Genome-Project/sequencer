import argparse
import json
import os
import sys

from bgp import ia, DEFAULT_SEQUENCER

# TODO
# Make identifiers file passed as param
# Switch to 1 folder per book
# genome named book_genome.json
# Make functions for UPLOADED, ISBN_ADDED, DATE_ADDED
# Hit OL for ISBN info and save in folder
# Create test ia items
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
            except Exception as e:
                fout.write("Failure: {} | {}\n".format(book, e))
        # Force log writing to disk from memory for each book
        fout.flush()
