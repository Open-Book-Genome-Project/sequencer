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
from bgp import Sequencer, STOP_WORDS
from bgp.modules.terms import NGramProcessor, WordFreqModule
s = Sequencer({
    'words': NGramProcessor(modules={
        'term_freq': WordFreqModule()
    }, n=1, stop_words=STOP_WORDS)
})
```

Then, you would pass this book identifier into the Sequencer to sequence the book to get back a genome Sequence object:

```python
genome = s.sequence('hpmor')
genome.results
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
from bgp import DEFAULT_SEQUENCER
genome = DEFAULT_SEQUENCER.sequence('9780262517638OpenAccess')
genome.results
```

## Using pipeline.py

This pipeline allows a user to sequence a list of books from a jsonl in the following format:

```jsonl
{"identifier": "samplebook"}
{"identifier": "9780262517638OpenAccess"}
```

The pipeline then automatically chooses the most probable isbn for the book and attempts to update ia metadata accordingly while keeping a filesystem based database of all these actions.


|Record|Filesystem Action|
| ---- | ---- |
| How do we determine which books we've successfully uploaded a genome     | Touches `GENOME_UPDATED_{identifier}`    |
| How do we determine the ISBNs of all books we’ve sequenced so far    | Touches `ISBN_1234567890_{identifier}`    |
| How do we determine which books were sequenced but had no ISBN     | Touches `UPDATE_NONE_{identifier}`    |
| How do we know which books attempted updating but failed     | `UPDATE_FAILED_{identifier}`     |
| How do we know which books succeeded at updating and succeed     | `UPDATE_SUCCEED_{identifier}`     |
| How do we know if item already has isbn metadata and is skipped     | `UPDATE_CONFLICT_{identifier}`     |
| How do we know how many new urls were found in a book     | `URLS_{number_of_urls}_{identifier}`     |

The user can can grep and pipe to wc -l which tells them how many for each status and lists those items


### Example Usage

Here is a archive item with the identifier `samplebook`. It has an isbn in the text of the book but no isbn metadata.

<img width="638" alt="Screen Shot 2021-07-15 at 6 06 08 PM" src="https://user-images.githubusercontent.com/6785029/125876309-efed1316-96a2-47fb-a874-77169be15529.png">

There is a jsonl file with the items to be sequenced listed on new lines.

```jsonl
{"identifier": "samplebook"}
{"identifier": "9780262517638OpenAccess"}
```

To use the pipeline, run `python pipeline.py samplebook.jsonl`

You can specify the amount of pipeline processes to run concurrently with `--p {number of processes}` as a parameter. For example: `python pipeline.py --p 4 samplebook.jsonl`

If we `tree results/bgp_results` now we get:

```
results/bgp_results
├── 9780262517638OpenAccess
│   ├── ISBN_9780262517638_9780262517638OpenAccess
│   ├── UPDATE_CONFLICT_9780262517638OpenAccess
│   ├── URLS_290_9780262517638OpenAccess
│   └── book_genome.json
└── samplebook
    ├── ISBN_0787959529_samplebook
    ├── UPDATE_SUCCEED_samplebook
    ├── URLS_0_samplebook
    └── book_genome.json

2 directories, 8 files
```

If we check the metadata for the book on archive.org again we can see that the isbn field has been updated.

<img width="638" alt="Screen Shot 2021-07-15 at 6 06 08 PM" src="https://user-images.githubusercontent.com/6785029/125876475-976495e1-05ac-465d-bac6-6fd8fe9ca5cb.png">

There is also a file generated named `URLS_0_samplebook` which indicates that 0 non 'archive.org' were extracted.

In the case of another item like `9780262517638OpenAccess`, the filename indicates that 290 new urls were extracted. If we look at the contents of that file we will see all the unique urls extracted separated by newlines.

```
http://blogs.law.harvard.edu/pamphlet/2009/05/29/what-percentage
http://www.sherpa.ac.uk/romeo
http://www.library.yale.edu/~llicense/listarchives/0405/msg00038
http://dash.harvard.edu/bitstream/handle/l/4552050/suber_nofee
http://dx.doi.org/10.1371/journal.pone.0013636
http://doctorrw.blogspot.com/2007/05/tabloid-based-medicine
... etc.
```

The `9780262517638OpenAccess` directory also shows that a url was extracted with the `ISBN_9780262517638_9780262517638OpenAccess` record, but was the ia item was not updated because a isbn already existed with the `UPDATE_CONFLICT_9780262517638OpenAccess`


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
  "metadata": {
    "identifier": "(ia identifier)",
    "version": "(commit)",
    "timestamp": "r(Unix Epoch)",
    "sequence_time": "r(sequence process seconds)",
    "source": {
      "txt": {
        "time": "r(txt download seconds)",
        "bytes": "r(txt bytes)"
      },
      "xml": {
        "time": "r(xml download seconds)",
        "bytes": "r(xml bytes)"
      }
    },
    "processors": {
      "1gram": {
        "tokenization_time": "r(1gram tokenization process seconds)",
        "total_tokens": "r(1gram count)",
        "total_time": "r(1gram processor process seconds)",
        "modules": {
          "urls": {
            "time": "r(url process seconds)"
          },
          "1grams": {
            "time": "r(1gram frequency process seconds)"
          }
        }
      },
      "2gram": {
        "tokenization_time": "r(2gram tokenization process seconds)",
        "total_tokens": "r(2gram count)",
        "total_time": "r(2gram processor process seconds)",
        "modules": {
          "2grams": {
            "time": "r(2gram frequency process seconds)"
          }
        }
      },
      "fulltext": {
        "total_time": "r(fulltext processor process seconds)",
        "modules": {
          "readinglevel": {
            "time": "r(reading level process seconds)"
          }
        }
      },
      "pagetypes": {
        "total_time": "r(pagetype processor process seconds)",
        "modules": {
          "copyright_page": {
            "time": "r(copyright page process seconds)"
          },
          "backpage_isbn": {
            "time": "r(copyright page process seconds)"
          }
        }
      }
    }
  },
  "urls": [
              "(url)"
            ],
  "1grams": [
              [
                "(1gram)",
                "r(1gram frequency)"
              ]
            ],
  "2grams": [
              [
                "(2gram)",
                "r(2gram frequency)"
              ]
            ],
  "readinglevel": {
              "readability": {
                "flesch_kincaid_score": "r(flesch kincaid score)",
                "smog_score": "r(smog score)"
              },
              "lexile": {
                "min_age": "(Lower age in range)",
                "max_age": "(Upper age in range)"
              }
            },
  "copyright_page": [
              {
                "page": "(copyright page)",
                "isbns": [
                  "(isbn)"
                ]
              }
            ],
  "backpage_isbn": [
              "(isbn)"
            ]
}
```

## Public Testing Data sets

Here's a corpus of ~800k Archive.org item identifiers of public domain books (of varying quality/appearance/language) which may be used for testing your module:

https://archive.org/download/869k-public-domain-book-urls-dataset/2017-12-26_public-domain-books-dataset_800k-identifiers.csv (~19mb)

## Questions?
Please [open an issue](https://github.com/Open-Book-Genome-Project/sequencer/issues/new) and [request a slack invite](mailto:hi@mek.fyi)
