import os
import json

RESULTS_PATH = 'results/bgp_results/'
books = [doc['identifier'] for doc in json.load(open('2021-06-16-obgp_ids.json'))]
done_books = set([iaid.split('_genome.json')[0] for iaid in os.listdir(RESULTS_PATH)])

from bgp import ia, DEFAULT_SEQUENCER
with open('run.log', 'a') as fout:
    for book in books:
        if book in done_books:
            print("Skipping: %s\n" % book)
        else:
            try:
                result = DEFAULT_SEQUENCER.sequence(book)
                if result:
                    fout.write("Success: %s\n" % book)
                    result.save(path=RESULTS_PATH)
            except:
                fout.write("Failure: %s\n" % book)