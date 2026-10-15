"""Colour palettes and colormaps (decision record 0003).

Categorical palettes are :class:`Palette` objects, which behave like tuples of
hex strings, so they can go anywhere matplotlib expects a list of colours.
Sequential and diverging palettes are matplotlib colormaps, registered under
``"vf.<name>"`` so that ``cmap="vf.termeh"`` also works.

The Rang colours are copied unchanged from Rang 0.3.0 by Mohsen Tahmasebi Nasab
(https://github.com/mohsennasab/Rang), which dedicates its palette values to the
public domain under CC0 1.0. They are in ``rang.json`` next to this file.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib as mpl
import numpy as np
from cycler import Cycler, cycler
from matplotlib.colors import Colormap, LinearSegmentedColormap, ListedColormap, to_hex

from .. import _colour
from .._defaults import DELTA_E_FAIL, OBSERVED_GREY

__all__ = [
    "MARKERS",
    "OBSERVED_GREY",
    "LegacyPaletteWarning",
    "Palette",
    "legacy",
    "mina_div",
    "qual",
    "rang",
    "rostan",
    "science_safe",
    "termeh",
]

_DATA = json.loads((Path(__file__).parent / "rang.json").read_text(encoding="utf-8"))

rang: dict[str, tuple[str, ...]] = {
    key: tuple(c.lower() for c in entry["colors"]) for key, entry in _DATA["palettes"].items()
}
"""The vendored Rang palettes by lower-case name, colours in Rang's listed order."""

RANG_VERSION = _DATA["version"]
RANG_COMMIT = _DATA["commit"]

MARKERS = ("o", "s", "^", "D", "v", "P", "X", "<", "p", "h")
"""Markers added for redundancy, in order. All are filled shapes."""


class Palette(tuple):
    """An ordered set of colours with a name and a note on where it comes from.

    A ``Palette`` is a tuple of lower-case hex strings::

        ax.set_prop_cycle(color=vf.qual)

    Parameters
    ----------
    colours
        Colours in any matplotlib format.
    name
        Short name, such as ``"qual"``.
    source
        Where the colours come from.
    redundancy_from
        Number of categories at which :meth:`styles` adds markers, so that
        series stay distinguishable without colour. ``None`` never adds them.
    """

    name: str
    source: str
    redundancy_from: int | None

    def __new__(
        cls,
        colours,
        *,
        name: str,
        source: str = "",
        redundancy_from: int | None = 5,
    ):
        self = super().__new__(cls, (to_hex(c) for c in colours))
        self.name = name
        self.source = source
        self.redundancy_from = redundancy_from
        return self

    def __getnewargs_ex__(self):
        # Lets copy, deepcopy and pickle rebuild a Palette with its keywords.
        keywords = {
            "name": self.name,
            "source": self.source,
            "redundancy_from": self.redundancy_from,
        }
        return (tuple(self),), keywords

    def __repr__(self) -> str:
        return f"Palette({self.name!r}, {list(self)!r})"

    def cycler(self) -> Cycler:
        """A colour cycler for ``axes.prop_cycle`` or ``ax.set_prop_cycle``."""
        return cycler(color=list(self))

    def separation(self, n: int | None = None, *, greyscale: bool = False) -> _colour.Separation:
        """Closest pair among the first ``n`` colours (all by default), over all visions.

        This is the score from decision record 0003: CIEDE2000 under normal
        vision and simulated protanopia, deuteranopia and tritanopia.
        ``greyscale=True`` adds the difference in lightness alone.
        """
        colours = self if n is None else self[:n]
        visions = (*_colour.VISIONS, "greyscale") if greyscale else _colour.VISIONS
        return _colour.separation(colours, visions)

    def styles(self, n: int, *, greyscale: bool = False) -> list[dict]:
        """Matplotlib style keywords for ``n`` series.

        From ``redundancy_from`` categories on (5 for ``vf.qual``), every series
        also gets its own marker: with five or six categories the closest
        ``vf.qual`` colours are 13.6 and 12.2 CIEDE2000 units apart, above the
        target but close enough that reds and blues start to look related.
        ``greyscale=True`` adds markers from the third category on, because
        ``vf.qual`` is not separated by lightness.

        Each dict has ``color`` and, where markers are added, ``marker`` and a
        black ``markeredgecolor`` (0.4 pt edges in the house style)::

            for (name, df), kw in zip(groups, vf.qual.styles(len(groups))):
                ax.plot(df.x, df.y, label=name, **kw)
        """
        if n < 1:
            raise ValueError("n must be at least 1.")
        if n > len(self):
            raise ValueError(
                f"Palette {self.name!r} has {len(self)} colours; {n} series would reuse "
                "colours. Group the data, highlight one series, or use small multiples."
            )
        threshold = 3 if greyscale else self.redundancy_from
        styles: list[dict] = [{"color": c} for c in self[:n]]
        if threshold is not None and n >= threshold:
            if n > len(MARKERS):
                raise ValueError(f"Only {len(MARKERS)} markers are available for {n} series.")
            for style, marker in zip(styles, MARKERS, strict=False):
                style["marker"] = marker
                style["markeredgecolor"] = "black"
        return styles


qual = Palette(
    ("#333a80", "#d96e4c", "#598fb6", "#603d34", "#b0472c", "#4a657f"),
    name="qual",
    source=(
        "Rang 0.3.0 (CC0): Golestan, Rasht, Gilas, Rostan, Shahnameh and Rasht colours, "
        "picked for maximum separation under colour vision deficiency (decision record 0003)"
    ),
)
"""Default categorical palette: indigo, terracotta, steel blue, brown, rust, slate."""

science_safe = Palette(
    ("#0c5da5", "#33a964", "#db7e00", "#da2500", "#8a678c"),
    name="science_safe",
    source=(
        "The first five SciencePlots colours, adjusted for colour vision deficiency "
        "(decision record 0003)"
    ),
)
"""The SciencePlots colours in the same hue order, adjusted for colour vision deficiency.

Not separated by lightness: green and orange have the same L*, so figures for
greyscale printing need dashes or markers.
"""


# Sequential and diverging colormaps --------------------------------------------------

_RAMP_STEPS = 256


def _lab_ramp(name: str, anchors, positions=None) -> ListedColormap:
    """A colormap interpolated linearly in CIELAB between anchor colours."""
    anchor_lab = _colour.lab(anchors)
    if positions is None:
        positions = np.linspace(0.0, 1.0, len(anchors))
    t = np.linspace(0.0, 1.0, _RAMP_STEPS)
    ramp = np.stack([np.interp(t, positions, anchor_lab[:, i]) for i in range(3)], axis=-1)
    return ListedColormap(_colour.lab_to_srgb(ramp), name=name)


termeh = _lab_ramp("vf.termeh", rang["termeh"][1:])
"""Sequential blues from Rang's Termeh, light (low) to dark (high).

Rang's near-white first stop is left out, so the lowest value stays visible on
white. Interpolated in CIELAB; L* falls steadily from about 87 to 32. Made for
water: depth, concentration, bathymetry.
"""

rostan = _lab_ramp("vf.rostan", rang["rostan"][::-1])
"""Sequential warm ramp from Rang's Rostan, light (low) to dark (high).

Rang lists Rostan from dark to light; Visualific reverses it so that every
sequential map runs light to dark. For temperature, radiation and heat.
"""

_MINA_POSITIONS = np.concatenate([np.linspace(0.0, 0.5, 4), np.linspace(0.5, 1.0, 6)[1:]])
mina_div = _lab_ramp("vf.mina_div", rang["mina"], _MINA_POSITIONS)
"""Diverging red to blue from Rang's Mina, with its enamel white at the centre (0.5).

Rang's Mina has three red stops and five blue stops, so spaced evenly its light
colour sits at 0.375. Here the red stops fill 0 to 0.5 and the blue stops fill
0.5 to 1, so a centred norm puts the light colour at zero. Use only for signed
data. ``vf.mina_div.reversed()`` puts blue at the negative end.
"""


def _register(cmap: Colormap) -> None:
    for item in (cmap, cmap.reversed()):
        if item.name not in mpl.colormaps:
            mpl.colormaps.register(item)


for _cmap in (termeh, rostan, mina_div):
    _register(_cmap)


# Legacy palettes ---------------------------------------------------------------------


class LegacyPaletteWarning(UserWarning):
    """A legacy palette was used. They exist only to reproduce published figures."""


_LEGACY = {
    "science": Palette(
        ("#0c5da5", "#00b945", "#ff9500", "#ff2c00", "#845b97", "#474747", "#9e9e9e"),
        name="legacy.science",
        source="The SciencePlots default colour cycle",
        redundancy_from=None,
    ),
    "science4": Palette(
        ("#0c5da5", "#ff9500", "#ff2c00", "#845b97"),
        name="legacy.science4",
        source="The SciencePlots colours without the green",
        redundancy_from=None,
    ),
    "tab10": Palette(
        mpl.colormaps["tab10"].colors,
        name="legacy.tab10",
        source="matplotlib's default colour cycle (tab10)",
        redundancy_from=None,
    ),
}

_LEGACY_CMAPS = {
    "corr5": LinearSegmentedColormap.from_list(
        "vf.legacy.corr5", ["#001b82", "#0034ff", "#ffffff", "#ff000d", "#7d0006"]
    ),
}


_SEEN_WITH = {
    "normal": "with normal colour vision",
    "protan": "under simulated protanopia",
    "deutan": "under simulated deuteranopia",
    "tritan": "under simulated tritanopia",
    "greyscale": "in greyscale",
}


class _Legacy:
    """Palettes kept only to reproduce figures that are already published.

    Every access gives a :class:`LegacyPaletteWarning` with the palette's
    measured separation. Use ``vf.qual`` or ``vf.science_safe`` for new figures.

    - ``science``: the SciencePlots default cycle (7 colours).
    - ``science4``: the SciencePlots colours without the green.
    - ``tab10``: matplotlib's default cycle.
    - ``corr5``: a saturated blue-white-red colormap.
    """

    def __dir__(self):
        return sorted([*_LEGACY, *_LEGACY_CMAPS])

    def __getattr__(self, name: str):
        if name in _LEGACY:
            palette = _LEGACY[name]
            worst = palette.separation()
            a, b = worst.colours
            verdict = "below" if worst.delta_e < DELTA_E_FAIL else "above"
            warnings.warn(
                f"vf.legacy.{name} is kept only to reproduce published figures. Its closest "
                f"colours, {a} and {b}, are {worst.delta_e:.2f} CIEDE2000 units apart "
                f"{_SEEN_WITH[worst.vision]}, {verdict} Visualific's fail line of "
                f"{DELTA_E_FAIL:g}. Use vf.qual or vf.science_safe for new figures.",
                LegacyPaletteWarning,
                stacklevel=2,
            )
            return palette
        if name in _LEGACY_CMAPS:
            warnings.warn(
                f"vf.legacy.{name} is kept only to reproduce published figures. Its colours "
                "are saturated and partly outside the print gamut. Use vf.mina_div for new "
                "figures.",
                LegacyPaletteWarning,
                stacklevel=2,
            )
            return _LEGACY_CMAPS[name]
        raise AttributeError(f"No legacy palette {name!r}. Available: {', '.join(dir(self))}.")


legacy = _Legacy()
