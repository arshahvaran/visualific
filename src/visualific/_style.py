"""The house style: ``vf.use()``, ``vf.style()`` and ``vf.rc_params()`` (decision record 0002)."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Sequence

import matplotlib as mpl
from cycler import cycler

from . import _scripts
from ._defaults import (
    COMPACT,
    DEFAULT_FIGSIZE_MM,
    LINES,
    MATH_FONTSET,
    MM_PER_INCH,
    NORMAL,
    PNG_DPI,
    TypeScale,
)
from ._fonts import resolve_font
from .palettes import qual, science_safe

STYLES = ("house", "science-like")


def type_scale(compact: bool = False) -> TypeScale:
    """Type sizes in points: 8, 9 and 10 pt, or 7, 8 and 9 pt with ``compact=True``.

    Sub- and superscripts are kept at 6 pt or larger in both. A script inside a
    script can still be smaller; ``vf.check`` reports it.
    """
    return COMPACT if compact else NORMAL


def rc_params(
    name: str = "house",
    *,
    compact: bool = False,
    font: str | None = None,
    palette: Sequence | None = None,
) -> dict:
    """The matplotlib settings for a Visualific style, without applying them.

    Parameters are as for :func:`use`.
    """
    if name not in STYLES:
        raise ValueError(f"Unknown style {name!r}. Styles: {', '.join(STYLES)}.")
    scale = type_scale(compact)
    family = resolve_font(font)
    families = [family] if family == "STIXGeneral" else [family, "STIXGeneral"]
    if palette is None:
        palette = science_safe if name == "science-like" else qual
    if len(palette) == 0:
        raise ValueError("palette needs at least one colour.")
    width_mm, height_mm = DEFAULT_FIGSIZE_MM

    rc = {
        # Type. Fonts that lack a glyph fall back to STIXGeneral; mathematics
        # uses STIX, so no LaTeX installation is needed.
        "font.family": families,
        "font.serif": [*families, "DejaVu Serif"],
        "font.size": scale.tick,
        "mathtext.fontset": MATH_FONTSET,
        "text.usetex": False,
        "axes.unicode_minus": True,
        "axes.formatter.use_mathtext": True,
        "axes.formatter.useoffset": False,
        "axes.titlesize": scale.label,
        "axes.titleweight": "normal",
        "axes.titlepad": 4.0,
        "axes.labelsize": scale.label,
        "axes.labelpad": 3.0,
        "figure.titlesize": scale.label,
        "figure.labelsize": scale.label,
        "xtick.labelsize": scale.tick,
        "ytick.labelsize": scale.tick,
        "legend.fontsize": scale.tick,
        "legend.title_fontsize": scale.tick,
        # Legend: no frame.
        "legend.frameon": False,
        "legend.borderpad": 0.3,
        "legend.borderaxespad": 0.4,
        "legend.handlelength": 1.6,
        "legend.handletextpad": 0.5,
        "legend.labelspacing": 0.35,
        "legend.columnspacing": 1.2,
        "legend.markerscale": 1.0,
        # Lines, in points at print size.
        "axes.linewidth": LINES.axes,
        "lines.linewidth": LINES.data,
        "lines.markersize": 4.0,
        "lines.markeredgewidth": LINES.marker_edge,
        "lines.solid_capstyle": "round",
        "patch.linewidth": LINES.edge,
        "patch.edgecolor": "black",
        "hatch.linewidth": LINES.edge,
        "errorbar.capsize": 0.0,
        "grid.linewidth": 0.4,
        "grid.color": "#b0b0b0",
        "grid.linestyle": "--",
        "axes.grid": False,
        "axes.axisbelow": True,
        "xtick.major.width": LINES.axes,
        "ytick.major.width": LINES.axes,
        "xtick.minor.width": 0.45,
        "ytick.minor.width": 0.45,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.75,
        "ytick.minor.size": 1.75,
        "xtick.major.pad": 2.5,
        "ytick.major.pad": 2.5,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.minor.visible": False,
        "ytick.minor.visible": False,
        "axes.spines.top": True,
        "axes.spines.right": True,
        # Colour
        "axes.prop_cycle": cycler(color=list(palette)),
        "image.cmap": "vf.termeh",
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "text.color": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        # Layout: drawn at the final size, laid out by constrained layout.
        "figure.figsize": (width_mm / MM_PER_INCH, height_mm / MM_PER_INCH),
        "figure.dpi": 150,
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 2 / 72,
        "figure.constrained_layout.w_pad": 2 / 72,
        "figure.constrained_layout.hspace": 0.02,
        "figure.constrained_layout.wspace": 0.02,
        # Export: never "tight", which changes the saved width.
        "savefig.bbox": "standard",
        "savefig.dpi": PNG_DPI,
        "savefig.facecolor": "white",
        "savefig.transparent": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "path",
    }

    if name == "science-like":
        # The look SciencePlots users know: ticks inside on all four sides, with
        # minor ticks. Everything else stays house style.
        rc.update(
            {
                "xtick.direction": "in",
                "ytick.direction": "in",
                "xtick.top": True,
                "ytick.right": True,
                "xtick.minor.visible": True,
                "ytick.minor.visible": True,
                "xtick.minor.size": 1.5,
                "ytick.minor.size": 1.5,
            }
        )
    return rc


def use(
    name: str = "house",
    *,
    compact: bool = False,
    font: str | None = None,
    palette: Sequence | None = None,
) -> None:
    """Apply a Visualific style to matplotlib for the rest of the session.

    Parameters
    ----------
    name
        ``"house"`` (default) or ``"science-like"``. ``"science-like"`` keeps
        the house type and lines but draws ticks inside on all four sides, as
        SciencePlots does, and uses ``vf.science_safe`` colours.
    compact
        Use 7, 8 and 9 pt type instead of 8, 9 and 10 pt, for dense matrices
        and maps.
    font
        A typeface to use instead of the house chain (Times New Roman, then the
        bundled Liberation Serif, then STIXGeneral). ``font="Liberation Serif"``
        skips Times New Roman, so every computer uses Liberation Serif (the
        bundled copy, unless another version is installed).
    palette
        Colours for the colour cycle. Defaults to ``vf.qual``, or
        ``vf.science_safe`` for ``"science-like"``.

    Notes
    -----
    Besides the matplotlib settings, Visualific keeps mathtext sub- and
    superscripts at 6 pt or larger, which matplotlib would otherwise draw at
    70 % of their text size. This stays on for the rest of the session and only
    affects text smaller than about 8.57 pt. A script inside a script can still
    be smaller; ``vf.check`` reports it.
    """
    params = rc_params(name, compact=compact, font=font, palette=palette)
    _scripts.install()
    mpl.rcParams.update(params)


@contextlib.contextmanager
def style(
    name: str = "house",
    *,
    compact: bool = False,
    font: str | None = None,
    palette: Sequence | None = None,
) -> Iterator[None]:
    """Apply a Visualific style inside a ``with`` block.

    Takes the same arguments as :func:`use`. Matplotlib's settings are
    restored when the block ends, so save the figure inside the block or with
    ``vf.save``, which applies the export settings itself. The 6 pt floor for
    sub- and superscripts (see :func:`use`) stays on after the block.
    """
    params = rc_params(name, compact=compact, font=font, palette=palette)
    _scripts.install()
    with mpl.rc_context(params):
        yield
