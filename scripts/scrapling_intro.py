#!/usr/bin/env python3
"""Tiny, complete Scrapling example.

Fetches a public practice site made for scraping (books.toscrape.com) and pulls
out a list of books — title, price, and star rating. Run: python3 scripts/scrapling_intro.py
"""
import requests
from scrapling import Selector

URL = "https://books.toscrape.com/"

# 1. GET the HTML. (In this sandbox we fetch with requests and hand the HTML to
#    Scrapling; outside it you could use scrapling's own Fetcher.get(URL).)
resp = requests.get(URL, timeout=30)
resp.encoding = "utf-8"   # the page is UTF-8; tell requests so £ etc. decode correctly
html = resp.text
page = Selector(html, url=URL)

# 2. Point at the repeating thing — each book sits in <article class="product_pod">.
books = page.css("article.product_pod")
print(f"Found {len(books)} books on the page.\n")

# 3. For each one, pull out the pieces we want.
STARS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
for i, book in enumerate(books[:10], 1):
    title = book.css("h3 a::attr(title)").get()          # title is in the link's 'title' attribute
    price = book.css(".price_color::text").get()          # e.g. "£51.77"
    rating_word = book.css("p.star-rating::attr(class)").get().replace("star-rating", "").strip()
    stars = STARS.get(rating_word, "?")
    print(f"{i:2}. {title[:44]:44}  {price:>8}  {stars}★")
