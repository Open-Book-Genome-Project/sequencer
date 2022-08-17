import internetarchive as ia
import requests
import json

def get_isbns(query="")
    """Some function to fetch ISBNs from Archive.org items"""
    url = "https://archive.org/advancedsearch.php?q=" + query
    r = requests.get(url)
    return r.json()

def get_lexile(isbn):
    try:
        r = requests.get("TODO")
        r.json()
    except Exception as e:
        # make sure successes and failures go in `log`
        pass
    pass
  
def main(query=""):
    isbns = get_isbns(query)
    seen_isbns = set()
    # next, load all isbns we've seen from the `log` file
    # Now, do our query to get isbns
    # If isbn is in the seen_isbns, skip it.
    for isbn in isbns:
        if isbn not in seen_isbns:
            data = get_lexile(isbn)
            if data:
                # put in success file (which gets opened in append mode, which means
                # we will add to the end rather than clobbering our file
                pass

if __name__ == "__main__":
     query = ""  # get from command line? see: argparse
     main(query)
