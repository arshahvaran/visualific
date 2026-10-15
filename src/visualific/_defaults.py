"""House-style numbers, kept in one place.

Every size here is at the final printed size: points (pt) for type and lines,
millimetres for figure widths. The values and the reasons for them are in
docs/decisions/0002-house-style.md and 0003-default-palette.md.
"""

from __future__ import annotations

from dataclasses import dataclass

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0


@dataclass(frozen=True)
class TypeScale:
    """Type sizes in points at print size."""

    tick: float
    """Tick labels, legend entries and annotations."""
    label: float
    """Axis labels and panel titles."""
    panel: float
    """Panel letters, set in bold."""
    script_min: float = 6.0
    """Smallest size for sub- and superscripts."""


NORMAL = TypeScale(tick=8.0, label=9.0, panel=10.0)
COMPACT = TypeScale(tick=7.0, label=8.0, panel=9.0)
"""One point smaller throughout, for dense matrices and maps. Scripts stay at 6 pt."""


@dataclass(frozen=True)
class LineWeights:
    """Line widths in points at print size."""

    axes: float = 0.6
    """Axes frame and major ticks."""
    data: float = 1.2
    """Data lines."""
    reference: float = 0.8
    """Reference lines (1:1 line, zero line), drawn dashed."""
    edge: float = 0.5
    """Patch and bar edges."""
    marker_edge: float = 0.4
    """Marker edges."""
    minimum: float = 0.3
    """Nothing is drawn thinner than this."""


LINES = LineWeights()

# Typeface: Times New Roman, then the bundled Liberation Serif (same character
# widths), then STIXGeneral, which ships with matplotlib.
FONT_CHAIN = ("Times New Roman", "Liberation Serif", "STIXGeneral")
MATH_FONTSET = "stix"

# Smallest sizes accepted by vf.check. Elsevier gives 7 pt for normal text and
# 6 pt for sub- and superscripts as its rule of thumb (artwork sizing page, see
# visualific.sizes); the compact preset sits exactly on 7 pt.
MIN_TEXT_PT = 7.0
MIN_SCRIPT_PT = 6.0
MIN_LINE_PT = LINES.minimum

# Figures
DEFAULT_FIGSIZE_MM = (90.0, 65.0)
WIDTH_TOLERANCE_MM = 0.5


def width_within_tolerance(measured_mm: float, declared_mm: float) -> bool:
    """Whether a width is within 0.5 mm of the declared width (one rule for save and check)."""
    return abs(measured_mm - declared_mm) <= WIDTH_TOLERANCE_MM + 1e-6


PNG_DPI = 600

# Colour separation (CIEDE2000, worst pair over normal vision and simulated
# protanopia, deuteranopia and tritanopia). House conventions from decision record 0003.
DELTA_E_FAIL = 8.0
DELTA_E_TARGET = 10.0

OBSERVED_GREY = "#808080"
"""The one grey for observed or reference data."""
