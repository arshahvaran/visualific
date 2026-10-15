"""Visualific: publication figures for engineering and environmental research.

Figures are drawn at their final printed size in one house style::

    import matplotlib.pyplot as plt
    import visualific as vf

    vf.use()
    fig, ax = plt.subplots(figsize=vf.figsize("elsevier-single", 60))
    ax.plot([0, 1, 2], [1, 3, 2], label="Model")
    print(vf.check(fig, width="elsevier-single"))
    vf.save(fig, "figures/fig1", width="elsevier-single")

The package is in early development. The figure templates arrive later in v0.1;
see the README for the plan.
"""

from . import palettes, sizes
from ._check import CheckReport, FigureCheckError, Measurement, check
from ._defaults import LINES, OBSERVED_GREY, LineWeights, TypeScale
from ._export import TIFF_DPI, save
from ._style import rc_params, style, type_scale, use
from .palettes import (
    LegacyPaletteWarning,
    Palette,
    legacy,
    mina_div,
    qual,
    rostan,
    science_safe,
    termeh,
)
from .sizes import WIDTHS, figsize, width_mm

__version__ = "0.0.1.dev0"

__all__ = [
    "LINES",
    "OBSERVED_GREY",
    "TIFF_DPI",
    "WIDTHS",
    "CheckReport",
    "FigureCheckError",
    "LegacyPaletteWarning",
    "LineWeights",
    "Measurement",
    "Palette",
    "TypeScale",
    "__version__",
    "check",
    "figsize",
    "legacy",
    "mina_div",
    "palettes",
    "qual",
    "rc_params",
    "rostan",
    "save",
    "science_safe",
    "sizes",
    "style",
    "termeh",
    "type_scale",
    "use",
    "width_mm",
]
