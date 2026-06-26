"""
Scrapes product listings from multiple Subito.it search-results pages.
Outputs a single JSON file containing all extracted products.

Data sources
------------
1. <script type="application/ld+json">
   A JSON-LD graph (key "@graph") containing ImageObject entries.
   Extracts: title ("name"), image URL ("contentUrl").

2. <script id="__NEXT_DATA__" type="application/json">
   A large Next.js state object.
   Extracts for each product (in order):
     - price  : found under key "/price" -> "values" -> [0] -> "value"
     - url    : found under key "urls"   -> "default"

Dependencies: requests, beautifulsoup4
"""

import json
import sys

import requests
from bs4 import BeautifulSoup

from config import BASE_URL, HEADERS, SEARCH_TERMS


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
    The length is determined by the longest list; missing slots -> None.
    """
    n = max(len(image_items), len(prices), len(urls), 0)
    products = []
    for i in range(n):
        item = image_items[i] if i < len(image_items) else {}
        products.append(
            {
                "title": item.get("name") or None,
                "image": item.get("contentUrl") or None,
                "price": prices[i] if i < len(prices) else None,
                "url": urls[i] if i < len(urls) else None,
            }
        )
    return products


#  Main
def main() -> None:
    """Loop over all search terms, scrape each one, and write a JSON file."""
    all_products = []

    for term in SEARCH_TERMS:
        url = f"{BASE_URL}{term}"
        print(f"Fetching: {url}")

        try:
            html = fetch_page(url)
        except requests.HTTPError as exc:
            print(f"HTTP error for '{term}': {exc}", file=sys.stderr)
            continue
        except requests.RequestException as exc:
            print(f"Network error for '{term}': {exc}", file=sys.stderr)
            continue

        soup = BeautifulSoup(html, "html.parser")

        # 1. Titles + image URLs  ← application/ld+json
        image_items = parse_ld_json(soup)

        # 2. Prices + product URLs  ← __NEXT_DATA__
        prices, urls = parse_next_data(soup)

        # 3. Assemble & extend the master list
        products = build_products(image_items, prices, urls)
        all_products.extend(products)

    # Write all products to a JSON file
    output_file = "output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(all_products)} product(s) to {output_file}")


if __name__ == "__main__":
    main()
