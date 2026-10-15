"""Colour measurement used by the palettes and by ``vf.check``.

Method (decision record 0003): colours are sRGB with a D65 white. Colour vision deficiency
is simulated with the Machado, Oliveira and Fernandes (2009) matrices at
severity 1.0, applied to linear RGB, with out-of-gamut results clipped. Colour
difference is CIEDE2000 (Sharma, Wu and Dalal 2005). Greyscale keeps each
colour's relative luminance, so two colours look alike in greyscale when their
CIELAB lightness L* is close.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from matplotlib.colors import to_hex, to_rgb

VISIONS = ("normal", "protan", "deutan", "tritan")
"""Normal vision and the three simulated dichromacies."""

# sRGB (linear) to CIE XYZ, D65 white
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_XYZ_TO_RGB = np.linalg.inv(_RGB_TO_XYZ)
_WHITE = np.array([0.95047, 1.0, 1.08883])
_EPSILON = 216 / 24389
_KAPPA = 24389 / 27

# Machado, Oliveira and Fernandes (2009), severity 1.0, for linear RGB
_MACHADO = {
    "protan": np.array(
        [
            [0.152286, 1.052583, -0.204868],
            [0.114503, 0.786281, 0.099216],
            [-0.003882, -0.048116, 1.051998],
        ]
    ),
    "deutan": np.array(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ]
    ),
    "tritan": np.array(
        [
            [1.255528, -0.076749, -0.178779],
            [-0.078411, 0.930809, 0.147602],
            [0.004733, 0.691367, 0.303900],
        ]
    ),
}


def to_srgb(colours) -> np.ndarray:
    """Colours in any matplotlib format as an (n, 3) array of sRGB values in 0..1."""
    if isinstance(colours, str):
        colours = [colours]
    return np.array([to_rgb(c) for c in colours], dtype=float).reshape(-1, 3)


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=float)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def linear_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Linear RGB (..., 3) to CIELAB (..., 3)."""
    xyz = np.asarray(rgb, dtype=float) @ _RGB_TO_XYZ.T / _WHITE
    f = np.where(xyz > _EPSILON, np.cbrt(xyz), (_KAPPA * xyz + 16) / 116)
    lightness = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([lightness, a, b], axis=-1)


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """CIELAB (..., 3) to sRGB in 0..1, clipped to the gamut."""
    lab = np.asarray(lab, dtype=float)
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    x = np.where(fx**3 > _EPSILON, fx**3, (116 * fx - 16) / _KAPPA)
    y = np.where(lab[..., 0] > _KAPPA * _EPSILON, fy**3, lab[..., 0] / _KAPPA)
    z = np.where(fz**3 > _EPSILON, fz**3, (116 * fz - 16) / _KAPPA)
    xyz = np.stack([x, y, z], axis=-1) * _WHITE
    return linear_to_srgb(xyz @ _XYZ_TO_RGB.T)


def simulate(colours, vision: str) -> np.ndarray:
    """Linear RGB (n, 3) of ``colours`` as seen with ``vision``.

    ``vision`` is one of ``"normal"``, ``"protan"``, ``"deutan"``, ``"tritan"``
    or ``"greyscale"``.
    """
    linear = srgb_to_linear(to_srgb(colours))
    if vision == "normal":
        return linear
    if vision == "greyscale":
        luminance = linear @ _RGB_TO_XYZ[1]
        return np.repeat(luminance[:, None], 3, axis=1)
    if vision not in _MACHADO:
        raise ValueError(f"Unknown vision {vision!r}; use one of {(*VISIONS, 'greyscale')}.")
    return np.clip(linear @ _MACHADO[vision].T, 0.0, 1.0)


def lab(colours, vision: str = "normal") -> np.ndarray:
    """CIELAB (n, 3) of ``colours`` as seen with ``vision``."""
    return linear_to_lab(simulate(colours, vision))


def lightness(colour) -> float:
    """CIELAB lightness L* of one colour."""
    return float(lab(colour)[0, 0])


def delta_e2000(lab1, lab2) -> np.ndarray:
    """CIEDE2000 colour difference between CIELAB arrays (broadcast over leading axes)."""
    lab1 = np.asarray(lab1, dtype=float)
    lab2 = np.asarray(lab2, dtype=float)
    l1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    l2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    c_mean = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    g = 0.5 * (1 - np.sqrt(c_mean**7 / (c_mean**7 + 25.0**7)))
    a1p, a2p = a1 * (1 + g), a2 * (1 + g)
    c1p, c2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    neutral = (c1p * c2p) == 0

    dl = l2 - l1
    dc = c2p - c1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(neutral, 0.0, dh)
    dh_big = 2 * np.sqrt(c1p * c2p) * np.sin(np.radians(dh / 2))

    l_mean = (l1 + l2) / 2
    cp_mean = (c1p + c2p) / 2
    h_sum = h1p + h2p
    h_mean = np.where(
        np.abs(h1p - h2p) <= 180,
        h_sum / 2,
        np.where(h_sum < 360, (h_sum + 360) / 2, (h_sum - 360) / 2),
    )
    h_mean = np.where(neutral, h_sum, h_mean)

    t = (
        1
        - 0.17 * np.cos(np.radians(h_mean - 30))
        + 0.24 * np.cos(np.radians(2 * h_mean))
        + 0.32 * np.cos(np.radians(3 * h_mean + 6))
        - 0.20 * np.cos(np.radians(4 * h_mean - 63))
    )
    d_theta = 30 * np.exp(-(((h_mean - 275) / 25) ** 2))
    r_c = 2 * np.sqrt(cp_mean**7 / (cp_mean**7 + 25.0**7))
    s_l = 1 + 0.015 * (l_mean - 50) ** 2 / np.sqrt(20 + (l_mean - 50) ** 2)
    s_c = 1 + 0.045 * cp_mean
    s_h = 1 + 0.015 * cp_mean * t
    r_t = -np.sin(np.radians(2 * d_theta)) * r_c
    return np.sqrt(
        (dl / s_l) ** 2 + (dc / s_c) ** 2 + (dh_big / s_h) ** 2 + r_t * (dc / s_c) * (dh_big / s_h)
    )


def difference(colour1, colour2, vision: str = "normal") -> float:
    """CIEDE2000 difference between two colours as seen with ``vision``."""
    return float(delta_e2000(lab(colour1, vision)[0], lab(colour2, vision)[0]))


@dataclass(frozen=True)
class Separation:
    """The closest pair of colours in a set."""

    delta_e: float
    """CIEDE2000 difference of the closest pair."""
    colours: tuple[str, str]
    vision: str
    """The vision under which the pair is closest."""

    def __str__(self) -> str:
        a, b = self.colours
        return f"{self.delta_e:.2f} ({a} vs {b}, {self.vision})"


def separation(colours: Sequence, visions: Iterable[str] = VISIONS) -> Separation:
    """Closest pair of ``colours`` over all ``visions``.

    This is the score in decision record 0003: below 8 fails, 10 or more is the target.
    """
    hexes = [to_hex(c) for c in colours]
    if len(hexes) < 2:
        raise ValueError("Separation needs at least two colours.")
    best: Separation | None = None
    pairs = list(itertools.combinations(range(len(hexes)), 2))
    first = np.array([i for i, _ in pairs])
    second = np.array([j for _, j in pairs])
    for vision in visions:
        values = lab(hexes, vision)
        distances = delta_e2000(values[first], values[second])
        k = int(np.argmin(distances))
        if best is None or distances[k] < best.delta_e:
            best = Separation(float(distances[k]), (hexes[first[k]], hexes[second[k]]), vision)
    assert best is not None
    return best


def relative_luminance(colour) -> float:
    """WCAG relative luminance."""
    return float(srgb_to_linear(to_srgb(colour))[0] @ np.array([0.2126, 0.7152, 0.0722]))


def contrast_ratio(colour, background="#ffffff") -> float:
    """WCAG contrast ratio between two colours (1 to 21)."""
    a, b = relative_luminance(colour), relative_luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)
