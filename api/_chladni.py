"""Núcleo matemático das figuras de Chladni (somente numpy).

Todas as funções devolvem um campo de deslocamento w(x, y) normalizado em [-1, 1].
As linhas nodais (w = 0) são onde a areia se acumula.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

PLATES = {
    "square": "Quadrada (modos m, n)",
    "rect": "Retangular (proporção livre)",
    "circle": "Circular (Bessel)",
    "ring": "Anel (membrana anular)",
    "mix": "Superposição de modos",
}


# ---------------------------------------------------------------- Bessel (numpy)
def bessel_j(n: int, x: np.ndarray, steps: int = 400) -> np.ndarray:
    """J_n(x) pela representação integral de Bessel (precisa para o uso aqui)."""
    x = np.asarray(x, dtype=float)
    tau = (np.arange(steps) + 0.5) * np.pi / steps
    arg = n * tau[None, :] - x.reshape(-1, 1) * np.sin(tau)[None, :]
    return (np.cos(arg).sum(axis=1) / steps).reshape(x.shape)


@lru_cache(maxsize=None)
def bessel_zeros(n: int, count: int) -> tuple:
    """Primeiros `count` zeros positivos de J_n (varredura + bisseção)."""
    zeros: list[float] = []
    step = 0.1
    x = max(step, n * 0.5) if n else step
    prev = float(bessel_j(n, np.array([x]))[0])
    while len(zeros) < count and x < 200:
        nxt = x + step
        cur = float(bessel_j(n, np.array([nxt]))[0])
        if prev == 0.0 or prev * cur < 0:
            lo, hi = x, nxt
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                fm = float(bessel_j(n, np.array([mid]))[0])
                flo = float(bessel_j(n, np.array([lo]))[0])
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo = mid
            zeros.append(0.5 * (lo + hi))
        x, prev = nxt, cur
    return tuple(zeros)


def bessel_y_like(n: int, x: np.ndarray, steps: int = 600) -> np.ndarray:
    """Y_n(x) (integral de Bessel de 2ª espécie), usada no modo anular."""
    x = np.asarray(x, dtype=float)
    t = np.linspace(0, 8, steps)
    dt = t[1] - t[0]
    xs = x.reshape(-1, 1)
    integ = np.exp(-xs * np.sinh(t)[None, :]) * (np.exp(n * t)[None, :] + (-1) ** n * np.exp(-n * t)[None, :])
    tau = (np.arange(steps) + 0.5) * np.pi / steps
    part1 = (np.sin(xs * np.sin(tau)[None, :] - n * tau[None, :])).sum(axis=1) / steps
    part2 = integ.sum(axis=1) * dt / np.pi
    return (part1 - part2).reshape(x.shape)


# ---------------------------------------------------------------- utilitários
def _norm(w: np.ndarray) -> np.ndarray:
    m = np.nanmax(np.abs(w))
    return w / m if m > 0 else w


def _grid(res: int, aspect: float = 1.0):
    """Malha [0,1] x [0,1]; `aspect` = largura/altura (altura fixa em 1)."""
    ny = res
    nx = max(8, int(round(res * aspect)))
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    return np.meshgrid(x, y)  # X.shape == (ny, nx)


# ---------------------------------------------------------------- placas
def square(m: int, n: int, sign: int = 1, res: int = 128):
    X, Y = _grid(res)
    w = np.cos(n * np.pi * X) * np.cos(m * np.pi * Y) + sign * np.cos(m * np.pi * X) * np.cos(n * np.pi * Y)
    return _norm(w), float(m * m + n * n)


def rect(m: int, n: int, aspect: float = 1.5, res: int = 128):
    X, Y = _grid(res, aspect)
    a = aspect
    w = np.cos(n * np.pi * X) * np.cos(m * np.pi * Y)
    return _norm(w), float((n / a) ** 2 + m ** 2)


def circle(n: int, k: int, res: int = 128):
    """Membrana circular presa: J_n(z_{n,k} r) cos(n θ), raio = 1."""
    z = bessel_zeros(n, k)[k - 1]
    ax = np.linspace(-1, 1, res)
    X, Y = np.meshgrid(ax, ax)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    w = bessel_j(n, z * r) * np.cos(n * th)
    w = np.where(r <= 1.0, w, np.nan)
    return _norm(w), float(z * z)


@lru_cache(maxsize=None)
def _ring_roots(n: int, inner: float, count: int = 8) -> tuple:
    ks = np.linspace(0.5, 60, 4000)

    def f(kk):
        # condição de contorno nos dois raios: J(k a) Y(k) - J(k) Y(k a) = 0
        return bessel_j(n, kk * inner) * bessel_y_like(n, kk) - bessel_j(n, kk) * bessel_y_like(n, kk * inner)

    vals = f(ks)
    roots = []
    for i in range(len(ks) - 1):
        if vals[i] * vals[i + 1] < 0:
            lo, hi = ks[i], ks[i + 1]
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if f(np.array([lo]))[0] * f(np.array([mid]))[0] <= 0:
                    hi = mid
                else:
                    lo = mid
            roots.append(0.5 * (lo + hi))
        if len(roots) >= count:
            break
    return tuple(roots)


def ring(n: int, k: int, inner: float = 0.35, res: int = 128):
    """Membrana anular presa em r=inner e r=1: combinação J_n/Y_n com zeros em ambos os raios."""
    roots = _ring_roots(n, round(inner, 3))
    kk = roots[min(k, len(roots)) - 1]
    ax = np.linspace(-1, 1, res)
    X, Y = np.meshgrid(ax, ax)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    c = bessel_j(n, np.array([kk]))[0] / bessel_y_like(n, np.array([kk]))[0]
    radial = bessel_j(n, kk * np.clip(r, 1e-6, None)) - c * bessel_y_like(n, kk * np.clip(r, 1e-6, None))
    w = radial * np.cos(n * th)
    w = np.where((r <= 1.0) & (r >= inner), w, np.nan)
    return _norm(w), float(kk * kk)


def mix(m: int, n: int, mix_: float = 0.5, res: int = 128):
    """Superposição geral: cos(nπx)cos(mπy) + mix·cos(mπx)cos(nπy), mix em [-1, 1]."""
    X, Y = _grid(res)
    a = np.cos(n * np.pi * X) * np.cos(m * np.pi * Y)
    b = np.cos(m * np.pi * X) * np.cos(n * np.pi * Y)
    return _norm(a + mix_ * b), float(m * m + n * n)


# ---------------------------------------------------------------- despacho
def compute(plate: str, m: int = 1, n: int = 2, sign: int = 1, aspect: float = 1.5, mix_: float = 0.5,
            inner: float = 0.35, res: int = 128):
    if plate == "square":
        return square(m, n, sign, res)
    if plate == "rect":
        return rect(m, n, aspect, res)
    if plate == "circle":
        return circle(n, max(1, m), res)
    if plate == "ring":
        return ring(n, max(1, m), inner, res)
    if plate == "mix":
        return mix(m, n, mix_, res)
    raise ValueError(f"placa desconhecida: {plate}")


def gallery(plate: str, kmax: int = 5, res: int = 64, aspect: float = 1.5, mix_: float = 0.5, inner: float = 0.35):
    """Todas as variações (modos) de uma placa até a ordem `kmax`."""
    items = []
    if plate in ("square", "mix"):
        for m in range(0, kmax + 1):
            for n in range(m + 1, kmax + 1):
                signs = (1, -1) if plate == "square" else (1,)
                for s in signs:
                    w, f = compute(plate, m, n, s, aspect, mix_, inner, res)
                    items.append({"plate": plate, "m": m, "n": n, "sign": s, "freq": f, "w": _pack(w)})
    elif plate == "rect":
        for m in range(0, kmax + 1):
            for n in range(0, kmax + 1):
                if m == 0 and n == 0:
                    continue
                w, f = compute(plate, m, n, 1, aspect, mix_, inner, res)
                items.append({"plate": plate, "m": m, "n": n, "sign": 1, "freq": f, "w": _pack(w)})
    elif plate in ("circle", "ring"):
        for n in range(0, kmax + 1):
            for k in range(1, max(2, kmax - n + 1) + 1):
                try:
                    w, f = compute(plate, k, n, 1, aspect, mix_, inner, res)
                except Exception:
                    continue
                items.append({"plate": plate, "m": k, "n": n, "sign": 1, "freq": f, "w": _pack(w)})
    items.sort(key=lambda d: d["freq"])
    shape = list(items[0]["w"]["shape"]) if items else [0, 0]
    return items, shape


def _pack(w: np.ndarray) -> dict:
    """Quantiza para int8 (-127..127, NaN -> -128) e devolve como lista: compacto no JSON."""
    q = np.where(np.isnan(w), -128, np.round(np.nan_to_num(w) * 127)).astype(int)
    return {"shape": list(w.shape), "data": q.flatten().tolist()}


def pack(w: np.ndarray) -> dict:
    return _pack(w)
