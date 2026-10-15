"""``vf.save``: write a figure at exactly its declared width (decision record 0002)."""

from __future__ import annotations

import io
import os
import re
from collections.abc import Sequence
from pathlib import Path

import matplotlib as mpl
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.figure import Figure
from PIL import Image

from . import _scripts
from ._defaults import (
    MM_PER_INCH,
    PNG_DPI,
    PT_PER_INCH,
    WIDTH_TOLERANCE_MM,
    width_within_tolerance,
)
from .sizes import width_mm

TIFF_DPI = {"line": 1000, "combination": 500, "halftone": 300}
"""TIFF resolution by content type, from Elsevier's artwork types page.

Line art (graphs, diagrams) 1000 dpi, combination art (line art with photos)
500 dpi, halftones (photos) 300 dpi. Source:
https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-types
(read 2026-10-15). Elsevier asks for 1200 dpi when line art has very fine lines.
"""

_EXPORT_RC = {
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "path",
    "savefig.bbox": "standard",
    "savefig.transparent": False,
}
_SUFFIXES = {".pdf": "pdf", ".png": "png", ".tif": "tiff", ".tiff": "tiff", ".svg": "svg"}
_FORMATS = ("pdf", "png", "tiff", "svg")
_ALIASES = {"tif": "tiff"}
_EXTENSION = {"pdf": ".pdf", "png": ".png", "tiff": ".tif", "svg": ".svg"}
_RASTER = ("png", "tiff")


def save(
    fig: Figure,
    path: str | os.PathLike,
    *,
    width: str | float | None = None,
    formats: Sequence[str] | None = None,
    content: str = "line",
) -> list[Path]:
    """Save ``fig`` at its declared width as a PDF and a 600 dpi PNG.

    The PDF, with TrueType (Type 42) fonts, is the file to submit; the PNG is
    for previews. Nothing is cropped: the saved width equals the figure width,
    and every file written is measured afterwards.

    Parameters
    ----------
    fig
        The figure, drawn at its final size.
    path
        Output path. Without a suffix, ``"fig1"`` writes ``fig1.pdf`` and
        ``fig1.png``. With a suffix (``.pdf``, ``.png``, ``.tif``, ``.svg``)
        only that format is written. Missing folders are created.
    width
        The declared width: a preset name such as ``"elsevier-single"`` or a
        number of millimetres. If a file would be more than 0.5 mm wider or
        narrower, nothing is saved and a ``ValueError`` explains how to create
        the figure at the right size. The default is the figure's own width.
    formats
        Formats to write, from ``"pdf"``, ``"png"``, ``"tiff"`` (or ``"tif"``)
        and ``"svg"``, when ``path`` has no suffix. Default ``("pdf", "png")``.
        TIFF files are RGB, without an alpha channel.
    content
        For TIFF: ``"line"`` (graphs, 1000 dpi), ``"combination"`` (500 dpi) or
        ``"halftone"`` (photographs, 300 dpi).

    Returns
    -------
    list of Path
        The files written.
    """
    if not isinstance(fig, Figure):
        raise TypeError(f"Expected a matplotlib Figure, got {type(fig).__name__}.")
    if content not in TIFF_DPI:
        raise ValueError(f"content must be one of {', '.join(TIFF_DPI)}, got {content!r}.")
    figure_mm = fig.get_figwidth() * MM_PER_INCH
    declared = figure_mm if width is None else width_mm(width)
    targets = _targets(Path(path), formats)
    for fmt, _ in targets:
        expected = _expected_width_mm(fig, fmt, _dpi(fmt, content))
        if not width_within_tolerance(expected, declared):
            example = "vf.figsize(...)" if width is None else f"vf.figsize({width!r})"
            raise ValueError(
                f"The figure is {figure_mm:.2f} mm wide, so the {fmt.upper()} would be "
                f"{expected:.2f} mm, more than {WIDTH_TOLERANCE_MM:g} mm from the declared "
                f"{declared:g} mm. Nothing was saved. Create the figure at its final width, "
                f"for example plt.subplots(figsize={example}), instead of resizing it "
                "when saving."
            )

    _scripts.install()
    written = []
    for fmt, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        dpi = _dpi(fmt, content)
        _write(fig, target, fmt, dpi)
        saved = measure_width_mm(target, fmt, dpi)
        if not width_within_tolerance(saved, declared):  # pragma: no cover - safeguard
            raise RuntimeError(
                f"{target.name} is {saved:.2f} mm wide, not the declared {declared:g} mm."
            )
        written.append(target)
    return written


def _dpi(fmt: str, content: str) -> float:
    return TIFF_DPI[content] if fmt == "tiff" else PNG_DPI


def _expected_width_mm(fig: Figure, fmt: str, dpi: float) -> float:
    """Width the saved file will have: exact for vector files, whole pixels for raster."""
    inches = fig.get_figwidth()
    if fmt in _RASTER:
        inches = int(inches * dpi) / dpi  # matplotlib truncates to whole pixels
    return inches * MM_PER_INCH


def _targets(path: Path, formats: Sequence[str] | None) -> list[tuple[str, Path]]:
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        raise ValueError(
            "JPEG is lossy and blurs lines and text. Save line art as PDF, PNG or TIFF."
        )
    if suffix[1:] in FigureCanvasBase.get_supported_filetypes() and suffix not in _SUFFIXES:
        raise ValueError(
            f"vf.save does not write {suffix} files. Use .pdf, .png, .tif or .svg, or "
            "fig.savefig for other formats."
        )
    if suffix in _SUFFIXES:
        if formats is not None:
            raise ValueError("Give either a path with a suffix or formats=, not both.")
        return [(_SUFFIXES[suffix], path)]
    if isinstance(formats, str):
        raise TypeError("formats must be a sequence such as ('pdf', 'png'), not a string.")
    chosen = ("pdf", "png") if formats is None else tuple(_ALIASES.get(f, f) for f in formats)
    unknown = [f for f in chosen if f not in _FORMATS]
    if not chosen:
        raise ValueError(f"formats is empty; choose from {', '.join(_FORMATS)}.")
    if unknown:
        raise ValueError(f"Unknown formats {unknown}; choose from {', '.join(_FORMATS)}.")
    return [(fmt, path.with_name(path.name + _EXTENSION[fmt])) for fmt in dict.fromkeys(chosen)]


def _write(fig: Figure, target, fmt: str, dpi: float) -> None:
    with mpl.rc_context(_EXPORT_RC):
        if fmt != "tiff":
            fig.savefig(target, format=fmt, dpi=dpi, bbox_inches=None)
            return
        # TIFF for submission: RGB without an alpha channel, LZW-compressed.
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=dpi, bbox_inches=None)
    buffer.seek(0)
    with Image.open(buffer) as image:
        image.convert("RGB").save(target, format="TIFF", dpi=(dpi, dpi), compression="tiff_lzw")


def measure_width_mm(target, fmt: str, dpi: float) -> float:
    """Width of a saved figure in millimetres, read from the file itself."""
    if isinstance(target, io.BytesIO):
        data = target.getvalue()
    else:
        data = Path(target).read_bytes()
    if fmt == "pdf":
        match = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", data)
        if match is None:  # pragma: no cover - matplotlib always writes one
            raise RuntimeError("No MediaBox found in the PDF.")
        return (float(match[3]) - float(match[1])) / PT_PER_INCH * MM_PER_INCH
    if fmt == "svg":
        match = re.search(rb'<svg[^>]*?\swidth="([\d.]+)pt"', data)
        if match is None:  # pragma: no cover
            raise RuntimeError("No width found in the SVG.")
        return float(match[1]) / PT_PER_INCH * MM_PER_INCH
    with Image.open(io.BytesIO(data)) as image:
        return image.size[0] / dpi * MM_PER_INCH
