Welcome to the Open Book Genome Project (OBGP) Sequencer™, an open-source Book Processing Pipeline of responsibly vetted community "[modules](https://github.com/Open-Book-Genome-Project/sequencer/tree/master/bgp/modules)" which classify, sequence, and fingerprint book fulltext to reveal public insights about Books.

## Quickstart

Want to get started immediately?

Try the [OBGP Sequencer™ Google Colab Notebook](https://colab.research.google.com/drive/1q3eBgrMeq1mfObzwYyS3VTIwGr5W7wtL?authuser=1):

## How it Works

Each month, the OBGP Sequencer™ gets run against the fulltext of more than 1M books, generating valuable public insights for book lovers and researchers around the globe. OBGP Sequencer™ consists of carefully vetted community-contributed [modules](https://github.com/Open-Book-Genome-Project/sequencer/tree/master/bgp/modules) which aim to responsibly [help increase the discoverability and usefulness of books](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#heading=h.dj2jqsxuy8my), e.g.:
- Identifying urls, isbns, and citations within the text
- Generating word frequency mappings
- Guessing grade reading levels

## Who we are

OBGP is an independent, community-run, not-for-profit committee of open-source and book enthusiasts who want to responsibly further the effort of making books as useful and accessible as possible.

## Installation

### Production

If you want to run the OBGP Sequencer™ pipeline, run:
```
pip install obgp
```

### Local Development

```
git clone https://github.com/Open-Book-Genome-Project/sequencer.git  # get the code
virtualenv venv && source venv/bin/activate  # setup a virtual environment
cd sequencer  # change into project directory
pip install -e .  # install the library (and re-run in project root as you make changes)
```

## Usage

Once you've install either the production code or build your developer code, you may proceed to start python and import the `runner.pipeline` with whatever modules you'd like.

Let's say you want to process the book https://archive.org/details/hpmor which has identifier `hpmor` on Archive.org. First, you would define your Sequencer as follows:

```python
>>> from bgp import Sequencer, STOP_WORDS
>>> from bgp.modules.terms import NGramProcessor, WordFreqModule
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

## Saving & Uploading Results

If your `internetarchive` tool is configured against an account with sufficient permissions, you can then upload your genome results back to an Archive.org item (we'll arbitrarily pick the identifier `bgp`) by running:

```
>>> genome.write_results_to_item('bgp')
```

This will upload the `genome.results` as json to <book_identifier>_results.json (e.g. `hpmor_results.json`) unless otherwise specified by overriding params.

You will then be able to see your file `hpmor_results.json` within the `bgp` item's file downloads: https://archive.org/download/bgp

If you want to run a default test to make sure everything works, try:

```python
>>> from bgp import DEFAULT_SEQUENCER
>>> genome = DEFAULT_SEQUENCER.sequence('9780262517638OpenAccess')
>>> genome.results
```

## Contributing a Module

1. Please [read the whitepaper](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#) and look through our community list of [proposed or requested modules](https://docs.google.com/document/d/1eybbw_qZ3EE9CJg868BhPuq5z_36Wq2G0Ki3Lkde9v8/edit?ts=5e5edcd1#heading=h.dj2jqsxuy8my)
2. [Propose a "module"](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) by creating a github issue
3. Get the code: Fork this git repository and clone it to your workspace. Create a new branch for your module (named after its corresponding github issue number and title: e.g. `git checkout -b 12/module/find-isbns`). Install
4. [Create a new module](https://github.com/Open-Book-Genome-Project/sequencer/new/master) to the `modules/` directory
5. Test your module locally using [Internet Archive's unrestricted collection of ~800k books](https://docs.google.com/document/d/10cNGGYrDFu0BJg-pUYYzKpjB1TWkqKspTZl2YG-yLJ4/edit?fbclid=IwAR3fx-LPu7D4zU1FbcehX2bIY1fNU_nvbqOiy5QpS0yGv_ILhVr73WHD-BI#heading=h.36kkw3g3gzos)
5. [open a Pull Request](https://github.com/Open-Book-Genome-Project/sequencer/compare) so your contribution may be reviewed.


## Technical Overview

- Book Genome Project extends/overloads @jjjake's `internetarchive` tool (invisibly using bad practices) in bgp/__init__.py with functions to fetch xml / plaintext (in a smart, memoized way)
- Programmer builds a Sequencer (which is a list) of Sequences (a Sequence essentially does 1-pass on the data). Currently, the only sequences we have are 1gram and 2gram and these could be done in a single pass.
- Each Sequence specified a list of modules to get run as it steps
- The result is the top-level Sequencer can print out its `.results` as a dict

### Sequencers, Processors & Modules

A `Sequencer` tells the Book Genome Project what tasks should be run and what results should be derived when processing a book's genome.

When a OGBP Sequencer is defined, it is loaded with a list of Processors, and these Processors with Modules.

A Processor is an abstraction which is responsible for fetching a specific representation of a Book (e.g. plaintext, xml, abbyy), splitting it into predefined logical units (e.g. characters, words, sentences, paragraphs, pages, chapters, entire text), stepping over each of these logical units, and sending them to it's registered Modules. 

One example hypothetrical Processor might be called `XMLSentenceProcessor`. This Processor may be responsible for fetching (i.e. downloading) a Book in XML format with word-level markup. The `run()` method of the Processor's interface might parse and split the structured XML data into sentences, iterate through each sentence, and forward them to each of its registered Modules for processing. This hypothetical `SentenceProcessor` might be loaded with several Modules, such as a `TotalSentenceCountModule` and an `SentenceWordCountStatsModule` which, respectively, keeps track of the total number of sentences within the book and calculates the average number of words per sentence, etc.

In many cases a developer may find that the package's out-of-the-box `bgp.DEFAULT_SEQUENCER` is a great place to start, either as a Sequencer to run or a good example for extending.

### Genome Schema
This is the reference schema used in genome json files:
```json
{
  "version": "(commit)",
  "timestamp": "r(Unix Epoch)",
  "total_time": "r(sequence process seconds)",
  "_memoize_plaintext": {
    "time": "r(txt download seconds)",
    "kb": "r(txt bytes)"
  },
  "_memoize_xml": {
    "time": "r(xml download seconds)",
    "kb": "r(xml bytes)"
  },
  "1grams": {
    "tokenization_time": "r(1gram tokenization process seconds)",
    "total_tokens": "r(1gram count)",
    "total_time": "r(1gram processor process seconds)",
    "modules": {
      "urls": {
        "time": "r(url process seconds)",
        "results": [
          "(url)"
        ]
      },
      "term_freq": {
        "time": "r(1gram frequency process seconds)",
        "results": [
          [
            "(1gram)",
            "r(1gram frequency)"
          ]
        ]
      }
    }
  },
  "2grams": {
    "tokenization_time": "r(2gram tokenization process seconds)",
    "total_tokens": "r(2gram count)",
    "total_time": "r(2gram processor process seconds)",
    "modules": {
      "term_freq": {
        "time": "r(2gram frequency process seconds)",
        "results": [
          [
            "(2gram)",
            "r(2gram frequency)"
          ]
        ]
      }
    }
  },
  "fulltext": {
    "total_time": "r(fulltext processor process seconds)",
    "modules": {
      "readinglevel": {
        "time": "r(reading level process seconds)",
        "results": {
          "readability": {
            "flesch_kincaid_score": "r(flesch kincaid score)",
            "smog_score": "r(smog score)"
          },
          "lexile": {
            "min_age": "(Lower age in range)",
            "max_age": "(Upper age in range)"
          }
        }
      }
    }
  },
  "pagetypes": {
    "total_time": "r(pagetype processor process seconds)",
    "modules": {
      "copyright_page": {
        "time": "r(copyright page process seconds)",
        "results": [
          {
            "page": "(copyright page)",
            "isbns": [
              "(isbn)"
            ]
          }
        ]
      },
      "backpage_isbn": {
        "results": [
          "(isbn)"
        ],
        "time": "r(copyright page process seconds)"
      }
    }
  }
}
```

## Public Testing Data sets

Here's a corpus of ~800k Archive.org item identifiers of public domain books (of varying quality/appearance/language) which may be used for testing your module:

https://archive.org/download/869k-public-domain-book-urls-dataset/2017-12-26_public-domain-books-dataset_800k-identifiers.csv (~19mb)

## Questions?
Please [open an issue](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) and [request a slack invite](mailto:hi@mek.fyi)
