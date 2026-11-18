"""Servidor local de desenvolvimento: serve /public e roteia /api/* para os handlers Python.
Uso: python dev.py  ->  http://localhost:3000   (alternativa: `vercel dev`)"""
import importlib
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))


class Dev(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            mod = importlib.import_module(path[5:].strip("/"))
            return mod.handler.do_GET(self)
        f = os.path.join(ROOT, "public", "index.html" if path == "/" else path.lstrip("/"))
        if not os.path.isfile(f):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(f)[0] or "application/octet-stream")
        self.end_headers()
        self.wfile.write(open(f, "rb").read())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Dev).serve_forever()
