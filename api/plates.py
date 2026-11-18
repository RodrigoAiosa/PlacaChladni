"""GET /api/plates -> lista de tipos de placa."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
import _chladni as c  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(c.PLATES).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
