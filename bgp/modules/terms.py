#-*- encoding: utf-8 -*-

import string
import re
from collections import defaultdict
from lxml import etree


STOP_WORDS = set("""a about above after again against all almost also am among an and
    any are around as at be became because been before being below between both but by
    can could did do does doing don down during each ever far few for from further had
    has have having he her here hers herself him himself his how i if in into is it its
    itself just like many may me more most much my myself new no nor not now of off
    often on once one only or other our ours ourselves out over own s same see seems
    she should so some such t than that the their theirs them themselves then there
    these they things this those three through to too two under until up very was we
    well were what when where which while who whom why will with would you your yours
    yourself yourselves""".split())

class NGramProcessor():

    def __init__(self, modules, n=1, stop_words=None):
        """
        :param modules: a dict of {'name': module}
        """
        self.modules = modules
        self.n = n
        self.stop_words = stop_words

    def run(self, book):
        self.terms = self.fulltext_to_ngrams(
            book.plaintext, n=self.n, stop_words=self.stop_words)
        for i, term in enumerate(self.terms):
            for m in self.modules:
                self.modules[m].run(term, index=i)

    @property
    def results(self):
        return {m: self.modules[m].results for m in self.modules}

    @staticmethod
    def tokens_to_ngrams(tokens, n=2):
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return [" ".join(ngram) for ngram in ngrams]

    @classmethod
    def fulltext_to_ngrams(cls, fulltext, n=1, stop_words=None,
                           punctuation='!"#$%&\'()*+,;<=>?@[\\]^`{|}*'):
        stop_words = stop_words or {}
        def clean(fulltext):
            return ''.join(c for c in (
                fulltext.lower()
                .replace('. ', ' ')
                .replace('\n-', '')
                .replace('\n', ' ')
            ) if str(c) not in punctuation)
        tokens = [t.strip() for t in clean(fulltext).split(' ') if t and t not in stop_words]
        return cls.tokens_to_ngrams(tokens, n=n) if n > 1 else tokens


class WordFreqModule:

    def __init__(self):
        self.freqmap = defaultdict(int)

    def run(self, word, **kwargs):
        self.freqmap[word] += 1

    @property
    def results(self):
        return sorted(self.freqmap.items(), key=lambda k_v: k_v[0], reverse=True)

class ExtractorModule(object):

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
        super(UrlExtractorModule, self).__init__(self.validate_url)


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
        super(IsbnExtractorModule, self).__init__(self.validate_isbn)


class PageTypeProcessor:

    def __init__(self, modules):
        self.modules = modules

    def run(self, book):
        utf8_parser = etree.XMLParser(encoding='utf-8')
        node = etree.fromstring(book.xml.encode('utf-8'), parser=utf8_parser)
        for x in node.iter('OBJECT'):
            param = x[0].attrib['value'].split('.')[0] 
            pageNo = param[-4:]
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
