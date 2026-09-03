# Scrapling setup

[Scrapling](https://github.com/D4Vinci/Scrapling) is a Python web scraping library. It
gives you a CSS/XPath selector API over parsed HTML, plus fetchers that retrieve pages
over plain HTTP or through a real browser.

## What's installed

`scrapling[fetchers]` is listed under the `pip:` section of [`environment.yml`](../environment.yml),
which the [devcontainer Dockerfile](../.devcontainer/Dockerfile) applies with
`conda env update -n base`. A fresh codespace therefore has it already — nothing to run.

The `fetchers` extra adds `Fetcher` (HTTP, via curl_cffi), `DynamicFetcher` and
`StealthyFetcher` (browser-driven, via Playwright/Camoufox), and the `scrapling`
command line tool. Without the extra you get the parser only.

## Installing it yourself

Outside the devcontainer, or after editing `environment.yml`:

```bash
conda env update -n base -f environment.yml
```

Or straight from pip, into whichever environment you're using:

```bash
pip install "scrapling[fetchers]"
```

The browser-driven fetchers need their browsers downloaded once, which pip does not do:

```bash
scrapling install
```

Skip that step if you only need `Fetcher` and the parser — it pulls down several hundred
megabytes of browser builds.

## Verifying the install

```bash
python scripts/verify_scrapling.py
```

It prints the installed version, parses a sample flight board, and fetches the same
markup back from a temporary server on localhost:

```
scrapling 0.4.15
parser: ok
fetcher: ok
```

`fetcher: skipped` means Scrapling is installed without the `fetchers` extra. The check
never reaches the public internet, so it works on a locked-down network.

## Usage

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://example.com")
print(page.status)
print(page.css("h1::text").get())
print(page.xpath("//a/@href").getall())
```

`css()` and `xpath()` return a list of matches: `.get()` takes the first (or `None`),
`.getall()` takes them all. A `::text` suffix on a CSS selector pulls the text out of the
matched elements, and `::attr(name)` pulls an attribute.

Parsing a string you already have skips the fetchers entirely:

```python
from scrapling import Selector

page = Selector("<h1>Flights</h1>")
print(page.css("h1::text").get())
```

## Network notes

Behind a proxy, pass it per request — Scrapling's HTTP fetcher does not read the
`HTTPS_PROXY` environment variable:

```python
Fetcher.get("https://example.com", proxy="http://127.0.0.1:8080")
```

`Fetcher` mimics a browser's TLS fingerprint, which some intercepting proxies terminate
mid-handshake; that surfaces as a `curl: (35) Recv failure` SSL error rather than an
HTTP status. On such a network, fetch with `requests` and hand the HTML to `Selector`.
