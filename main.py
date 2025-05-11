import requests
from urllib.parse import urlparse
import datetime
import json
import sys

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

def fetch_book_info(volume_id):
    api_url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

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
        author_fields.append(f"|last{idx+1}={last} |first{idx+1}={first}")

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

    template = f"""{{{{cite book {author_string} |date={volume_info.get('publishedDate', '')} |title={volume_info.get('title', '')} |url=https://books.google.com/books?id={volume_id} |publisher={volume_info.get('publisher', '')} |isbn={isbn} |access-date={today}}}}}"""
    return template

def main():
    if len(sys.argv) < 2:
        print("Usage: python citebook.py <google_books_url>")
        print("Example: python citebook.py https://www.google.com/books/edition/Example_Title/abc123XYZ?hl=en")
        sys.exit(1)

    url = sys.argv[1]
    volume_id = get_volume_id(url)
    if not volume_id:
        print("Error: Could not extract volume ID from the URL.")
        sys.exit(1)

    try:
        data = fetch_book_info(volume_id)
        
        # Save JSON to file
        #with open("thing.json", "w", encoding="utf-8") as f:
        #    json.dump(data, f, indent=4, ensure_ascii=False)

        citation = generate_cite_book(data, volume_id)
        print(citation)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
