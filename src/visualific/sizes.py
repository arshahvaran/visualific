"""Figure widths in millimetres, with the source of every number.

Draw each figure at the width it will be printed at::

    import matplotlib.pyplot as plt
    import visualific as vf

    fig, ax = plt.subplots(figsize=vf.figsize("elsevier-single", 60))

Each preset records the page it was taken from and the date that page was
read. Publishers change their guides, so check the page before submission.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._defaults import DEFAULT_FIGSIZE_MM, MM_PER_INCH

__all__ = ["WIDTHS", "Width", "figsize", "width_mm"]

_ELSEVIER_SIZING = (
    "https://www.elsevier.com/about/policies-and-standards/author/"
    "artwork-and-media-instructions/artwork-sizing"
)
_NATURE_FINAL = "https://www.nature.com/nature/for-authors/final-submission"
_ACCESSED = "2026-10-15"
_NATURE_NOTE = (
    "Width only. Nature also asks for 5 to 7 pt Arial or Helvetica, which the "
    "house style (8 to 10 pt serif) does not follow; that needs its own profile."
)


@dataclass(frozen=True)
class Width:
    """A figure width taken from a publisher's guide."""

    name: str
    mm: float
    publisher: str
    description: str
    source: str
    """URL of the page the number comes from."""
    accessed: str
    """Date (ISO 8601) the page was read."""
    note: str = ""

    @property
    def inches(self) -> float:
        return self.mm / MM_PER_INCH


WIDTHS: dict[str, Width] = {
    w.name: w
    for w in (
        Width("elsevier-single", 90.0, "Elsevier", "single column", _ELSEVIER_SIZING, _ACCESSED),
        Width("elsevier-onehalf", 140.0, "Elsevier", "1.5 column", _ELSEVIER_SIZING, _ACCESSED),
        Width(
            "elsevier-double",
            190.0,
            "Elsevier",
            "double column (full width)",
            _ELSEVIER_SIZING,
            _ACCESSED,
        ),
        Width(
            "nature-single",
            89.0,
            "Nature",
            "single column",
            _NATURE_FINAL,
            _ACCESSED,
            _NATURE_NOTE,
        ),
        Width(
            "nature-double",
            183.0,
            "Nature",
            "double column",
            _NATURE_FINAL,
            _ACCESSED,
            _NATURE_NOTE,
        ),
    )
}
"""Width presets by name."""


def width_mm(width: str | float) -> float:
    """A preset name or a number of millimetres, as millimetres."""
    if isinstance(width, str):
        try:
            return WIDTHS[width].mm
        except KeyError:
            names = ", ".join(sorted(WIDTHS))
            raise ValueError(f"Unknown width {width!r}. Presets: {names}.") from None
    value = float(width)
    if not value > 0:
        raise ValueError(f"Width must be positive, got {width!r} mm.")
    return value


def figsize(
    width: str | float | None = None,
    height: float | None = None,
    *,
    aspect: float | None = None,
) -> tuple[float, float]:
    """Figure size in inches for matplotlib, from millimetres.

    Parameters
    ----------
    width
        A preset name such as ``"elsevier-single"``, or a width in mm. The
        default is the house default of 90 mm.
    height
        Height in mm.
    aspect
        Height divided by width, used when ``height`` is not given. The
        default keeps the house proportions of 90 x 65 mm.
    """
    default_w, default_h = DEFAULT_FIGSIZE_MM
    w = default_w if width is None else width_mm(width)
    if height is not None and aspect is not None:
        raise ValueError("Give height or aspect, not both.")
    if height is None:
        height = w * (default_h / default_w if aspect is None else aspect)
    if not height > 0:
        raise ValueError(f"Height must be positive, got {height!r} mm.")
    return (w / MM_PER_INCH, height / MM_PER_INCH)
