"""Palette tests. The pinned numbers are the ones quoted in docs/decisions/0003.

Each separation is checked three ways: it reaches the house fail line of 8, it
stays within about 1 unit of the value in the decision record (so a change to a
palette or to the simulation code fails here), and it rounds to the quoted value
(so the record and the code agree).
"""

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.colors import to_hex

import visualific as vf
from visualific import _colour
from visualific.palettes import LegacyPaletteWarning

FAIL_LINE = 8.0
MARGIN = 1.0
ROOT = Path(__file__).resolve().parents[1]


def pinned(measured, documented):
    assert measured >= FAIL_LINE or documented < FAIL_LINE
    assert measured == pytest.approx(documented, abs=MARGIN)
    assert round(measured, 1) == documented


# vf.qual ------------------------------------------------------------------------------------


def test_qual_colours_and_order():
    assert tuple(vf.qual) == ("#333a80", "#d96e4c", "#598fb6", "#603d34", "#b0472c", "#4a657f")


@pytest.mark.parametrize(
    ("n", "documented"), [(2, 48.2), (3, 26.5), (4, 24.9), (5, 13.6), (6, 12.2)]
)
def test_qual_separation_by_number_of_categories(n, documented):
    worst = vf.qual.separation(n)
    pinned(worst.delta_e, documented)
    assert worst.delta_e >= FAIL_LINE


def test_qual_normal_vision_separation():
    pinned(_colour.separation(vf.qual, ["normal"]).delta_e, 14.3)


def test_qual_is_not_separated_by_lightness():
    lightness = {c: _colour.lightness(c) for c in vf.qual}
    assert abs(lightness["#d96e4c"] - lightness["#598fb6"]) == pytest.approx(1.2, abs=0.05)
    assert abs(lightness["#333a80"] - lightness["#603d34"]) == pytest.approx(2.1, abs=0.05)


def test_qual_colours_are_from_rang_unchanged():
    sources = {
        "#333a80": "golestan",
        "#d96e4c": "rasht",
        "#598fb6": "gilas",
        "#603d34": "rostan",
        "#b0472c": "shahnameh",
        "#4a657f": "rasht",
    }
    for colour, palette in sources.items():
        assert colour in vf.palettes.rang[palette]


def test_qual_contrast_on_white():
    assert min(_colour.contrast_ratio(c) for c in vf.qual) >= 3.0


# Greys ---------------------------------------------------------------------------------------


def test_observed_grey_is_far_from_every_qual_colour():
    assert vf.OBSERVED_GREY == "#808080"
    closest = min(
        _colour.difference(vf.OBSERVED_GREY, c, v) for c in vf.qual for v in _colour.VISIONS
    )
    assert closest >= 16.0
    assert closest == pytest.approx(16.0, abs=MARGIN)


def test_dark_grey_474747_is_below_the_fail_line_next_to_brown():
    protan = _colour.difference("#474747", "#603d34", "protan")
    assert protan < FAIL_LINE
    assert protan == pytest.approx(7.97, abs=0.005)


# Marker redundancy -----------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_no_markers_up_to_four_categories(n):
    styles = vf.qual.styles(n)
    assert [s["color"] for s in styles] == list(vf.qual[:n])
    assert all("marker" not in s for s in styles)


@pytest.mark.parametrize("n", [5, 6])
def test_every_series_gets_its_own_marker_from_the_fifth(n):
    markers = [s["marker"] for s in vf.qual.styles(n)]
    assert len(set(markers)) == n


def test_greyscale_needs_markers_from_the_third():
    assert "marker" not in vf.qual.styles(2, greyscale=True)[0]
    assert len({s["marker"] for s in vf.qual.styles(3, greyscale=True)}) == 3


def test_styles_never_reuse_colours():
    with pytest.raises(ValueError, match="reuse"):
        vf.qual.styles(7)
    with pytest.raises(ValueError):
        vf.qual.styles(0)


# vf.science_safe -------------------------------------------------------------------------------


def test_science_safe_colours():
    assert tuple(vf.science_safe) == ("#0c5da5", "#33a964", "#db7e00", "#da2500", "#8a678c")


def test_science_safe_separation():
    pinned(vf.science_safe.separation().delta_e, 11.0)


def test_science_safe_contrast_and_lightness():
    assert min(_colour.contrast_ratio(c) for c in vf.science_safe) >= 3.0
    assert _colour.lightness("#33a964") == pytest.approx(61.65, abs=0.005)
    assert _colour.lightness("#db7e00") == pytest.approx(61.64, abs=0.005)
    assert _colour.lightness("#da2500") == pytest.approx(47.3, abs=0.05)
    assert _colour.lightness("#8a678c") == pytest.approx(48.3, abs=0.05)


def test_science_safe_keeps_blue_and_hue_order():
    with pytest.warns(LegacyPaletteWarning):
        original = vf.legacy.science[:5]
    assert vf.science_safe[0] == original[0]
    hues = []
    for colours in (original, vf.science_safe):
        lab = _colour.lab(colours)
        hues.append(np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360)
    assert np.argsort(hues[0]).tolist() == np.argsort(hues[1]).tolist()


# Legacy -----------------------------------------------------------------------------------------


def test_scienceplots_colours_fail_under_protanopia():
    with pytest.warns(
        LegacyPaletteWarning,
        match="#00b945 and #ff9500, are 3.71 CIEDE2000 units apart under simulated protanopia",
    ):
        science = vf.legacy.science
    worst = _colour.separation(science[:5])
    pinned(worst.delta_e, 3.7)
    assert worst.colours == ("#00b945", "#ff9500")
    assert worst.vision == "protan"


@pytest.mark.parametrize("name", ["science", "science4", "tab10", "corr5"])
def test_every_legacy_palette_warns(name):
    with pytest.warns(LegacyPaletteWarning, match="reproduce published figures"):
        getattr(vf.legacy, name)


def test_unknown_legacy_palette():
    with pytest.raises(AttributeError, match="Available"):
        vf.legacy.rainbow  # noqa: B018
    assert "science" in dir(vf.legacy)


# Colormaps --------------------------------------------------------------------------------------


def ramp_lightness(cmap):
    rgb = np.asarray(cmap.colors)[:, :3]
    return _colour.linear_to_lab(_colour.srgb_to_linear(rgb))[:, 0]


@pytest.mark.parametrize("name", ["vf.termeh", "vf.rostan", "vf.mina_div"])
def test_colormaps_are_registered(name):
    assert name in mpl.colormaps
    assert f"{name}_r" in mpl.colormaps


@pytest.mark.parametrize("cmap", [vf.termeh, vf.rostan], ids=["termeh", "rostan"])
def test_sequential_maps_run_light_to_dark(cmap):
    lightness = ramp_lightness(cmap)
    assert np.all(np.diff(lightness) < 0)


def test_termeh_drops_the_near_white_stop():
    assert to_hex(vf.termeh.colors[0]) == vf.palettes.rang["termeh"][1]
    assert to_hex(vf.termeh.colors[-1]) == vf.palettes.rang["termeh"][-1]


def test_rostan_runs_from_rang_last_colour_to_first():
    assert to_hex(vf.rostan.colors[0]) == vf.palettes.rang["rostan"][-1]
    assert to_hex(vf.rostan.colors[-1]) == vf.palettes.rang["rostan"][0]


def test_mina_div_is_light_at_its_centre():
    lightness = ramp_lightness(vf.mina_div)
    assert int(np.argmax(lightness)) in (127, 128)
    centre = to_hex(vf.mina_div(0.5))
    assert _colour.difference(centre, vf.palettes.rang["mina"][3]) < 1.0


def test_mina_div_nine_samples():
    idx = [int(i) for i in np.linspace(0, 255, 9)]
    samples = [to_hex(vf.mina_div.colors[i]) for i in idx]
    assert samples == [
        "#581c1d",
        "#863c3a",
        "#ad6d6c",
        "#cbaaad",
        "#e7f1f5",
        "#90c3ee",
        "#4c9fc8",
        "#2f52a8",
        "#07187b",
    ]
    pinned(_colour.separation(samples).delta_e, 10.6)


# Vendored Rang data ----------------------------------------------------------------------------


def test_rang_data_is_the_pinned_snapshot():
    installed = Path(vf.palettes.__file__).with_name("rang.json")
    data = json.loads(installed.read_text("utf-8"))
    assert data["version"] == "0.3.0"
    assert data["commit"] == "f30cbd7f8b133e6ce0ed1b0d2ff38f7e29af09e1"
    assert data["license"] == "CC0-1.0"
    digest = hashlib.sha256(json.dumps(data["palettes"], sort_keys=True).encode()).hexdigest()
    # Checked against https://github.com/mohsennasab/Rang/tree/f30cbd7/palettes on 2026-10-15.
    assert digest == "65058e0cd7e5f8280adb14591358a2467c0f70cb58375a1eb3e48102c7728e5b"
    assert len(vf.palettes.rang) == 11
    assert sum(len(c) for c in vf.palettes.rang.values()) == 93


def test_palette_behaves_like_a_tuple():
    assert isinstance(vf.qual, tuple)
    assert vf.qual.cycler().by_key()["color"] == list(vf.qual)
    assert "qual" in repr(vf.qual)
    assert vf.qual.name == "qual"
    assert "Rang" in vf.qual.source
