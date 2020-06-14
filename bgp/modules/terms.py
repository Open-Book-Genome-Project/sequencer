#-*- encoding: utf-8 -*-

import string
import re
from collections import defaultdict
from lxml import etree


STOP_WORDS = {'elsewhere', 'bottom', 'n’t', 're', 'herself', 'see', 'which', 'yourself', 'top', 'somehow', 'nothing', 'move',
              'since', 'former', 'this', 'doing', 'too', 'who', 'again', 'below', 'we', 'either', 'he', 'so', 'none', 'indeed',
              'still', 'thereafter', 'also', 'empty', 'please', '‘ve', 'name', 'here', 'quite', 'no', 'afterwards', 'then',
              "'s", 'down', 'its', 'full', 'nowhere', 'off', 'own', 'first', 'regarding', 'twelve', 'by', 'her', 'where', 'within',
              'a', 'others', 'another', 'but', 'really', 'during', 'itself', 'seem', 'each', 'neither', 'three', '‘ll', 'somewhere',
              '‘re', 'other', 'n‘t', 'rather', '’s', 'how', 'be', 'under', 'at', 'much', 'whenever', 'of', 'wherein', 'hence',
              'are', 'my', 'everywhere', 'am', 'something', '’ll', 'twenty', 'because', 'few', 'seems', '‘d', 'through', 'your',
              'four', 'thereby', 'into', 'has', 'could', 'our', 'out', 'if', 'already', 'namely', 'such', 'hereupon', 'therefore',
              'why', 'back', 'some', 'whereafter', 'for', 'never', 'whom', 'two', 'there', 'me', 'however', 'anyone', 'yourselves',
              'whereupon', 'whole', 'enough', 'on', 'unless', 'same', 'behind', 'becoming', 'than', 'sometimes', 'upon', 'often',
              'else', 'along', 'part', 'as', 'was', 'ours', 'further', 'onto', 'until', 'amount', "'ve", 'due', 'anything', 'becomes',
              'seeming', 'is', 'forty', 'sometime', 'around', 'once', 'beyond', 'even', 'have', 'used', 'several', '‘m', 'without',
              'everyone', 'therein', 'whatever', 'formerly', '‘s', 'less', 'mine', 'fifteen', 'it', '’m', 'beforehand', 'from',
              'almost', 'most', 'latterly', 'now', 'not', 'these', 'whose', 'nevertheless', 'per', 'after', 'themselves', 'via',
              'everything', 'what', 'herein', 'show', 'whereby', 'anyhow', 'will', 'become', "'ll", 'various', 'latter', 'were',
              'throughout', 'his', 'always', 'serious', 'must', "'d", 'in', 'meanwhile', 'before', 'keep', 'yet', 'though', 'get',
              'hereafter', 'hereby', 'ten', 'had', 'thereupon', 'alone', 'whoever', 'one', 'across', 'side', 'over', 'or', 'besides',
              'using', 'otherwise', 'whence', 'take', 'those', 'ever', 'eight', 'they', 'anyway', 'noone', 'an', 'many', 'moreover',
              'third', 'himself', 'their', 'cannot', 'myself', 'i', 'call', 'been', 'hundred', 'thence', '’re', 'do', 'give', 'did',
              'him', 'made', 'can', 'nine', 'very', 'go', 'perhaps', 'thru', 'wherever', 'although', "'m", 'became', 'above', 'hers',
              'except', 'while', 'more', 'would', 'well', 'toward', 'might', 'only', 'to', 'the', 'you', 'say', 'about', 'yours',
              'whether', "n't", 'among', 'least', 'nor', 'next', 'amongst', 'whither', 'ourselves', 'beside', 'them', 'whereas',
              'put', 'and', 'towards', 'make', 'last', 'eleven', 'between', 'thus', '’ve', 'does', 'five', 'together', 'done',
              'being', 'us', 'both', 'should', 'every', "'re", 'against', 'any', 'may', 'seemed', 'fifty', 'when', 'just', 'front',
              '’d', 'anywhere', 'all', 'that', 'six', 'nobody', 'ca', 'with', 'sixty', 'someone', 'she', 'up', 'mostly'
             }

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
        return sorted(
            self.freqmap.items(), key=lambda k_v: k_v[0], reverse=True)

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
