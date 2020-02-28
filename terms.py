import re
from collections import defaultdict
import string

STOP_WORDS = {'would', 'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'in\
to', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', \
'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yo\
urselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't'\
, 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than', 'new', 'his', 'her', 'one', 'two', 'three', 'also', 'like', 'could', 'many', 'see', 'may', 'ever', 'became', 'becaus\
e', 'far', 'well', 'among', 'things', 'seems', 'much', 'almost', 'around', 'often'}

def ngram(tokens, n=2):
    ngrams = zip(*[tokens[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]

def sanitize(fulltext):
    return fulltext.lower().replace('\n-', '').replace('\n', ' ').translate(None, string.punctuation).decode('utf-8')

def sequence(fulltext, n=1):
    """Sequence the genome of this book"""
    freqmap = defaultdict(int)
    words = [w.strip() for w in sanitize(fulltext).split(' ') if len(w) > 1 and w not in STOP_WORDS]
    corpus = words if n == 1 else ngram(words, n=n)

    for s in corpus:
        if s.isdigit():
            freqmap[':number'] += 1
        else:
            freqmap[s] += 1
    return sorted(freqmap, key=freqmap.get, reverse=True)

def fingerprint(fulltext_filename='glutmasteringinf00wrig_djvu.txt', n=1):
    with open(fulltext_filename) as book:
        return sequence(book.read(), n=n)
