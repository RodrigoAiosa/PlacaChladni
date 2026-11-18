import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
import _chladni as c  # noqa: E402


def test_bessel_zeros():
    assert np.allclose(c.bessel_zeros(0, 3), [2.4048, 5.5201, 8.6537], atol=1e-3)
    assert np.allclose(c.bessel_zeros(1, 2), [3.8317, 7.0156], atol=1e-3)


def test_square_symmetry():
    w, _ = c.square(2, 3, 1, 64)
    assert np.allclose(w, w.T, atol=1e-9)        # modo simétrico
    w, _ = c.square(2, 3, -1, 64)
    assert np.allclose(w, -w.T, atol=1e-9)       # modo antissimétrico


def test_circle_edge_is_nodal():
    w, _ = c.circle(2, 2, 201)
    ax = np.linspace(-1, 1, 201)
    X, Y = np.meshgrid(ax, ax)
    r = np.hypot(X, Y)
    edge = (r > 0.985) & (r <= 1.0)
    assert np.nanmax(np.abs(w[edge])) < 0.2


def test_gallery_counts():
    items, _ = c.gallery("square", 4, 24)
    assert len(items) == 20
    assert all(a["freq"] <= b["freq"] for a, b in zip(items, items[1:]))
