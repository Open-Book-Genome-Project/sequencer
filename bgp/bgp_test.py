import unittest

from bgp import ia
from bgp.utils import STOP_WORDS
from bgp.modules.terms import NGramProcessor

try:  # TODO: create bgp.runner
    from bgp import DEFAULT_SEQUENCER
except ImportError:
    class DEFAULT_SEQUENCER:
        @classmethod
        def sequence(cls, book):
            class dummy_genome:
                results = {'pagetypes': {'copyright_page': ['0004']}}
            return dummy_genome

item_id = '9780262517638OpenAccess'
book = ia.get_item(item_id)
genome = DEFAULT_SEQUENCER.sequence(book)


class TestSequencer(unittest.TestCase):

    def test_smoketest(self):
        genome = DEFAULT_SEQUENCER.sequence('arcadeflyer_the-ninja-kids')
    
    def test_copyright_page_detection(self):
        assert genome.results['copyright_page'][0] == {
            'isbns': ['9780262517638'],
            'page': '0004'
        }

    def test_stop_words(self):
        book = "be be water be a small a any anyhow anyone 2 3 4 5 anything anyway anywhere are around at back be became because become becomes becoming been before beforehand behind being below beside besides between beyond both bottom but by call can cannot could did do does doing melon be"
        ngrams = NGramProcessor.fulltext_to_ngrams(book, n=2, stop_words=STOP_WORDS)
        assert ngrams == ['water small', 'small melon'], ngrams
