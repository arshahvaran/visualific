"""The bundled Liberation Serif and the choice of typeface."""

from __future__ import annotations

from pathlib import Path

from matplotlib import font_manager

from ._defaults import FONT_CHAIN

BUNDLED_FAMILY = "Liberation Serif"
BUNDLED_FILES = (
    "LiberationSerif-Regular.ttf",
    "LiberationSerif-Bold.ttf",
    "LiberationSerif-Italic.ttf",
    "LiberationSerif-BoldItalic.ttf",
)

_registered_with = None  # the font manager the bundled files were added to


def bundled_font_paths() -> list[Path]:
    """Paths of the bundled Liberation Serif files (version 2.1.5, unmodified)."""
    folder = Path(__file__).parent / "fonts"
    return [folder / name for name in BUNDLED_FILES]


def register_bundled_fonts() -> None:
    """Make the bundled Liberation Serif known to matplotlib. Safe to call repeatedly."""
    global _registered_with
    manager = font_manager.fontManager
    if _registered_with is manager:
        return
    known = {Path(entry.fname).resolve() for entry in manager.ttflist}
    for path in bundled_font_paths():
        if path.resolve() not in known:
            manager.addfont(str(path))
    _registered_with = manager


def installed_name(family: str) -> str | None:
    """The installed font family matching ``family`` (ignoring case), or None."""
    wanted = family.casefold()
    for entry in font_manager.fontManager.ttflist:
        if entry.name.casefold() == wanted:
            return entry.name
    return None


def is_installed(family: str) -> bool:
    """Whether matplotlib can find a font file for ``family``."""
    return installed_name(family) is not None


def resolve_font(family: str | None = None) -> str:
    """Return the typeface the house style will use.

    With ``family=None`` this is the first installed font in the chain Times New
    Roman, Liberation Serif, STIXGeneral. Liberation Serif is bundled, so the
    chain only reaches STIXGeneral if the bundled files are missing. A named
    ``family`` must be installed; case does not matter.
    """
    register_bundled_fonts()
    if family is not None:
        name = installed_name(family)
        if name is None:
            raise ValueError(
                f"Font {family!r} is not installed. Pass font=None to use the house chain "
                f"({', '.join(FONT_CHAIN)}), or font={BUNDLED_FAMILY!r} for the bundled font."
            )
        return name
    for candidate in FONT_CHAIN:
        name = installed_name(candidate)
        if name is not None:
            return name
    return "DejaVu Serif"  # pragma: no cover - STIXGeneral ships with matplotlib
