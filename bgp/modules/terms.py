import re
from collections import defaultdict

import isbnlib
import requests
import time
from lxml import etree

from readability import Readability
from readability.scorers.flesch_kincaid import ReadabilityException


PUNCTUATION = r'!"#$%&\'\/:()*+,.-;<=>?@[\\]^`{|}*'
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
        self.time = 0

    def run(self, book):
        processor_tic = time.perf_counter()
        for m in self.modules:
            module_tic = time.perf_counter()
            self.modules[m].run(book)
            module_toc = time.perf_counter()
            self.modules[m].time = round(module_toc - module_tic, 3)
        processor_toc = time.perf_counter()
        self.time = round(processor_toc - processor_tic, 3)

    @property
    def results(self):
        return {
            "modules": {m: self.modules[m].results for m in self.modules},
            "total_time": self.time
        }


class ReadingLevelModule:

    def __init__(self):
        self.lexile_min_age= 'None'
        self.lexile_max_age= 'None'
        self.readability_fk_score= None
        self.readability_s_score= None
        self.time = 0

    def run(self, book, **kwargs):
        doc = book.plaintext
        isbn = 'isbn' in book.metadata and book.metadata['isbn'][0]

        url = 'https://atlas-fab.lexile.com/free/books/' + str(isbn)

        headers = {'accept': 'application/json; version=1.0'}
        lexile = requests.get(url, headers=headers)
        # Checks if lexile exists for ISBN. If doesn't exist value remains 'None'.
        # If lexile does exist but no age range, value will be 'None'.
        # If no ISBN, value will be 'None'.
        if lexile.status_code == 200:
            lexile_work = lexile.json()['data']['work']
            self.lexile_min_age = str(lexile_work['min_age'])
            self.lexile_max_age = str(lexile_work['max_age'])
        try:
            r = Readability(doc)
            fk = r.flesch_kincaid()
            s = r.smog()
            self.readability_fk_score = fk.score
            self.readability_s_score = s.score
        # If less than 100 words
        except ReadabilityException:
            pass

    @property
    def results(self):
        return {
            "time": self.time,
            "results": {
                "lexile": {
                    "min_age": self.lexile_min_age,
                    "max_age": self.lexile_max_age
                },
                "readability": {
                    "flesch_kincaid_score": self.readability_fk_score,
                    "smog_score": self.readability_s_score,
                }
            }
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
        # use token_count as word count for profiler
        self.token_count = 0
        self.time = 0
        self.tokenization_time = 0

    def run(self, book):
        book.plaintext  # Priming memoization
        processor_tic = time.perf_counter()
        self.terms = self.fulltext_to_ngrams(
            book.plaintext, n=self.n, stop_words=self.stop_words)
        self.tokenization_time = round(time.perf_counter() - processor_tic, 3)
        for m in self.modules:
            module_tic = time.perf_counter()
            for i, term in enumerate(self.terms):
                self.token_count += 1
                self.modules[m].run(term, threshold=self.threshold, index=i)
            module_toc = time.perf_counter()
            self.modules[m].time = round(module_toc - module_tic, 3)
        processor_toc = time.perf_counter()
        self.time = round(processor_toc - processor_tic, 3)

    @property
    def results(self):
        return {
            "modules": {
                m: self.modules[m].results for m in self.modules
            },
            "total_time": self.time,
            "tokenization_time": self.tokenization_time,
            "total_tokens": self.token_count
        }

    @staticmethod
    def tokens_to_ngrams(tokens, n=2):
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return [" ".join(ngram) for ngram in ngrams]

    @classmethod
    def fulltext_to_ngrams(cls, fulltext, n=1, stop_words=None):
        stop_words = stop_words or {}

        def clean(fulltext):
            return (
                fulltext.lower()
                .replace('. ', ' ')
                .replace('\n-', '')
                .replace('\n', ' ')
            )
        tokens = [
            t.strip() for t in clean(fulltext).split(' ')
            if t and t not in stop_words
        ]
        return cls.tokens_to_ngrams(tokens, n=n) if n > 1 else tokens

def rmpunk(word, punctuation=PUNCTUATION):
    return ''.join(
        c.encode("ascii", "ignore").decode() for c in (word)
        if c not in punctuation
    )

def replace_mistakes(word):
    substitutions = [('I', '1'), ('O', '0'), ('l', '1'), ('D', '0'), ('A', '8'), ('/', 'X'), ('\\', 'X'), ('S', '5')]
    for sub in substitutions:
        word = word.replace(*sub)
    return word

class WordFreqModule:

    def __init__(self, punctuation=PUNCTUATION):
        self.punctuation = punctuation
        self.freqmap = defaultdict(int)
        self.time = 0

    def run(self, word, threshold=None, **kwargs):
        clean_word = rmpunk(
            word, punctuation=self.punctuation
        )
        self.threshold = threshold
        self.freqmap[clean_word] += 1

    @property
    def results(self):
        return {
            "time": self.time,
            "results": sorted(
                [items for items in self.freqmap.items()
                 if not self.threshold or items[1] >= self.threshold],
                key=lambda k_v: k_v[1], reverse=True)
        }

class ExtractorModule:

    def __init__(self, extractor):
        self.extractor = extractor
        self.matches = []
        self.time = 0

    def run(self, term, **kwargs):
        _term = self.extractor(term)
        if _term:
            self.matches.append(_term)

    @property
    def results(self):
        return{
            "results": self.matches,
            "time": self.time
        }


class UrlExtractorModule(ExtractorModule):

    @staticmethod
    def validate_url(s):
        s = s.lower()
        if s.startswith('http'):
            return s

    def __init__(self):
        super().__init__(self.validate_url)


class IsbnExtractorModule(ExtractorModule):


    @staticmethod
    def validate_isbn(isbn):
        isbn = rmpunk(isbn).replace(' ', '')
        if len(isbn) == 9:
            isbn = '0' + isbn
        match10 = re.search(r'^(\d{9})(\d|X)', isbn)
        match13 = re.search(r'^(\d{12})(\d)', isbn)

        if match10:
            if isbnlib.is_isbn10(match10.group()):
                return match10.group()
            elif match13:
                if isbnlib.is_isbn13(match13.group()):
                    return match13.group()
            else:
                return False

    @staticmethod
    def extract_isbn(page):
        isbns = []
        for line in page.iter('LINE'):
            line_text = ' '.join(word.text for word in line.iter('WORD'))
            line_text_clean = replace_mistakes(line_text)
            isbnlike_list = isbnlib.get_isbnlike(line_text_clean, level='loose')
            for candidate_isbn in isbnlike_list:
                isbn = IsbnExtractorModule.validate_isbn(candidate_isbn)
                if isbn:
                    isbns.append(isbn)
        return isbns

    def __init__(self):
        super().__init__(self.validate_isbn)


class PageTypeProcessor:

    def __init__(self, modules):
        self.modules = modules
        self.time = 0

    def run(self, book):
        processor_tic = time.perf_counter()
        utf8_parser = etree.XMLParser(encoding='utf-8')
        node = etree.fromstring(book.xml.encode('utf-8'), parser=utf8_parser)
        for m in self.modules:
            module_tic = time.perf_counter()
            for page in node.iter('OBJECT'):
                self.modules[m].run(page, node)
            module_toc = time.perf_counter()
            self.modules[m].time = round(module_toc - module_tic, 3)
        processor_toc = time.perf_counter()
        self.time = round(processor_toc - processor_tic, 3)
    @property
    def results(self):
        return {
            "modules": {m: self.modules[m].results for m in self.modules},
            "total_time": self.time,
        }

class KeywordPageDetectorModule:

    def __init__(self, keywords, extractor=None, match_limit=None):
        self.extractor = extractor
        self.keywords = keywords
        self.matched_pages = []
        self.match_limit = match_limit

    def run(self, page, node):
        if not self.match_limit or len(self.matched_pages) < self.match_limit:
            for word in page.iter('WORD'):
                if word.text.lower() in self.keywords:
                    param = page[0].attrib['value'].split('.djvu')[0]
                    current_page = param[-4:]
                    match = {
                        'page': current_page,
                    }
                    if self.extractor:
                        match.update(self.extractor(page))
                    self.matched_pages.append(match)
                    # If we've found a match, we no longer need to
                    # keep processing this page; exit for loop
                    break
    @property
    def results(self):
        return {
            "results": self.matched_pages,
            "time": self.time
        }


class CopyrightPageDetectorModule(KeywordPageDetectorModule):

    def extractor(self, page):
        isbns = IsbnExtractorModule.extract_isbn(page)

        return {
            'isbns': isbns,
        }

    def __init__(self):
        super().__init__(['copyright', '©'], extractor=self.extractor, match_limit=1)


class TocPageDetectorModule(KeywordPageDetectorModule):

    def __init__(self):
        super().__init__(["table of contents"], match_limit=1)

    def detectTocHeading(self, page):
        for i, line in enumerate(page.iter('LINE')):
            if i < 5:  # if we're in the first few lines
            words = " ".join(line.iter('WORD')).lower().strip()
            if any(kws == words for kws in self.keywords):
                return True
        return False


    def run(self, page, node):
        if not self.match_limit or len(self.matched_pages) < self.match_limit:
            if self.detectTocHeading(page):
                param = page[0].attrib['value'].split('.djvu')[0]
                current_page = param[-4:]
                match = {
                    'page': current_page,
                }
                self.matched_pages.append(match)

class BackpageIsbnExtractorModule():

    def __init__(self):
        self.isbns = []

    def run(self, page, node):
        current_page = int(page[0].attrib['value'].split('.djvu')[0][-4:])
        if not hasattr(self, 'last_page'):
            self.last_page = int(node.xpath("//OBJECT")[-1][0].attrib['value'].split('.djvu')[0][-4:])
        if current_page == self.last_page:
            self.isbns = IsbnExtractorModule.extract_isbn(page)

    @property
    def results(self):
        return {
            "results": self.isbns,
            "time": self.time
        }
