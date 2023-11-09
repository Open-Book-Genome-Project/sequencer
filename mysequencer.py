from bgp import ia
from bgp import Sequencer
from bgp.modules.terms import TocPageDetectorModule, PageTypeProcessor, CopyrightPageDetectorModule


PageTypeDetectionSequencer = Sequencer({
    "pagetypes": PageTypeProcessor(modules={
        "toc_page": TocPageDetectorModule()
    })
})


book = ia.get_item("9780262517638OpenAccess") 

results = PageTypeDetectionSequencer.sequence(book).results

print(results)