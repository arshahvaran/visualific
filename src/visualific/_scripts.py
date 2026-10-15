"""Keep mathtext sub- and superscripts at 6 pt or larger.

Matplotlib's mathtext draws a script at 70 % of the size of the text it belongs
to, so the exponent of an 8 pt tick label such as 10^-3 prints at 5.6 pt.
Decision record 0002 sets 6 pt as the floor. Matplotlib has no setting for
this, so Visualific raises mathtext's shrink factor for small text while an
expression is parsed: the factor becomes max(0.7, 6 pt / text size), capped at
1. Text larger than 6 / 0.7 (about 8.57 pt) is unchanged, because its scripts
are already 6 pt or larger. Second-level scripts (a script inside a script)
shrink twice and can still fall below 6 pt; ``vf.check`` reports them.

The change is installed the first time ``vf.use``, ``vf.style``, ``vf.save`` or
``vf.check`` runs and stays for the rest of the session. Switching it off again
would leave matplotlib's text-size caches out of date.
"""

from __future__ import annotations

import functools
import warnings
import weakref

from ._defaults import MIN_SCRIPT_PT

_installed = False
_BASE_FACTOR = 0.7  # matplotlib's mathtext.SHRINK_FACTOR


def shrink_factor(fontsize: float) -> float:
    """The factor by which a script shrinks from text of ``fontsize`` pt.

    0.7 as in matplotlib, raised for small text once the floor is installed.
    A hair above the floor, so that rounding never lands at 5.999... pt.
    """
    if not _installed or fontsize <= 0:
        return _BASE_FACTOR
    return min(1.0, max(_BASE_FACTOR, (MIN_SCRIPT_PT + 1e-9) / fontsize))


def install() -> bool:
    """Install the script-size floor. Return whether it is active."""
    global _installed, _BASE_FACTOR
    if _installed:
        return True
    try:
        from matplotlib import _mathtext
    except ImportError:  # pragma: no cover - present in every supported matplotlib
        _mathtext = None
    parser = getattr(_mathtext, "Parser", None)
    base = getattr(_mathtext, "SHRINK_FACTOR", None)
    if parser is None or not isinstance(base, float):  # pragma: no cover
        warnings.warn(
            "This matplotlib version does not expose the mathtext shrink factor, so "
            "sub- and superscripts keep matplotlib's size. vf.check still measures them.",
            RuntimeWarning,
            stacklevel=3,
        )
        return False

    original = parser.parse
    _BASE_FACTOR = base

    @functools.wraps(original)
    def parse(self, s, fonts_object, fontsize, dpi):
        factor = shrink_factor(fontsize)
        if factor == base:
            return original(self, s, fonts_object, fontsize, dpi)
        saved = _mathtext.SHRINK_FACTOR
        _mathtext.SHRINK_FACTOR = factor
        try:
            return original(self, s, fonts_object, fontsize, dpi)
        finally:
            _mathtext.SHRINK_FACTOR = saved

    parser.parse = parse
    _clear_text_caches()
    _installed = True
    return True


def is_installed() -> bool:
    return _installed


def _clear_text_caches() -> None:
    """Drop matplotlib's cached text layouts, which were measured before the floor."""
    from matplotlib import mathtext, text

    cached = getattr(mathtext.MathTextParser, "_parse_cached", None)
    if hasattr(cached, "cache_clear"):
        cached.cache_clear()
    older = getattr(text, "_get_text_metrics_with_cache_impl", None)
    if hasattr(older, "cache_clear"):
        older.cache_clear()
    newer = getattr(text, "_get_text_metrics_function", None)
    for default in getattr(newer, "__defaults__", None) or ():
        if isinstance(default, weakref.WeakKeyDictionary):
            default.clear()
