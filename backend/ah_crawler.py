import time
import re
import requests

from bs4 import BeautifulSoup
from collections import deque

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from db import init_db, save_product, save_nutrition


# =========================================================
# CONFIG
# =========================================================

BASE_URL = "https://www.ah.nl"
REQUEST_DELAY = 0.7
MAX_PAGES = 10


# =========================================================
# HEADERS
# =========================================================

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    )
}


# =========================================================
# SESSION + RETRIES
# =========================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)
session.mount("http://", adapter)


# =========================================================
# FETCH
# =========================================================

def fetch(url):

    time.sleep(REQUEST_DELAY)

    try:
        print(f"[FETCH] {url}")

        response = session.get(
            url,
            timeout=10,
            headers=headers
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as e:
        print(f"[ERROR] {url} -> {e}")
        return None


# =========================================================
# HELPERS
# =========================================================

def normalize_url(url):
    return BASE_URL + url if url.startswith("/") else url


def is_product_url(url):
    return "/producten/product/" in url


def extract_product_id(url):
    match = re.search(r"(wi\d+)", url)
    return match.group(1) if match else None


# =========================================================
# NUTRITION PARSING
#
# Functions for extracting / parsing specific data from HTML
# =========================================================

def extract_nutrition_text(soup):

    heading = soup.find(string=lambda s: s and "Voedingswaarden" in s)

    if not heading:
        return None

    table = heading.find_parent().find_next("table")

    if not table:
        return None

    return table.get_text("\n", strip=True)


def extract_calories(text):
    match = re.search(r'(\d+(?:,\d+)?)\s*kcal', text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else None


def extract_grams(text):
    match = re.search(r'(\d+(?:[,.]\d+)?)\s*g', text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else None


def parse_nutrition(raw_text):
    if not raw_text:
        return None

    lines = raw_text.split("\n")

    data = {
        "energy_kcal": None,
        "carbs_g": None,
        "protein_g": None,
        "fat_g": None,
        "salt_g": None
    }

    for i, line in enumerate(lines):
        if "kcal" in line and not "Referentie-inname" in line:
            data["energy_kcal"] = extract_calories(line)

        elif "Koolhydraten" in line:
            data["carbs_g"] = extract_grams(lines[i + 1])

        elif "Eiwit" in line:
            data["protein_g"] = extract_grams(lines[i + 1])

        elif "Vet" in line:
            data["fat_g"] = extract_grams(lines[i + 1])

        elif "Zout" in line:
            data["salt_g"] = extract_grams(lines[i + 1])

    return data


# =========================================================
# PRODUCT PARSER
#
# Extract name and nutrition text from HTML, return object with all product data
# =========================================================

def parse_product_page(product_id, url, html):

    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.find("h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    nutrition_text = extract_nutrition_text(soup)
    nutrition = parse_nutrition(nutrition_text)

    return {
        "id": product_id,
        "url": url,
        "name": name,
        "nutrition": nutrition,
        "raw_text": nutrition_text
    }


# =========================================================
# CRAWLER
# =========================================================

def crawl(seed_urls, max_pages=MAX_PAGES):
    queue = deque(seed_urls)
    visited = set()
    amount_visited = 0
    seen_products = set()

    while queue and amount_visited < max_pages:
        print(f"Fetchin number { amount_visited } out of { max_pages }")
        url = queue.popleft()

        if url in visited:
            continue

        visited.add(url)
        amount_visited += 1

        html = fetch(url)

        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):

            href = normalize_url(a["href"])

            if not href.startswith(BASE_URL):
                continue


            # =================================================
            # PRODUCT PAGE
            # =================================================
            if is_product_url(href):
                product_id = extract_product_id(href)

                if product_id and product_id not in seen_products:
                    seen_products.add(product_id)
                    product_html = fetch(href)

                    if product_html:
                        data = parse_product_page(
                            product_id,
                            href,
                            product_html
                        )

                        if data["nutrition"]:
                            save_product(data)

                            save_nutrition(
                                product_id,
                                data["nutrition"],
                                data["raw_text"]
                            )
                continue

            # =================================================
            # CATEGORY / NAVIGATION
            # =================================================
            if "/producten" in href:
                if href not in visited:
                    queue.append(href)

    print(f"\nDone. Products collected: {len(seen_products)}")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_db()

    seeds = [
        "https://www.ah.nl/producten"
    ]

    crawl(seeds, max_pages=5)