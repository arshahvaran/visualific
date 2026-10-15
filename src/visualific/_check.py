"""``vf.check``: measure a finished figure against the house rules.

The five measurements are listed in the docstring of :func:`check`.
"""

from __future__ import annotations

import contextlib
import io
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np
from matplotlib.backend_bases import RendererBase
from matplotlib.colors import to_hex, to_rgba
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle
from matplotlib.mathtext import MathTextParser
from matplotlib.patheffects import PathEffectRenderer

from . import _colour, _export, _scripts
from ._defaults import (
    DELTA_E_FAIL,
    DELTA_E_TARGET,
    MIN_LINE_PT,
    MIN_SCRIPT_PT,
    MIN_TEXT_PT,
    MM_PER_INCH,
    PNG_DPI,
    WIDTH_TOLERANCE_MM,
    width_within_tolerance,
)
from .palettes import qual
from .sizes import width_mm

RULES = ("text-size", "line-width", "saved-width", "text-outside", "colour-separation")
_EPS = 1e-6
_MAX_SERIES_COLOURS = 12
_OUTSIDE_TOLERANCE_MM = 0.1


@dataclass(frozen=True)
class Measurement:
    """One measured property of a figure."""

    rule: str
    status: str
    """``"pass"``, ``"warn"``, ``"fail"`` or ``"skip"`` (nothing to measure)."""
    value: float | None
    unit: str
    limit: str
    detail: str = ""
    values: dict[str, float] = field(default_factory=dict, hash=False)
    """Named parts of the measurement, such as ``{"text": 8.0, "script": 6.0}``."""

    def __str__(self) -> str:
        value = "-" if self.value is None else f"{self.value:.3g} {self.unit}".strip()
        text = f"{self.status.upper():5s} {self.rule:18s} {value:12s} limit {self.limit}"
        return f"{text}\n      {self.detail}" if self.detail else text


@dataclass(frozen=True)
class CheckReport:
    """The result of :func:`check`."""

    measurements: tuple[Measurement, ...]

    @property
    def ok(self) -> bool:
        """True when no measurement failed. Warnings do not count as failures."""
        return not self.failures

    @property
    def failures(self) -> list[Measurement]:
        return [m for m in self.measurements if m.status == "fail"]

    @property
    def warnings(self) -> list[Measurement]:
        return [m for m in self.measurements if m.status == "warn"]

    def __getitem__(self, rule: str) -> Measurement:
        for m in self.measurements:
            if m.rule == rule:
                return m
        raise KeyError(f"No measurement {rule!r}; rules are {', '.join(RULES)}.")

    def __iter__(self):
        return iter(self.measurements)

    def __str__(self) -> str:
        counts = {s: sum(m.status == s for m in self.measurements) for s in ("fail", "warn")}
        head = (
            f"vf.check: {counts['fail']} failed, {counts['warn']} warned, "
            f"{len(self.measurements) - counts['fail'] - counts['warn']} passed or skipped"
        )
        return "\n".join([head, *(str(m) for m in self.measurements)])


class FigureCheckError(AssertionError):
    """Raised by ``vf.check(fig, strict=True)`` when a measurement fails."""

    def __init__(self, report: CheckReport):
        super().__init__(str(report))
        self.report = report


def check(
    fig: Figure,
    *,
    width: str | float | None = None,
    greyscale: bool = False,
    strict: bool = False,
) -> CheckReport:
    """Measure ``fig`` at its print size.

    Five measurements:

    ``text-size``
        Smallest text and smallest mathtext sub- or superscript. Fails below
        7 pt for text or 6 pt for scripts, Elsevier's rule of thumb (decision
        record 0002 sets the same 6 pt floor).
    ``line-width``
        Thinnest stroke drawn: lines, edges, ticks, hatching. Fails below 0.3 pt.
    ``saved-width``
        Width of the PDF that ``vf.save`` would write. Fails more than 0.5 mm
        from the declared width.
    ``text-outside``
        Text that extends past the edge of the figure. Fails for any.
    ``colour-separation``
        How far apart the closest two plotted colours are, as a CIEDE2000
        colour difference (shown as dE00), under normal vision and simulated
        protanopia, deuteranopia and tritanopia, and in greyscale on request.
        Fails below 8 and warns below the target of 10.

    Parameters
    ----------
    fig
        The finished figure.
    width
        The declared width, as a preset name or millimetres. The default is the
        figure's own width, so the saved-width measurement then only confirms
        that saving does not crop or pad the figure.
    greyscale
        Also require the series colours to differ in greyscale, for figures
        meant for black-and-white printing.
    strict
        Raise :class:`FigureCheckError` if any measurement fails.

    Returns
    -------
    CheckReport
        Print it for a table; ``report.ok`` is False when anything failed.
    """
    if not isinstance(fig, Figure):
        raise TypeError(f"Expected a matplotlib Figure, got {type(fig).__name__}.")
    floor_was_on = _scripts.is_installed()
    _scripts.install()
    declared = fig.get_figwidth() * MM_PER_INCH if width is None else width_mm(width)

    buffer = io.BytesIO()
    _export._write(fig, buffer, "pdf", PNG_DPI)
    saved = _export.measure_width_mm(buffer, "pdf", PNG_DPI)

    recorder = _Recorder(fig)
    dpi = fig.dpi
    try:
        with _record_path_effect_text(recorder):
            fig.draw(recorder)
    finally:
        if fig.dpi != dpi:  # some backends change it while finding a layout renderer
            fig.dpi = dpi

    report = CheckReport(
        (
            _text_size(recorder, floor_was_on),
            _line_width(recorder),
            _saved_width(saved, declared),
            _text_outside(recorder, fig),
            _colour_separation(fig, greyscale),
        )
    )
    if strict and not report.ok:
        raise FigureCheckError(report)
    return report


# Recording renderer -----------------------------------------------------------------


@dataclass
class _Text:
    string: str
    size: float
    script: float | None
    corners: np.ndarray | None  # (4, 2) in display pixels, y up


@dataclass
class _Stroke:
    width: float
    kind: str


class _Recorder(RendererBase):
    """A renderer that draws nothing and records text and line sizes."""

    def __init__(self, fig: Figure):
        super().__init__()
        self._fig = fig
        self.texts: list[_Text] = []
        self.strokes: list[_Stroke] = []
        self._math = MathTextParser("path")

    # Read from the figure at draw time, in case the layout engine changes the dpi.
    @property
    def dpi(self):
        return self._fig.dpi

    @property
    def width(self):
        return self._fig.bbox.width

    @property
    def height(self):
        return self._fig.bbox.height

    # canvas geometry
    def flipy(self):
        return False

    def get_canvas_width_height(self):
        return self.width, self.height

    def points_to_pixels(self, points):
        return points * self.dpi / 72.0

    # drawing
    def _stroke(self, gc, kind: str) -> None:
        width = gc.get_linewidth()
        if width > 0 and gc.get_rgb()[3] > 0:
            self.strokes.append(_Stroke(float(width), kind))
        if gc.get_hatch() is not None:
            hatch_width = getattr(gc, "get_hatch_linewidth", lambda: None)()
            if hatch_width:
                self.strokes.append(_Stroke(float(hatch_width), "hatch"))

    def draw_path(self, gc, path, transform, rgbFace=None):
        self._stroke(gc, "line")

    def draw_markers(self, gc, marker_path, marker_trans, path, trans, rgbFace=None):
        if len(path.vertices):
            self._stroke(gc, "marker or tick")

    def draw_path_collection(
        self,
        gc,
        master_transform,
        paths,
        all_transforms,
        offsets,
        offset_trans,
        facecolors,
        edgecolors,
        linewidths,
        linestyles,
        antialiaseds,
        urls,
        offset_position,
        **kwargs,
    ):
        if len(paths) == 0 or len(edgecolors) == 0:
            return
        if np.max(np.asarray(edgecolors)[:, 3]) <= 0:
            return
        widths = [float(w) for w in np.atleast_1d(linewidths) if w > 0]
        if len(np.atleast_1d(linewidths)) == 0 and gc.get_linewidth() > 0:
            widths = [float(gc.get_linewidth())]
        if widths:
            self.strokes.append(_Stroke(min(widths), "collection edge"))

    def draw_image(self, gc, x, y, im, transform=None):
        pass

    def draw_gouraud_triangles(self, gc, triangles_array, colors_array, transform):
        pass

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        if not s or gc.get_rgb()[3] <= 0:
            return
        size = float(prop.get_size_in_points())
        script = None
        if ismath:
            # Scripts are the glyphs shrunk once or more by the script factor.
            # Other small glyphs, such as delimiters sized to fit, are not scripts.
            factor = _scripts.shrink_factor(size)
            levels = [size * factor**k for k in (1, 2, 3)]
            glyph_sizes = [float(g[1]) for g in self._math.parse(s, 72, prop).glyphs]
            scripts = [g for g in glyph_sizes if any(abs(g - lv) < 0.01 for lv in levels)]
            script = min(scripts) if scripts else None
        w, h, d = self.get_text_width_height_descent(s, prop, ismath)
        local = np.array([(0.0, -d), (w, -d), (w, h - d), (0.0, h - d)])
        theta = math.radians(angle)
        rotation = np.array(
            [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
        )
        corners = local @ rotation.T + (x, y)
        self.texts.append(_Text(s, size, script, corners))

    def draw_tex(self, gc, x, y, s, prop, angle, *, mtext=None):
        if s:
            self.texts.append(_Text(s, float(prop.get_size_in_points()), None, None))


@contextlib.contextmanager
def _record_path_effect_text(recorder: _Recorder):
    """Also record text drawn with path effects, such as a halo.

    Matplotlib draws such text as outlines through a ``PathEffectRenderer``,
    which never passes the text itself to the underlying renderer.
    """
    own = PathEffectRenderer.__dict__.get("draw_text")
    inherited = PathEffectRenderer.draw_text

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        if getattr(self, "_renderer", None) is recorder:
            recorder.draw_text(gc, x, y, s, prop, angle, ismath, mtext)
        return inherited(self, gc, x, y, s, prop, angle, ismath=ismath, mtext=mtext)

    PathEffectRenderer.draw_text = draw_text
    try:
        yield
    finally:
        if own is None:
            del PathEffectRenderer.draw_text
        else:  # pragma: no cover - matplotlib currently inherits draw_text
            PathEffectRenderer.draw_text = own


# Measurements --------------------------------------------------------------------------


def _short(s: str, n: int = 40) -> str:
    """``s`` quoted, shortened and plain ASCII, for printing on any console.

    Mathtext markup is dropped, so the tick label ``$\\mathdefault{10^{3}}$``
    reads ``'10^{3}'``.
    """
    s = re.sub(r"\\mathdefault\{(.*)\}", r"\1", s).replace("$", "")
    s = s.replace("\u2212", "-")  # matplotlib's minus sign
    s = s if len(s) <= n else s[: n - 3] + "..."
    return "'" + s.encode("ascii", "backslashreplace").decode("ascii") + "'"


def _text_size(rec: _Recorder, floor_was_on: bool = True) -> Measurement:
    limit = f"{MIN_TEXT_PT:g} pt text, {MIN_SCRIPT_PT:g} pt scripts"
    if not rec.texts:
        return Measurement("text-size", "skip", None, "pt", limit, "No text drawn.")
    text = min(rec.texts, key=lambda t: t.size)
    scripts = [t for t in rec.texts if t.script is not None]
    script = min(scripts, key=lambda t: t.script) if scripts else None
    text_failed = text.size < MIN_TEXT_PT - _EPS
    script_failed = script is not None and script.script < MIN_SCRIPT_PT - _EPS
    detail = f"Smallest text {text.size:.2f} pt in {_short(text.string)}"
    if text_failed:
        detail += f", below {MIN_TEXT_PT:g} pt"
    values = {"text": round(text.size, 3)}
    if script is not None:
        detail += f"; smallest script {script.script:.2f} pt in {_short(script.string)}"
        if script_failed:
            detail += f", below {MIN_SCRIPT_PT:g} pt"
        values["script"] = round(script.script, 3)
        if not floor_was_on:
            detail += (
                ". Scripts were measured with Visualific's 6 pt floor, which this check "
                "switched on; files saved earlier with plain savefig have scripts at 70 % "
                "of the text size"
            )
    return Measurement(
        "text-size",
        "fail" if text_failed or script_failed else "pass",
        values["text"],
        "pt",
        limit,
        detail + ".",
        values,
    )


def _line_width(rec: _Recorder) -> Measurement:
    limit = f"{MIN_LINE_PT:g} pt"
    if not rec.strokes:
        return Measurement("line-width", "skip", None, "pt", limit, "No lines drawn.")
    thinnest = min(rec.strokes, key=lambda s: s.width)
    failed = thinnest.width < MIN_LINE_PT - _EPS
    count = sum(s.width < MIN_LINE_PT - _EPS for s in rec.strokes)
    detail = f"Thinnest stroke {thinnest.width:.3g} pt ({thinnest.kind})"
    if count:
        detail += f"; {count} strokes below {MIN_LINE_PT:g} pt"
    return Measurement(
        "line-width",
        "fail" if failed else "pass",
        round(thinnest.width, 4),
        "pt",
        limit,
        detail + ".",
    )


def _saved_width(saved: float, declared: float) -> Measurement:
    failed = not width_within_tolerance(saved, declared)
    off = round(saved - declared, 2) + 0.0  # no "-0.00"
    return Measurement(
        "saved-width",
        "fail" if failed else "pass",
        round(saved, 2),
        "mm",
        f"{declared:g} +/- {WIDTH_TOLERANCE_MM:g} mm",
        f"The saved PDF is {saved:.2f} mm wide, {off:+.2f} mm from the declared {declared:g} mm.",
    )


def _text_outside(rec: _Recorder, fig: Figure) -> Measurement:
    tol = _OUTSIDE_TOLERANCE_MM / MM_PER_INCH * fig.dpi
    outside = []
    for t in rec.texts:
        if t.corners is None:
            continue
        (x0, y0), (x1, y1) = t.corners.min(axis=0), t.corners.max(axis=0)
        if x0 < -tol or y0 < -tol or x1 > rec.width + tol or y1 > rec.height + tol:
            outside.append(t.string)
    detail = (
        "All text is inside the figure."
        if not outside
        else f"{len(outside)} text items extend past the edge: "
        + ", ".join(_short(s, 30) for s in outside[:3])
        + ("..." if len(outside) > 3 else "")
        + "."
    )
    return Measurement(
        "text-outside", "fail" if outside else "pass", float(len(outside)), "", "0", detail
    )


def _colour_separation(fig: Figure, greyscale: bool) -> Measurement:
    limit = f"fail < {DELTA_E_FAIL:g}, target {DELTA_E_TARGET:g}"
    colours = series_colours(fig)
    if len(colours) < 2:
        return Measurement(
            "colour-separation", "skip", None, "dE00", limit, "Fewer than two series colours."
        )
    if len(colours) > _MAX_SERIES_COLOURS:
        return Measurement(
            "colour-separation",
            "warn",
            None,
            "dE00",
            limit,
            f"{len(colours)} distinct colours, more than {_MAX_SERIES_COLOURS}; this looks like "
            "continuous colour, which is not measured. Map values with a colormap "
            "(c=values, cmap=...) so they are recognised.",
        )
    visions = (*_colour.VISIONS, "greyscale") if greyscale else _colour.VISIONS
    worst = _colour.separation(colours, visions)
    status = (
        "fail"
        if worst.delta_e < DELTA_E_FAIL
        else "warn"
        if worst.delta_e < DELTA_E_TARGET
        else "pass"
    )
    detail = f"Closest pair {worst} among {len(colours)} colours."
    dark_grey = "#474747"
    used_qual = [c for c in colours if c in qual]
    if dark_grey in colours and used_qual:
        status = "fail"
        detail += (
            f" {dark_grey} is not used with vf.qual (decision record 0003): it is only "
            f"{_colour.difference(dark_grey, qual[3], 'protan'):.2f} from {qual[3]} under "
            "simulated protanopia. Use #808080 for observed or reference data."
        )
    return Measurement("colour-separation", status, round(worst.delta_e, 2), "dE00", limit, detail)


# Series colours ------------------------------------------------------------------------

_NO_LINE = ("None", "none", "", " ")


_OPAQUE = 0.98


@dataclass
class _Collector:
    """Colours seen, as (colour without alpha, colour on white, opaque) entries."""

    entries: list[tuple[str, str, bool]] = field(default_factory=list)

    def add(self, rgba) -> None:
        r, g, b, a = (float(v) for v in rgba)
        if a < 0.02:
            return
        on_white = to_hex(np.array([r, g, b]) * a + (1 - a))
        if on_white != "#ffffff":
            self.entries.append((to_hex((r, g, b)), on_white, a >= _OPAQUE))

    def add_many(self, colours: Iterable) -> None:
        for rgba in colours:
            self.add(rgba)

    def series(self) -> list[str]:
        # A translucent fill in the colour of an opaque series, such as an
        # uncertainty band around its line, belongs to that series.
        opaque = {base for base, _, solid in self.entries if solid}
        found: dict[str, None] = {}
        for base, on_white, solid in self.entries:
            if solid or base not in opaque:
                found[on_white] = None
        return list(found)


def _data_axes(fig: Figure) -> list:
    """Axes that hold data: inset axes included, colour bars left out."""
    colorbar_axes = set()
    axes, todo = [], list(fig.get_axes())
    while todo:
        ax = todo.pop(0)
        if ax in axes:
            continue
        axes.append(ax)
        todo.extend(getattr(ax, "child_axes", []))
        for mappable in (*ax.images, *ax.collections):
            colorbar = getattr(mappable, "colorbar", None)
            if colorbar is not None:
                colorbar_axes.add(colorbar.ax)
    return [
        ax
        for ax in axes
        if ax.get_visible() and ax not in colorbar_axes and ax.get_label() != "<colorbar>"
    ]


def _is_filled(line) -> bool:
    """Whether the line's marker is a filled shape (not ``"x"`` or ``"+"``)."""
    return bool(MarkerStyle(line.get_marker()).is_filled())


def series_colours(fig: Figure) -> list[str]:
    """Distinct colours of the data drawn in ``fig``, as they appear on white.

    Covers lines, markers, filled areas, bars and other patches, and collections
    such as scatter points and error bars, in every axes including insets. Left
    out: artists coloured through a colormap, images, text, axes, colour bars,
    white, and translucent fills in the colour of an opaque series (such as an
    uncertainty band around its line).
    """
    out = _Collector()
    for ax in _data_axes(fig):
        for line in ax.get_lines():
            if not line.get_visible():
                continue
            alpha = line.get_alpha()
            if line.get_linestyle() not in _NO_LINE and line.get_linewidth() > 0:
                out.add(to_rgba(line.get_color(), alpha))
            elif line.get_marker() not in (None, *_NO_LINE):
                face = to_rgba(line.get_markerfacecolor(), alpha)
                if _is_filled(line) and face[3] > 0:
                    out.add(face)
                else:
                    out.add(to_rgba(line.get_markeredgecolor(), alpha))
        for coll in ax.collections:
            if not coll.get_visible() or coll.get_array() is not None:
                continue
            if len(coll.get_paths()) == 0:
                continue
            faces = np.atleast_2d(coll.get_facecolor())
            edges = np.atleast_2d(coll.get_edgecolor())
            if faces.size and faces[:, 3].max() > 0:
                out.add_many(faces)
            elif edges.size:
                out.add_many(edges)
        for patch in ax.patches:
            if not patch.get_visible():
                continue
            face = patch.get_facecolor()
            if patch.get_fill() and face[3] > 0:
                out.add(face)
            elif patch.get_linewidth() > 0:
                out.add(patch.get_edgecolor())
    return out.series()
