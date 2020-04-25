#-*- encoding: utf-8 -*-

import string
import re
from collections import defaultdict
from lxml import etree


STOP_WORDS = {
    'would', 'ourselves', 'hers', 'between',
    'yourself', 'but', 'again', 'there', 'about', 'once',
    'during', 'out', 'very', 'having', 'with', 'they', 'own',
    'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such',
    'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's',
    'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the',
    'themselves', 'until', 'below', 'are', 'we', 'these', 'your',
    'through', 'don', 'nor', 'me', 'were', 'her', 'more',
    'himself', 'this', 'down', 'should', 'our', 'their', 'while',
    'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all',
    'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and',
    'been', 'have', 'in', 'will', 'on', 'does', 'yourselves',
    'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can',
    'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has',
    'just', 'where', 'too', 'only', 'myself', 'which', 'those',
    'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs',
    'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further',
    'was', 'here', 'than', 'new', 'his', 'her', 'one', 'two',
    'three', 'also', 'like', 'could', 'many', 'see', 'may',
    'ever', 'became', 'because', 'far', 'well', 'among', 'things',
    'seems', 'much', 'almost', 'around', 'often'
}


class NGramProcessor():

    def __init__(self, modules, n=1, stop_words=None):
        """
        :param modules: a dict of {'name': module}
        """
        self.modules = modules
        self.n = n
        self.stop_words = stop_words

    def run(self, fulltext):
        self.terms = self.fulltext_to_ngrams(
            fulltext, n=self.n, stop_words=self.stop_words)
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
                .encode('ascii', 'ignore')
            ) if c not in punctuation)
        tokens = [t.strip() for t in clean(fulltext).split(' ') if t and t not in stop_words]
        return cls.tokens_to_ngrams(tokens, n=n) if n > 1 else tokens


class WordFreqModule:

    def __init__(self):
        self.freqmap = defaultdict(int)

    def run(self, word, **kwargs):
        self.freqmap[word] += 1

    @property
    def results(self):
        return sorted(self.freqmap.iteritems(), key=lambda (k, v): v, reverse=True)

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


class PageTypeProcessor():

    def __init__(self, modules):
        """
        :param modules: a dict of {'name': module}
        """
        self.modules = modules

class CopyrightPageDetectorModule:
    
    def __init__(self, keyword):
        self.keyword = keyword
        self.pageNo = pageNo
        
    
    def search(self, keyword):
        parser = etree.XMLParser(recover=True)
        tree = etree.parse('djvu.xml',parser) # Help required: This xml file needs to be fetched through OL python library
        for x in tree.iter('OBJECT'):
            # Iterating over each WORD tag to locate the keyword
            for i in x.iter('WORD'):
                if(i.text == keyword):
                    '''
                        x[0].attrib['value'] is Descartes-TheGeometry_0273.djvu 
                        splitting at '.' and finding the last 4 lettes of the book name in this case it is 0273
                    '''
                    param = x[0].attrib['value'].split('.')[0] 
                    pageNo = param[-4:]
                    

    @property
    def results(self):
        return self.pageNo
