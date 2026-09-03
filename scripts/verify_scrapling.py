#!/usr/bin/env python3
"""Smoke test for the Scrapling install.

Runs entirely offline: it parses a static HTML string and then fetches the same
markup from a throwaway HTTP server bound to localhost, so it works in a
codespace with no outbound network access.

Usage:
    python scripts/verify_scrapling.py
"""

import http.server
import socketserver
import sys
import threading

SAMPLE_HTML = """<html>
  <head><title>Flight board</title></head>
  <body>
    <table id="flights">
      <tr class="flight"><td class="code">DL123</td><td class="delay">14</td></tr>
      <tr class="flight"><td class="code">AA456</td><td class="delay">0</td></tr>
      <tr class="flight"><td class="code">UA789</td><td class="delay">37</td></tr>
    </table>
  </body>
</html>"""

HOST = "127.0.0.1"


def rows(page):
    """Return [(flight code, delay in minutes)] from a parsed flight board."""
    return [
        (row.css("td.code::text").get(), int(row.css("td.delay::text").get()))
        for row in page.css("tr.flight")
    ]


def check_parser():
    from scrapling import Selector

    page = Selector(SAMPLE_HTML)
    assert page.css("title::text").get() == "Flight board", "title did not parse"
    assert rows(page) == [("DL123", 14), ("AA456", 0), ("UA789", 37)], "rows did not parse"
    assert page.xpath("//td[@class='code']/text()").getall() == ["DL123", "AA456", "UA789"]
    print("parser: ok")


def check_fetcher():
    from scrapling.fetchers import Fetcher

    body = SAMPLE_HTML.encode()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    # Port 0 lets the OS pick a free port, so repeat runs never collide.
    with socketserver.TCPServer((HOST, 0), Handler) as server:
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            page = Fetcher.get(f"http://{HOST}:{port}/", timeout=15)
        finally:
            server.shutdown()

    assert page.status == 200, f"expected HTTP 200, got {page.status}"
    assert rows(page) == [("DL123", 14), ("AA456", 0), ("UA789", 37)], "fetched rows did not parse"
    print("fetcher: ok")


def main():
    import scrapling

    print(f"scrapling {scrapling.__version__}")
    check_parser()
    try:
        check_fetcher()
    except ImportError:
        print("fetcher: skipped (install the 'fetchers' extra to enable it)")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
