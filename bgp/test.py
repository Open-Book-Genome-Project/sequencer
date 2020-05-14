
import unittest

from bgp import ia
from bgp.runner import DEFAULT_SEQUENCER

book = ia.get_item('9780262517638OpenAccess')
genome = DEFAULT_SEQUENCER.sequence(book)

class TestSequencer(unittest.TestCase):

    def test_copyright_page_detection(self):
        assert genome.results['pagetypes']['copyright_page'][0] == '0004'
