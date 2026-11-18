"""GET /api/pattern?plate=square&m=2&n=3&sign=1&res=160 -> campo w(x,y) de um modo."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(__file__))
import _chladni as c  # noqa: E402


def _int(q, k, d, lo, hi):
    try:
        return max(lo, min(hi, int(q.get(k, [d])[0])))
    except ValueError:
        return d


def _float(q, k, d, lo, hi):
    try:
        return max(lo, min(hi, float(q.get(k, [d])[0])))
    except ValueError:
        return d


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        plate = q.get("plate", ["square"])[0]
        try:
            w, f = c.compute(
                plate,
                m=_int(q, "m", 2, 0, 12),
                n=_int(q, "n", 3, 0, 12),
                sign=-1 if q.get("sign", ["1"])[0] == "-1" else 1,
                aspect=_float(q, "aspect", 1.5, 0.5, 3.0),
                mix_=_float(q, "mix", 0.5, -1.0, 1.0),
                inner=_float(q, "inner", 0.35, 0.1, 0.8),
                res=_int(q, "res", 160, 16, 320),
            )
            body = json.dumps({"plate": plate, "freq": f, **c.pack(w)}).encode()
            status = 200
        except Exception as e:  # noqa: BLE001
            body, status = json.dumps({"error": str(e)}).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "public, s-maxage=86400, stale-while-revalidate")
        self.end_headers()
        self.wfile.write(body)
