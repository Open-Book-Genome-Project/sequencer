# Welcome

Welcome to the Open Book Genome Project (OBGP) Sequencer™, an open-source Book Processing Pipeline of responsibly vetted community "[modules](https://github.com/Open-Book-Genome-Project/sequencer/tree/master/bgp/modules)" which classify, sequence, and fingerprint book fulltext to reveal public insights.

## How it Works

Each month, the OBGP Sequencer™ gets run against the fulltext of more than 1M books, generating valuable public insights for book lovers and researchers around the globe. OBGP Sequencer™ consists of carefully vetted community-contributed [modules](https://github.com/Open-Book-Genome-Project/sequencer/tree/master/bgp/modules) which aim to responsibly [help increase the discoverability and usefulness of books](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#heading=h.dj2jqsxuy8my), e.g.:
- Identifying urls, isbns, and citations within the text
- Generating word frequency mappings
- Guessing grade reading levels

## Contributing a Module

1. Please [read the whitepaper](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#) and look through our community list of [proposed or requested modules](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#heading=h.dj2jqsxuy8my)
2. [Propose a "module"](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) by creating a github issue
3. Get the code: Fork this git repository and clone it to your workspace. Ceate a new branch for your module (named after its corresponding github issue number and title: e.g. `git checkout -b 12/module/find-isbns`). Install
4. [Create a new module](https://github.com/Open-Book-Genome-Project/sequencer/new/master) to the `modules/` directory
5. Test your module locally using [Internet Archive's unrestricted collection of ~800k books](https://docs.google.com/document/d/10cNGGYrDFu0BJg-pUYYzKpjB1TWkqKspTZl2YG-yLJ4/edit?fbclid=IwAR3fx-LPu7D4zU1FbcehX2bIY1fNU_nvbqOiy5QpS0yGv_ILhVr73WHD-BI#heading=h.36kkw3g3gzos)
5. [open a Pull Request](https://github.com/Open-Book-Genome-Project/sequencer/compare) so your contribution may be reviewed.

## Questions?
Please [open an issue](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) and [request a slack invite](mailto:hi@mek.fyi)

## Installation

### Production

If you want to run the OBGP Sequencer™ pipeline, run:
```
pip install obgp
```
### Development

```
git clone https://github.com/Open-Book-Genome-Project/sequencer.git  # get the code
virtualenv venv && source venv/bin/activate  # setup a virtual environment
cd sequencer  # change into project directory
pip install -e .  # install the library (and re-run in project root as you make changes)
```

## Technical Overview

- Book Genome Project extends/overloads @jjjake's `internetarchive` tool (invisibly using bad practices) in bgp/__init__.py with functions to fetch xml / plaintext (in a smart, memoized way)
- Programmer builds a Sequencer (which is a list) of Sequences (a Sequence essentially does 1-pass on the data). Currently, the only sequences we have are 1gram and 2gram and these could be done in a single pass.
- Each Sequence specified a list of modules to get run as it steps
- The result is the top-level Sequencer can print out its `.results` as a dict

## Usage

Once you've install either the production code or build your developer code, you may proceed to start python and import the `runner.pipeline` with whatever modules you'd like.

Let's say you want to process the book https://archive.org/details/hpmor which has identifier `hpmor` on Archive.org. First, you would define your Sequencer as follows:

```python
>>> from bgp.runner import Sequencer, NGramProcessor, WordFreqModule, STOP_WORDS
>>> s = Sequencer({
...     'words': NGramProcessor(modules={
...         'term_freq': WordFreqModule()
...     }, n=1, stop_words=STOP_WORDS)
... })
```

Then, you would pass this book identifier into the Sequencer to sequence the book to get back a genome Sequence object:

```python
>>> genome = s.sequence('hpmor')
>>> genome.results
```

If your `internetarchive` tool is configured against an account with sufficient permissions, you can then upload your genome results back to an Archive.org item (we'll arbitrarily pick the identifier `bgp`) by running:

```
>>> genome.write_results_to_item('bgp')
```

This will upload the `genome.results` as json to <book_identifier>_results.json (e.g. `hpmor_results.json`) unless otherwise specificed by overriding params.

You will then be able to see your file `hpmor_results.json` within the `bgp` item's file downloads: https://archive.org/download/bgp

If you want to run a default test to make sure everything works, try:

```python
>>> from bgp import test_sequence_item
>>> genome = test_sequence_item('hpmor')
>>> genome.results
```

## Who we are

OBGP is an independent, community-run, not-for-profit committee of open-source and book enthusiasts who want to responsibly further the effort of making books as useful and accessible as possible.

## Public Testing Data sets

Here's a corpus of ~800k Archive.org item identifiers of public domain books (of varying quality/appearance/language) which may be used for testing your module:

https://archive.org/download/869k-public-domain-book-urls-dataset/2017-12-26_public-domain-books-dataset_800k-identifiers.csv (~19mb)
