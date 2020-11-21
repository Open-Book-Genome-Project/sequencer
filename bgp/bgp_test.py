import unittest

from bgp import ia
try:  # TODO: create bgp.runner
    from bgp.runner import DEFAULT_SEQUENCER
except ImportError:
    class DEFAULT_SEQUENCER:
        @classmethod
        def sequence(book):
            pass

item_id = '9780262517638OpenAccess'
book = ia.get_item(item_id)
genome = DEFAULT_SEQUENCER.sequence(book)


class TestSequencer(unittest.TestCase):

    def test_smoketest(self):
        book = ia.get_item(item_id)
        genome = DEFAULT_SEQUENCER.sequence('hpmor')
    
    def test_copyright_page_detection(self):
        assert genome.results['pagetypes']['copyright_page'][0] == '0004'
