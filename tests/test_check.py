import numpy as np
import pytest
from conftest import clean_figure, make_figure

import visualific as vf
from visualific._check import RULES, series_colours
from visualific.palettes import LegacyPaletteWarning


def statuses(report):
    return {m.rule: m.status for m in report}


def test_clean_figure_passes_every_rule(house):
    report = vf.check(clean_figure(), width="elsevier-single")
    assert [m.rule for m in report] == list(RULES)
    assert report.ok, str(report)
    assert statuses(report) == dict.fromkeys(RULES, "pass")
    assert report["text-size"].value == pytest.approx(8.0)  # tick labels
    assert report["text-size"].values["script"] == pytest.approx(6.3, abs=1e-3)  # m^3 at 9 pt
    assert "'Discharge (m^3 s^{-1})'" in report["text-size"].detail
    assert report["line-width"].value == pytest.approx(0.6)  # axes and ticks
    assert report["saved-width"].value == pytest.approx(90.0, abs=0.01)
    assert report["text-outside"].value == 0


def test_small_text_fails(house):
    fig = clean_figure()
    fig.axes[0].text(0.5, 0.5, "tiny", fontsize=5)
    report = vf.check(fig)
    assert report["text-size"].status == "fail"
    assert report["text-size"].value == pytest.approx(5)
    assert "'tiny'" in report["text-size"].detail
    assert not report.ok


def test_compact_text_passes():
    with vf.style(compact=True):
        report = vf.check(clean_figure())
    assert report["text-size"].status == "pass"


def test_second_level_script_fails(house):
    fig = clean_figure()
    fig.axes[0].set_title(r"$e^{x^{2}}$", fontsize=8)
    report = vf.check(fig)
    assert report["text-size"].status == "fail"
    assert report["text-size"].value == pytest.approx(8.0)
    assert report["text-size"].values["script"] < 6
    assert "below 6 pt" in report["text-size"].detail


def test_text_measured_without_the_house_style():
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    ax.tick_params(labelsize=6)
    report = vf.check(fig)
    assert report["text-size"].value == pytest.approx(6)
    assert report["text-size"].status == "fail"


def test_thin_line_fails(house):
    fig = clean_figure()
    fig.axes[0].axhline(1, linewidth=0.2, color="black")
    report = vf.check(fig)
    assert report["line-width"].status == "fail"
    assert report["line-width"].value == pytest.approx(0.2)


def test_thin_collection_edges_fail(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.scatter([0, 1, 2], [0, 1, 2], edgecolors="black", linewidths=0.1)
    assert vf.check(fig)["line-width"].status == "fail"


def test_hidden_edges_are_not_counted(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.bar([0, 1], [1, 2], edgecolor="none", linewidth=0.1)
    assert vf.check(fig)["line-width"].status == "pass"


def test_text_outside_the_canvas_fails(house):
    fig = clean_figure()
    fig.text(0.98, 0.5, "a note that runs off the page")
    report = vf.check(fig)
    assert report["text-outside"].status == "fail"
    assert report["text-outside"].value == 1
    assert "runs off" in report["text-outside"].detail


def test_rotated_text_outside_the_canvas_fails(house):
    fig = clean_figure()
    fig.text(0.5, 0.98, "rotated label", rotation=90)
    assert vf.check(fig)["text-outside"].status == "fail"


def test_declared_width_mismatch_fails(house):
    report = vf.check(clean_figure("elsevier-single"), width="elsevier-double")
    assert report["saved-width"].status == "fail"
    assert report["saved-width"].value == pytest.approx(90, abs=0.01)


def test_scienceplots_colours_fail_colour_separation(house):
    fig = make_figure()
    ax = fig.add_subplot()
    with pytest.warns(LegacyPaletteWarning):
        colours = vf.legacy.science[:5]
    for i, colour in enumerate(colours):
        ax.plot([0, 1], [i, i + 1], color=colour)
    measurement = vf.check(fig)["colour-separation"]
    assert measurement.status == "fail"
    assert measurement.value == pytest.approx(3.7, abs=0.05)
    assert "#00b945 vs #ff9500, protan" in measurement.detail


def test_science_safe_passes(house):
    fig = make_figure()
    ax = fig.add_subplot()
    for i, colour in enumerate(vf.science_safe):
        ax.plot([0, 1], [i, i + 1], color=colour)
    measurement = vf.check(fig)["colour-separation"]
    assert measurement.status == "pass"
    assert measurement.value == pytest.approx(11.0, abs=0.05)


def test_greyscale_option(house):
    fig = make_figure()
    ax = fig.add_subplot()
    for i, colour in enumerate(vf.qual[:3]):
        ax.plot([0, 1], [i, i + 1], color=colour)
    assert vf.check(fig)["colour-separation"].status == "pass"
    greyscale = vf.check(fig, greyscale=True)["colour-separation"]
    assert greyscale.status == "fail"
    assert "greyscale" in greyscale.detail


def test_dark_grey_next_to_qual_fails(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1], color=vf.qual[0])
    ax.plot([0, 1], [1, 0], color="#474747")
    measurement = vf.check(fig)["colour-separation"]
    assert measurement.status == "fail"
    assert "decision record 0003" in measurement.detail


def test_close_colours_warn_between_fail_line_and_target(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1], color="#333a80")
    ax.plot([0, 1], [1, 0], color="#4c5596")
    measurement = vf.check(fig)["colour-separation"]
    assert 8 <= measurement.value < 10, measurement
    assert measurement.status == "warn"
    assert vf.check(fig).ok  # warnings are not failures


def test_one_colour_is_skipped(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    assert vf.check(fig)["colour-separation"].status == "skip"


def test_colormapped_artists_are_not_series(house):
    fig = make_figure()
    ax = fig.add_subplot()
    points = ax.scatter(np.arange(50), np.arange(50), c=np.arange(50), cmap="vf.termeh")
    fig.colorbar(points)
    ax.imshow(np.random.default_rng(1).random((5, 5)))
    assert series_colours(fig) == []


def test_series_colours_cover_lines_bars_fills_and_scatter(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1], color="#333a80")
    ax.plot([0, 1], [1, 0], linestyle="none", marker="o", color="#d96e4c")
    ax.bar([0, 1], [1, 2], color="#598fb6")
    ax.fill_between([0, 1], [0, 0], [1, 1], color="#603d34", alpha=0.5)
    ax.scatter([0, 1], [0, 1], color="#b0472c")
    found = series_colours(fig)
    for colour in ("#333a80", "#d96e4c", "#598fb6", "#b0472c"):
        assert colour in found
    assert "#b09e9a" in found  # #603d34 at 50 % on white
    assert "#603d34" not in found


def test_many_colours_warn_instead_of_measuring(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.scatter(np.arange(20), np.arange(20), color=[(i / 20, 0.2, 0.5) for i in range(20)])
    measurement = vf.check(fig)["colour-separation"]
    assert measurement.status == "warn"
    assert measurement.value is None


def test_strict_raises(house):
    fig = clean_figure()
    fig.axes[0].text(0.5, 0.5, "tiny", fontsize=4)
    with pytest.raises(vf.FigureCheckError) as error:
        vf.check(fig, strict=True)
    assert error.value.report["text-size"].status == "fail"
    vf.check(clean_figure(), strict=True)


def test_report_text_is_ascii(house):
    report = vf.check(clean_figure())
    str(report).encode("ascii")
    assert str(report).startswith("vf.check: 0 failed")
    assert len(report.failures) == 0 and len(report.warnings) == 0
    with pytest.raises(KeyError):
        report["colour"]


def test_report_is_ascii_with_minus_signs_and_symbols(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([-2, 2], [-1, 1])
    ax.set_xlabel("Temperature (\u00b0C)")
    ax.text(0.1, 0.1, "\u03b1 = 0.5", fontsize=5)
    report = vf.check(fig)
    str(report).encode("ascii")
    assert "'\\u03b1 = 0.5'" in report["text-size"].detail


def test_empty_figure_is_skipped():
    report = vf.check(make_figure())
    assert report["text-size"].status == "skip"
    assert report["line-width"].status == "skip"
    assert report.ok


def test_only_figures_are_accepted():
    with pytest.raises(TypeError, match="Figure"):
        vf.check(None)
