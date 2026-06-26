"""
subito_scraper.py
-----------------
Scrapes product listings from a Subito.it search-results page.

Target URL : https://www.subito.it/annunci-italia/vendita/motori/?q=pioneer+rds
Search term: "pioneer+rds"  (fixed, not modified)

Data sources
------------
1. <script type="application/ld+json">
   A JSON-LD graph (key "@graph") containing ImageObject entries.
   Extracts: title ("name"), image URL ("contentUrl").

2. <script id="__NEXT_DATA__" type="application/json">
   A large Next.js state object.
   Extracts for each product (in order):
     - price  : found under key "/price" → "values" → [0] → "value"
     - url    : found under key "urls"   → "default"

Dependencies: requests, beautifulsoup4  (both installable via pip)
"""

import json
import sys

import requests
from bs4 import BeautifulSoup

#  Configuration

URL = "https://www.subito.it/annunci-italia/vendita/usato/?q=KEH-P7600R"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.subito.it/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}


#  Helpers


def fetch_page(url: str) -> str:
    """Download the page and return its HTML text."""
    session = requests.Session()
    # Warm up: hit the homepage first so the server can set any session cookies
    try:
        session.get("https://www.subito.it/", headers=HEADERS, timeout=15)
    except requests.RequestException:
        pass  # Not fatal – carry on without homepage cookies

    response = session.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_ld_json(soup: BeautifulSoup) -> list:
    """
    Extract all ImageObject entries from the application/ld+json script tag.

    Returns a list of dicts with keys 'name' and 'contentUrl',
    in the order they appear in the @graph array.
    """
    script_tag = soup.find("script", {"type": "application/ld+json"})
    if not script_tag or not script_tag.string:
        return []

    try:
        data = json.loads(script_tag.string)
    except json.JSONDecodeError as exc:
        print(f"[WARN] Could not parse ld+json: {exc}", file=sys.stderr)
        return []

    graph = data.get("@graph", [])
    return [item for item in graph if item.get("@type") == "ImageObject"]


def find_all_values(obj, target_key: str, results=None) -> list:
    """
    Recursively walk a parsed JSON structure (dicts and lists) and collect
    every value associated with *target_key*, in document order.
    """
    if results is None:
        results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == target_key:
                results.append(v)
            else:
                find_all_values(v, target_key, results)
    elif isinstance(obj, list):
        for item in obj:
            find_all_values(item, target_key, results)
    return results


def parse_next_data(soup: BeautifulSoup):
    """
    Extract parallel lists of prices and product URLs from __NEXT_DATA__.

    Returns (prices, urls) where each is a list aligned by product index.
    Missing values are represented as None.
    """
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script_tag or not script_tag.string:
        return [], []

    try:
        data = json.loads(script_tag.string)
    except json.JSONDecodeError as exc:
        print(f"[WARN] Could not parse __NEXT_DATA__: {exc}", file=sys.stderr)
        return [], []

    # Collect all "/price" nodes in document order
    price_nodes = find_all_values(data, "/price")
    prices = []
    for node in price_nodes:
        try:
            prices.append(node["values"][0]["value"])
        except (TypeError, KeyError, IndexError):
            prices.append(None)

    # Collect all "urls" nodes in document order
    url_nodes = find_all_values(data, "urls")
    urls = []
    for node in url_nodes:
        try:
            urls.append(node.get("default") if isinstance(node, dict) else None)
        except AttributeError:
            urls.append(None)

    return prices, urls


def build_products(image_items: list, prices: list, urls: list) -> list:
    """
    Zip the three parallel lists into a single list of product dicts.
    The length is determined by the longest list; missing slots → None.
    """
    n = max(len(image_items), len(prices), len(urls), 0)
    products = []
    for i in range(n):
        item = image_items[i] if i < len(image_items) else {}
        products.append(
            {
                "title": item.get("name") or None,
                "image_url": item.get("contentUrl") or None,
                "price": prices[i] if i < len(prices) else None,
                "url": urls[i] if i < len(urls) else None,
            }
        )
    return products


def print_products(products: list) -> None:
    """Pretty-print the scraped product list."""
    if not products:
        print("No products found.")
        return

    sep = "" * 72
    print(f"\n{'═' * 72}")
    print(f"  Subito.it – pioneer+rds  |  {len(products)} product(s) found")
    print(f"{'═' * 72}\n")

    for i, p in enumerate(products, start=1):
        print(f"[{i}] {p['title'] or '(no title)'}")
        print(f"    Price     : {p['price'] or '—'}")
        print(f"    URL       : {p['url'] or '—'}")
        print(f"    Image URL : {p['image_url'] or '—'}")
        print(sep)


#  Main


def main() -> None:
    print(f"Fetching: {URL}")
    try:
        html = fetch_page(URL)
    except requests.HTTPError as exc:
        sys.exit(f"HTTP error: {exc}")
    except requests.RequestException as exc:
        sys.exit(f"Network error: {exc}")

    soup = BeautifulSoup(html, "html.parser")

    # 1. Titles + image URLs  ← application/ld+json
    image_items = parse_ld_json(soup)
    print(f"  ImageObject entries found (ld+json)  : {len(image_items)}")

    # 2. Prices + product URLs  ← __NEXT_DATA__
    prices, urls = parse_next_data(soup)
    print(f"  Price entries found  (__NEXT_DATA__) : {len(prices)}")
    print(f"  URL   entries found  (__NEXT_DATA__) : {len(urls)}")

    # 3. Assemble & display
    products = build_products(image_items, prices, urls)
    print_products(products)


if __name__ == "__main__":
    main()
