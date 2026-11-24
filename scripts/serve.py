"""Serve the static site locally with caching disabled, so the browser always shows the latest files.

Usage: python scripts/serve.py [port]   (default 8000) -> http://localhost:8000
"""
import functools
import http.server
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / 'site'


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(NoCacheHandler, directory=str(SITE))
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    except OSError:
        sys.exit(f'Port {port} is already in use. Close the other explorer window, or run: python scripts/serve.py 8010')
    print(f'Stress Atlas: http://localhost:{port}  (serving {SITE}, caching off). Press Ctrl+C to stop.')
    server.serve_forever()
