"""Regression tests for problems found by the pre-publication code review."""

import copy
import pickle

import matplotlib.patheffects as pe
import numpy as np
import pytest
from conftest import clean_figure, make_figure
from matplotlib.colors import to_hex
from PIL import Image

import visualific as vf
from visualific import _scripts
from visualific._check import series_colours
from visualific.palettes import LegacyPaletteWarning

# Markers ----------------------------------------------------------------------------------


def test_unfilled_markers_keep_their_colour(house):
    fig = make_figure()
    ax = fig.add_subplot()
    cross = ax.plot([0, 1], [0, 1], "x", color="#ff0000")[0]
    ring = ax.plot([0, 1], [1, 0], "o", color="#0000ff", markerfacecolor="none")[0]
    assert to_hex(cross.get_markeredgecolor()) == "#ff0000"
    assert to_hex(ring.get_markeredgecolor()) == "#0000ff"
    assert sorted(series_colours(fig)) == ["#0000ff", "#ff0000"]


def test_redundancy_markers_get_black_edges():
    for style in vf.qual.styles(5):
        assert style["markeredgecolor"] == "black"
    assert "markeredgecolor" not in vf.qual.styles(4)[0]


def test_ten_series_all_get_markers():
    with pytest.warns(LegacyPaletteWarning):
        tab10 = vf.legacy.tab10
    markers = [s["marker"] for s in tab10.styles(10, greyscale=True)]
    assert len(set(markers)) == 10


# Colour separation ------------------------------------------------------------------------


def test_uncertainty_bands_belong_to_their_line(house):
    fig = make_figure()
    ax = fig.add_subplot()
    x = np.linspace(0, 1, 20)
    for i, colour in enumerate(vf.science_safe[:2]):
        ax.plot(x, x + i, color=colour)
        ax.fill_between(x, x + i - 0.2, x + i + 0.2, color=colour, alpha=0.3)
    assert sorted(series_colours(fig)) == sorted(vf.science_safe[:2])
    assert vf.check(fig)["colour-separation"].status == "pass"


def test_translucent_fills_without_a_line_still_count(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.fill_between([0, 1], [0, 0], [1, 1], color="#333a80", alpha=0.3)
    ax.fill_between([0, 1], [1, 1], [2, 2], color="#4a657f", alpha=0.3)
    assert len(series_colours(fig)) == 2


def test_colorbar_on_user_axes_is_not_a_series(house):
    fig = make_figure()
    ax = fig.add_subplot()
    points = ax.scatter(np.arange(10), np.arange(10), c=np.arange(10), cmap="vf.mina_div")
    fig.colorbar(points, cax=ax.inset_axes([1.02, 0, 0.05, 1]), extend="both")
    assert series_colours(fig) == []


def test_inset_axes_colours_are_checked(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1], color="#333a80")
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])
    inset.plot([0, 1], [0, 1], color="#3b4486")
    assert "#3b4486" in series_colours(fig)
    assert vf.check(fig)["colour-separation"].status == "fail"


# Text ---------------------------------------------------------------------------------------


def test_text_with_a_halo_is_measured(house):
    halo = [pe.withStroke(linewidth=2, foreground="white")]
    fig = clean_figure()
    fig.axes[0].text(0.5, 0.5, "tiny", fontsize=4, path_effects=halo)
    fig.text(0.97, 0.5, "runs off the page", path_effects=halo)
    report = vf.check(fig)
    assert report["text-size"].value == pytest.approx(4)
    assert report["text-outside"].status == "fail"


def test_stretchy_delimiters_are_not_scripts(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    ax.set_ylabel(r"Error $\left|e\right|$ (m)")
    measurement = vf.check(fig)["text-size"]
    assert measurement.status == "pass"
    assert "script" not in measurement.values


def test_check_says_when_it_switched_the_script_floor_on(house, monkeypatch):
    monkeypatch.setattr(_scripts, "is_installed", lambda: False)
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([1, 10, 100], [1, 2, 3])
    ax.set_xscale("log")
    assert "switched on" in vf.check(fig)["text-size"].detail


# Saving ---------------------------------------------------------------------------------------


def test_width_rule_is_the_same_for_save_and_check(tmp_path, house):
    fig = make_figure(width=90)
    fig.add_subplot().plot([0, 1], [0, 1])
    # The PDF would be 0.5 mm off, the 600 dpi PNG 0.54 mm: refuse before writing.
    with pytest.raises(ValueError, match="Nothing was saved"):
        vf.save(fig, tmp_path / "fig", width=90.5)
    assert list(tmp_path.iterdir()) == []
    assert vf.save(fig, tmp_path / "fig.pdf", width=90.5)
    assert vf.check(fig, width=90.5)["saved-width"].status == "pass"
    assert vf.check(fig, width=90.504)["saved-width"].status == "fail"
    with pytest.raises(ValueError):
        vf.save(fig, tmp_path / "other.pdf", width=90.504)


@pytest.mark.parametrize("suffix", [".eps", ".ps", ".webp", ".svgz"])
def test_unsupported_suffixes_are_refused(tmp_path, house, suffix):
    with pytest.raises(ValueError, match="does not write"):
        vf.save(clean_figure(), tmp_path / f"fig{suffix}")
    assert list(tmp_path.iterdir()) == []


def test_dotted_names_are_kept(tmp_path, house):
    written = vf.save(clean_figure(), tmp_path / "fig.v2")
    assert [p.name for p in written] == ["fig.v2.pdf", "fig.v2.png"]


def test_tif_alias_and_rgb_tiff(tmp_path, house):
    fig = make_figure(width=40, height=25)
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    ax.set_axis_off()
    (tif,) = vf.save(fig, tmp_path / "fig", formats=["tif"], content="halftone")
    assert tif.name == "fig.tif"
    with Image.open(tif) as image:
        assert image.mode == "RGB"
        assert image.info["compression"] == "tiff_lzw"


# API ----------------------------------------------------------------------------------------------


def test_palette_survives_copy_and_pickle():
    for clone in (
        copy.copy(vf.qual),
        copy.deepcopy(vf.qual),
        pickle.loads(pickle.dumps(vf.qual)),
    ):
        assert clone == vf.qual
        assert clone.name == "qual"
        assert clone.redundancy_from == 5
        assert isinstance(clone, vf.Palette)


def test_measurements_are_hashable(house):
    report = vf.check(clean_figure())
    assert len(set(report)) == 5


def test_empty_palette_is_refused():
    with pytest.raises(ValueError, match="at least one colour"):
        vf.use(palette=[])


def test_font_names_ignore_case():
    assert vf.rc_params(font="liberation serif")["font.family"][0] == "Liberation Serif"
