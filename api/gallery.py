"""GET /api/gallery?plate=square&kmax=5&res=64 -> todas as variações (modos) de uma placa."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(__file__))
import _chladni as c  # noqa: E402


def _num(q, k, d, lo, hi, cast=int):
    try:
        return max(lo, min(hi, cast(q.get(k, [d])[0])))
    except ValueError:
        return d


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        plate = q.get("plate", ["square"])[0]
        try:
            items, shape = c.gallery(
                plate,
                kmax=_num(q, "kmax", 5, 2, 8),
                res=_num(q, "res", 64, 24, 128),
                aspect=_num(q, "aspect", 1.5, 0.5, 3.0, float),
                mix_=_num(q, "mix", 0.5, -1.0, 1.0, float),
                inner=_num(q, "inner", 0.35, 0.1, 0.8, float),
            )
            body, status = json.dumps({"plate": plate, "shape": shape, "items": items}).encode(), 200
        except Exception as e:  # noqa: BLE001
            body, status = json.dumps({"error": str(e)}).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "public, s-maxage=86400, stale-while-revalidate")
        self.end_headers()
        self.wfile.write(body)
