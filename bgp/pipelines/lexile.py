import internetarchive as ia
import requests
import json
import time
import csv
from isbnlib import to_isbn13

def get_isbn_items(query=""):
    """Function which fetches ISBNs from Archive.org items"""
    url = "https://archive.org/advancedsearch.php?q=" + query
    r = requests.get(url)
    isbn_items = r.json()["response"]["docs"]
    print(f"Length of isbn_items: {len(isbn_items)}")
    return isbn_items

def get_lexile(isbn):
    try:
        url = 'https://atlas-fab.lexile.com/free/books/' + str(isbn)
        headers = {'accept': 'application/json; version=1.0'}
        lexile = requests.get(url, headers=headers)
        lexile.raise_for_status()  # this will raise an error for us if the http status returned is not 200 OK
        print(f"json from lexile is: \n {lexile.json()}")
        data = lexile.json()
        return data, data.get("error_msg")
    except Exception as e:
        if e.response.status_code not in [200, 404]:
            raise Exception(f"Got scary response back from server: {e}") 
        return {}, e
  
def main(query=""):
    # Now, do our query to get isbns
    isbn_items = get_isbn_items(query)
    # Next, load all isbns we've seen from the `log` file
    with open("log.csv", "r") as f:
        csv_reader = csv.reader(f, delimiter=",")
        next(csv_reader)
        seen_isbns = {row[0] for row in csv_reader}
    # Open a successes file to store lexile info from successful runs and a log file to keep track of the kind of result for each book run
    with open("successes.jsonl", "a") as successes, open("log.csv", "a") as log:
        fieldnames = ["isbn", "success", "error_msg"]
        writer = csv.DictWriter(log, fieldnames=fieldnames)
        log_info = {}
        ran_isbns = 0
        for i, item in enumerate(isbn_items):
            isbn = to_isbn13(item.get("isbn") and item["isbn"][0])
            print(f"i is {i}")
            # If isbn is in the seen_isbns, skip it.
            if isbn and isbn not in seen_isbns:
                log_info["isbn"] = isbn
                print(f"Running isbn {isbn}")
                # Keep from overloading lexile servers
                time.sleep(.5)
                data, error_msg = get_lexile(isbn)
                log_info["error_msg"] = error_msg
                log_info["success"] = data.get("success", False)
                if log_info["success"]:
                    successes.write(json.dumps(data)+"\n")
                writer.writerow(log_info)
                ran_isbns += 1
                print(f"There have been {ran_isbns} isbns run")

            # Set this to break once we've gone through as many books as we want
            if ran_isbns > 195820:
                break

if __name__ == "__main__":
    # Input our archive.org query here
    query = "collection%3Ainlibrary+AND+%21collection%3Aperiodicals+AND+format%3AMARC*+AND+isbn%3A*+AND+%28year%3A2015+OR+year%3A2014+OR+year%3A2013+OR+year%3A2012+OR+year%3A2011+OR+year%3A2010%29+AND+%28subject%3A%22Families%22+OR+subject%3A%22Friendship+--+Fiction%22+OR+subject%3A%22Friendship%22+OR+subject%3A%22Schools+--+Fiction%22+OR+subject%3A%22Friendship+--+Juvenile+fiction%22+OR+subject%3A%22Children%E2%80%99s+stories%22+OR+subject%3A%22Schools+--+Juvenile+fiction%22+OR+subject%3A%22Magic+--+Juvenile+fiction%22+OR+subject%3A%22Dogs+--+Juvenile+fiction%22+OR+subject%3A%22Families+--+Juvenile+fiction%22+subject%3A%22Fantasy+fiction%22+OR+subject%3A%22Animals+--+Juvenile+fiction%22%29&fl%5B%5D=identifier&fl%5B%5D=isbn&sort%5B%5D=&sort%5B%5D=&sort%5B%5D=&rows=300010&page=1&output=json"  
    main(query)