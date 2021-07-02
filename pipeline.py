import os
import json

from bgp import ia, DEFAULT_SEQUENCER

RESULTS_PATH = 'results/bgp_results/'
books = []
with open('2021-06-16-obgp_ids.jsonl') as fin:
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
