import re
import string
from collections import defaultdict

from lxml import etree

import time

STOP_WORDS = set("""'d 'll 'm 're 's 've a about above across after afterwards
again against all almost alone along already also although always am among
amongst amount an and another any anyhow anyone anything anyway anywhere are
around as at back be became because become becomes becoming been before
beforehand behind being below beside besides between beyond both bottom but by
ca call can cannot could did do does doing done down due during each eight
either eleven else elsewhere empty enough even ever every everyone everything
everywhere except few fifteen fifty first five for former formerly forty four
from front full further get give go had has have he hence her here hereafter
hereby herein hereupon hers herself him himself his how however hundred i if
in indeed into is it its itself just keep last latter latterly least less made
make many may me meanwhile might mine more moreover most mostly move much must
my myself n't name namely neither never nevertheless next nine no nobody none
noone nor not nothing now nowhere n‘t n’t of off often on once one only onto
or other others otherwise our ours ourselves out over own part per perhaps
please put quite rather re really regarding same say see seem seemed seeming
seems serious several she should show side since six sixty so some somehow
someone something sometime sometimes somewhere still such take ten than that
the their them themselves then thence there thereafter thereby therefore
therein thereupon these they third this those though three through throughout
thru thus to together too top toward towards twelve twenty two under unless
until up upon us used using various very via was we well were what whatever
when whence whenever where whereafter whereas whereby wherein whereupon
wherever whether which while whither who whoever whole whom whose why will
with within without would yet you your yours yourself yourselves ‘d ‘ll ‘m ‘re
‘s ‘ve ’d ’ll ’m ’re ’s ’ve""".split())


class FulltextProcessor():

    def __init__(self, modules):
        self.modules = modules

    def run(self, book):
        for m in self.modules:
            self.modules[m].run(book.plaintext)

    @property
    def results(self):
        return {m: self.modules[m].results for m in self.modules}


class ReadingLevelModule:

    def __init__(self):
        self.flesch_kincaid_grade= None
        self.time = 0

    def run(self, doc, **kwargs):
        import textstat
        tic = time.perf_counter()
        self.flesch_kincaid_grade = textstat.flesch_kincaid_grade(doc)
        toc = time.perf_counter()
        self.time = round(toc - tic, 3)

    @property
    def results(self):
        return {
            "time": self.time,
            "results": self.flesch_kincaid_grade
        }
    
class NGramProcessor():

    def __init__(self, modules, n=1, threshold=None, stop_words=None):
        """
        :param lambda modules: a dict of {'name': module}
        :param int n: n-gram sequence length
        :param int threshold: min occurrences threshold
        """
        self.modules = modules
        self.n = n
        self.threshold = threshold
        self.stop_words = stop_words

    def run(self, book):
        self.terms = self.fulltext_to_ngrams(
            book.plaintext, n=self.n, stop_words=self.stop_words)
        for m in self.modules:
            tic = time.perf_counter()
            for i, term in enumerate(self.terms):
                self.modules[m].run(term, threshold=self.threshold, index=i)
            toc = time.perf_counter()
            self.modules[m].time = round(toc - tic, 3)

    @property
    def results(self):
        return {m: self.modules[m].results for m in self.modules}

    @staticmethod
    def tokens_to_ngrams(tokens, n=2):
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return [" ".join(ngram) for ngram in ngrams]

    @classmethod
    def fulltext_to_ngrams(cls, fulltext, n=1, stop_words=None,
                           punctuation='!"#$%&\'()*+,.-;<=>?@[\\]^`{|}*'):
        fulltext_to_ngrams_tic = time.perf_counter()
        stop_words = stop_words or {}
        def clean(fulltext):
            return ''.join(c.encode("ascii", "ignore").decode() for c in (
                fulltext.lower()
                .replace('. ', ' ')
                .replace('\n-', '')
                .replace('\n', ' ')
            ) if c not in punctuation)
        tokens = [t.strip() for t in clean(fulltext).split(' ') if t and t not in stop_words]
        fulltext_to_ngrams_toc = time.perf_counter()
        fulltext_to_ngrams_time = round(fulltext_to_ngrams_toc - fulltext_to_ngrams_tic, 3)
        print(f"fulltext_to_ngrams took {fulltext_to_ngrams_time} seconds to complete.")
        return cls.tokens_to_ngrams(tokens, n=n) if n > 1 else tokens


class WordFreqModule:

    def __init__(self):
        self.freqmap = defaultdict(int)
        self.time = 0

    def run(self, word, threshold=None, **kwargs):
        self.threshold = threshold
        self.freqmap[word] += 1

    @property
    def results(self):
        return {
            "time": self.time,
            "results": sorted(
                [items for items in self.freqmap.items()
                 if not self.threshold or items[1] > self.threshold],
                key=lambda k_v: k_v[0], reverse=True)
        }

class ExtractorModule:

    def __init__(self, extractor):
        self.extractor = extractor
        self.matches = []

    def run(self, term, term_index=None, **kwargs):
        _term = self.extractor(term)
        if _term:
            self.matches.append((_term, term_index))

    @property
    def results(self):
        return self.matches


class UrlExtractorModule(ExtractorModule):

    @staticmethod
    def validate_url(s):
        s = s.lower()
        if s.lower().startswith('http'):
            return s

    def __init__(self):
        super().__init__(self.validate_url)


class IsbnExtractorModule(ExtractorModule):

    @staticmethod
    def validate_isbn(isbn):
        isbn = isbn.replace("-", "").replace(" ", "").upper();
        match = re.search(r'^(\d{9})(\d|X)$', isbn)
        if not match:
            return False
        digits = match.group(1)
        check_digit = 10 if match.group(2) == 'X' else int(match.group(2))
        result = sum((i + 1) * int(digit) for i, digit in enumerate(digits))
        if (result % 11) == check_digit:
            return match.group()

    def __init__(self):
        super().__init__(self.validate_isbn)


class PageTypeProcessor:

    def __init__(self, modules):
        self.modules = modules

    def run(self, book):
        utf8_parser = etree.XMLParser(encoding='utf-8')
        node = etree.fromstring(book.xml.encode('utf-8'), parser=utf8_parser)
        for x in node.iter('OBJECT'):
            for m in self.modules:
                self.modules[m].run(x)
    @property
    def results(self):
        return {m: self.modules[m].results for m in self.modules}

class KeywordPageDetectorModule:

    def __init__(self, keyword):
        self.keyword = keyword.lower()
        self.matched_pages = []

    def run(self,x):
        for word in x.iter('WORD'):
            if(word.text.lower() == self.keyword):
                param = x[0].attrib['value'].split('.')[0]
                current_page = param[-4:]
                self.matched_pages.append(current_page)
    @property
    def results(self):
        return self.matched_pages
