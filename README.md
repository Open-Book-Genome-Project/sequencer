# Welcome

Welcome to the Open Book Genome Project (OBGP) Sequencer™, an open-source Book Processing Pipeline of responsibly vetted community "[modules](https://github.com/Open-Book-Genome-Project/sequencer/blob/master/modules)" which classify, sequence, and fingerprint book fulltext to reveal public insights.

## How it Works

Each month, the OBGP Sequencer™ gets run against the fulltext of more than 1M books, generating valuable public insights for book lovers and researchers around the globe. OBGP Sequencer™ consists of carefully vetted community-contributed [modules](https://github.com/Open-Book-Genome-Project/sequencer/blob/master/modules) which aim to responsibly [help increase the discoverability and usefulness of books](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#heading=h.dj2jqsxuy8my), e.g.:
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
6. Questions? Please [open an issue](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) or [Request a Slack Invite](mailto:hi@mek.fyi)

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
pip install -e .  # install the library (and re-run in project root as you make changes)
```
## Usage

Once you've install either the production code or build your developer code, you may proceed to start python and import the `runner.pipeline` with whatever modules you'd like†, e.g.:
```
>>> from bgp.runner import pipeline
>>> from bgp.modules import terms
>>> pipeline(terms)
```

† the pipeline is not fully running yet; the code as listed above will not fully work!

## Who we are

OBGP is an independent, community-run, not-for-profit committee of open-source and book enthusiasts who want to responsibly further the effort of making books as useful and accessible as possible.

## Public Testing Data sets

Here's a corpus of ~800k Archive.org item identifiers of public domain books (of varying quality/appearance/language) which may be used for testing your module:

https://archive.org/download/869k-public-domain-book-urls-dataset/2017-12-26_public-domain-books-dataset_800k-identifiers.csv (~19mb)