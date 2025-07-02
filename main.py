import json

import requests
from urllib.parse import urlparse
import datetime
import sys
import re

#For the url, try to get the actual core id
def get_volume_id(url):
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[-2] == "edition":
        return path_parts[-1]
    elif "id=" in url:
        query = urlparse(url).query
        for param in query.split("&"):
            if param.startswith("id="):
                return param.split("=")[1]
    elif len(path_parts) >= 2:
        return path_parts[-1]
    return None

#Get the json from Google Books
def fetch_book_info(volume_id):
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes/{volume_id}")
    response.raise_for_status()
    return response.json()

#Get the json from DOI
def get_doi_metadata(doi):
    headers = {'Accept': 'application/vnd.citationstyles.csl+json'}
    response = requests.get(f"https://doi.org/{doi}", headers=headers)
    response.raise_for_status()
    return response.json()

#Get all the authors
def generate_author_fields(authors):
    author_fields = []
    for idx, author in enumerate(authors):
        first = author.get("given", "")
        last = author.get("family", "")
        author_fields.append(f"|last{idx + 1}={last} |first{idx + 1}={first}")
    return " ".join(author_fields)


def generate_cite_book(json_data, volume_id):
    volume_info = json_data['volumeInfo']
    authors = volume_info.get('authors', [])

    author_fields = []
    for idx, author in enumerate(authors):
        parts = author.split()
        if not parts:
            continue
        first = " ".join(parts[:-1])
        last = parts[-1]
        author_fields.append(f"|last{idx + 1}={last} |first{idx + 1}={first}")
    author_string = " ".join(author_fields)

    isbn = ""
    identifiers = volume_info.get('industryIdentifiers', [])
    for iden in identifiers:
        if iden['type'] == "ISBN_13":
            isbn = iden['identifier']
            break
    if not isbn:
        for iden in identifiers:
            if iden['type'] == "ISBN_10":
                isbn = iden['identifier']
                break

    today = datetime.date.today().isoformat()
    return f"""{{{{cite book {author_string} |date={volume_info.get('publishedDate', '')} |title={volume_info.get('title', '')} |url=https://books.google.com/books?id={volume_id} |publisher={volume_info.get('publisher', '')} |isbn={isbn} |access-date={today}}}}}"""


def generate_cite_book_from_doi(json_data, doi):
    authors = json_data.get("author", [])
    author_string = generate_author_fields(authors)
    title = json_data.get("title", "")
    publisher = json_data.get("publisher", "")
    published_date_parts = json_data.get("issued", {}).get("date-parts", [])
    year = str(published_date_parts[0][0]) if published_date_parts else ""
    isbn_list = json_data.get("ISBN", [])
    isbn = isbn_list[0] if isbn_list else ""
    url = f"https://doi.org/{doi}"
    today = datetime.date.today().isoformat()

    return f"""{{{{cite book {author_string} |date={year} |title={title} |url={url} |publisher={publisher} |isbn={isbn} |doi={doi} |access-date={today}}}}}"""


def generate_cite_book_chapter(json_data, doi):
    authors = json_data.get("author", [])
    author_string = generate_author_fields(authors)
    chapter_title = json_data.get("title", "")
    book_title = json_data.get("container-title", "")
    publisher = json_data.get("publisher", "")
    pages = json_data.get("page", "")
    published_date_parts = json_data.get("issued", {}).get("date-parts", [])
    year = str(published_date_parts[0][0]) if published_date_parts else ""
    isbn_list = json_data.get("ISBN", [])
    isbn = isbn_list[0] if isbn_list else ""
    url = f"https://doi.org/{doi}"
    today = datetime.date.today().isoformat()

    return f"""{{{{cite book {author_string} |date={year} |title={book_title} |chapter={chapter_title} |url={url} |publisher={publisher} |isbn={isbn} |pages={pages} |doi={doi} |access-date={today}}}}}"""


def generate_cite_journal(json_data, doi):
    authors = json_data.get("author", [])
    author_string = generate_author_fields(authors)
    published_date_parts = json_data.get("issued", {}).get("date-parts", [])
    year = str(published_date_parts[0][0]) if published_date_parts else ""
    today = datetime.date.today().isoformat()

    return f"""{{{{cite journal {author_string} |date={year} |title={json_data.get("title", '')} |url=https://doi.org/{doi} |journal={json_data.get("container-title", '')} |volume={json_data.get("volume", '')} |issue={json_data.get("issue", '')} |publisher={json_data.get("publisher", '')} |pages={json_data.get("page", '')} |doi={doi} |access-date={today}}}}}"""


def is_doi(input_str):
    return bool(re.match(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', input_str, re.I)) or input_str.lower().startswith("https://doi.org/")


def extract_doi(input_str):
    return input_str.split("doi.org/")[1] if "doi.org/" in input_str else input_str.strip()


def main():
    global DEBUG
    DEBUG = False

    args = sys.argv[1:]
    if not args:
        print("Usage: python citebook.py <url_or_doi> [--debug]")
        sys.exit(1)

    if "--debug" in args:
        DEBUG = True
        args.remove("--debug")

    input_str = args[0]

    try:
        if is_doi(input_str):
            doi = extract_doi(input_str)
            data = get_doi_metadata(doi)
            if DEBUG:
                with open("debug_metadata.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print("Metadata written to debug_metadata.json")
            doi_type = data.get("type", "")
            if doi_type == "journal-article":
                citation = generate_cite_journal(data, doi)
            elif doi_type in ("book", "monograph"):
                citation = generate_cite_book_from_doi(data, doi)
            elif doi_type == "book-chapter":
                citation = generate_cite_book_chapter(data, doi)
            else:
                print(f"Unsupported DOI type: {doi_type}")
                sys.exit(1)
        else:
            volume_id = get_volume_id(input_str)
            if not volume_id:
                print("Error: Could not extract volume ID from the URL.")
                sys.exit(1)
            data = fetch_book_info(volume_id)
            if DEBUG:
                with open("debug_metadata.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print("Metadata written to debug_metadata.json")

            citation = generate_cite_book(data, volume_id)

        print(citation)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
