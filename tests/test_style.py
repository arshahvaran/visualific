import hashlib
from pathlib import Path

import matplotlib as mpl
import pytest
from conftest import make_figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser

import visualific as vf
from visualific import _fonts, _scripts

ROOT = Path(__file__).resolve().parents[1]

# SHA-256 of the files in liberation-fonts-ttf-2.1.5.tar.gz, the official
# release at https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5
LIBERATION_2_1_5 = {
    "LiberationSerif-Regular.ttf": (
        "058ea80864aef09a23f45cbec2bb5400bc3dfbdea01c3f10538a21fcb497fb74"
    ),
    "LiberationSerif-Bold.ttf": "d754ba427cfe0bca54ae052384baa8f842da5bd6550ad4da024ac441e7a7d5ce",
    "LiberationSerif-Italic.ttf": (
        "0e3dea9f8d613e006ccfa62201f33e265d19167bd0907725c3e145368b04fc2e"
    ),
    "LiberationSerif-BoldItalic.ttf": (
        "f17db8af71e24d2066b587546021d4f0b296be389512b658dec3c09affeb11a7"
    ),
}


def script_sizes(expression, size):
    """Glyph sizes in pt that mathtext uses for ``expression`` at ``size`` pt."""
    parse = MathTextParser("path").parse(expression, 72, FontProperties(size=size))
    return sorted({round(g[1], 6) for g in parse.glyphs})


# Type scale -----------------------------------------------------------------------------


def test_type_scale_normal_is_8_9_10():
    scale = vf.type_scale()
    assert (scale.tick, scale.label, scale.panel, scale.script_min) == (8, 9, 10, 6)
    rc = vf.rc_params()
    assert rc["xtick.labelsize"] == rc["ytick.labelsize"] == rc["legend.fontsize"] == 8
    assert rc["font.size"] == 8
    assert rc["axes.labelsize"] == rc["axes.titlesize"] == 9


def test_compact_preset_is_one_point_smaller():
    scale = vf.type_scale(compact=True)
    assert (scale.tick, scale.label, scale.panel, scale.script_min) == (7, 8, 9, 6)
    rc = vf.rc_params(compact=True)
    assert rc["xtick.labelsize"] == rc["legend.fontsize"] == 7
    assert rc["axes.labelsize"] == 8


# Lines ------------------------------------------------------------------------------------


def test_line_weights_match_adr_0002():
    assert (vf.LINES.axes, vf.LINES.data, vf.LINES.reference) == (0.6, 1.2, 0.8)
    assert (vf.LINES.edge, vf.LINES.marker_edge, vf.LINES.minimum) == (0.5, 0.4, 0.3)
    rc = vf.rc_params()
    assert rc["axes.linewidth"] == rc["xtick.major.width"] == 0.6
    assert rc["lines.linewidth"] == 1.2
    assert rc["patch.linewidth"] == 0.5
    assert rc["lines.markeredgewidth"] == 0.4


@pytest.mark.parametrize("compact", [False, True])
def test_no_default_line_is_thinner_than_minimum(compact):
    rc = vf.rc_params(compact=compact)
    widths = {k: v for k, v in rc.items() if k.endswith(("width", ".linewidth"))}
    assert widths
    assert all(v >= vf.LINES.minimum for v in widths.values()), widths


# Layout and export --------------------------------------------------------------------------


def test_layout_and_export_settings(house):
    rc = mpl.rcParams
    assert rc["figure.constrained_layout.use"] is True
    assert rc["savefig.bbox"] is None  # never "tight"
    assert rc["savefig.dpi"] == 600
    assert rc["pdf.fonttype"] == 42
    assert rc["svg.fonttype"] == "path"
    assert rc["text.usetex"] is False
    assert rc["mathtext.fontset"] == "stix"
    assert not rc["legend.frameon"]


def test_default_figure_is_90_by_65_mm(house):
    fig = mpl.figure.Figure()
    w, h = fig.get_size_inches() * 25.4
    assert w == pytest.approx(90)
    assert h == pytest.approx(65)


def test_default_cycle_is_vf_qual(house):
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == list(vf.qual)


def test_palette_argument_sets_the_cycle():
    rc = vf.rc_params(palette=vf.science_safe)
    assert rc["axes.prop_cycle"].by_key()["color"] == list(vf.science_safe)


# Fonts ------------------------------------------------------------------------------------


def test_font_chain_ends_in_stix():
    family = vf.rc_params()["font.family"]
    assert family[0] in ("Times New Roman", "Liberation Serif")
    assert family[-1] == "STIXGeneral"


def test_times_new_roman_is_preferred_when_installed():
    expected = "Times New Roman" if _fonts.is_installed("Times New Roman") else "Liberation Serif"
    assert _fonts.resolve_font() == expected


def test_bundled_font_can_be_forced_everywhere():
    assert vf.rc_params(font="Liberation Serif")["font.family"] == [
        "Liberation Serif",
        "STIXGeneral",
    ]


def test_unknown_font_is_refused():
    with pytest.raises(ValueError, match="not installed"):
        vf.rc_params(font="No Such Typeface")


def test_bundled_fonts_are_liberation_2_1_5_unmodified():
    paths = _fonts.bundled_font_paths()
    assert [p.name for p in paths] == list(LIBERATION_2_1_5)
    for path in paths:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == LIBERATION_2_1_5[path.name]


def test_bundled_fonts_ship_with_their_licence():
    # The installed package (the wheel, in CI's build job) must carry the licence.
    shipped = _fonts.bundled_font_paths()[0].with_name("OFL.txt").read_bytes()
    assert shipped == (ROOT / "LICENSES" / "OFL-1.1.txt").read_bytes()
    assert (ROOT / "src" / "visualific" / "fonts" / "OFL.txt").read_bytes() == shipped
    assert b"SIL OPEN FONT LICENSE Version 1.1" in shipped
    assert b"Reserved Font Name Liberation" in shipped


def test_bundled_fonts_register_with_matplotlib():
    _fonts.register_bundled_fonts()
    _fonts.register_bundled_fonts()  # idempotent
    assert _fonts.is_installed("Liberation Serif")
    names = [Path(f.fname).name for f in mpl.font_manager.fontManager.ttflist]
    for name in LIBERATION_2_1_5:
        assert names.count(name) >= 1
    bundled = {p.resolve() for p in _fonts.bundled_font_paths()}
    added = [f for f in mpl.font_manager.fontManager.ttflist if Path(f.fname).resolve() in bundled]
    assert len(added) == len(bundled)  # each bundled file added once


# Styles -------------------------------------------------------------------------------------


def test_use_changes_rcparams_and_style_restores_them():
    before = mpl.rcParams["xtick.labelsize"]
    with vf.style(compact=True):
        assert mpl.rcParams["xtick.labelsize"] == 7
    assert mpl.rcParams["xtick.labelsize"] == before
    vf.use()
    assert mpl.rcParams["xtick.labelsize"] == 8


def test_unknown_style_is_refused():
    with pytest.raises(ValueError, match="Unknown style"):
        vf.use("classic")


def test_science_like_changes_only_ticks_and_colours():
    house = vf.rc_params()
    science = vf.rc_params("science-like")
    changed = {k for k in science if science[k] != house.get(k)}
    assert changed <= {
        "axes.prop_cycle",
        "xtick.direction",
        "ytick.direction",
        "xtick.top",
        "ytick.right",
        "xtick.minor.visible",
        "ytick.minor.visible",
        "xtick.minor.size",
        "ytick.minor.size",
    }
    assert science["xtick.direction"] == science["ytick.direction"] == "in"
    assert science["xtick.top"] and science["ytick.right"]
    assert science["axes.prop_cycle"].by_key()["color"] == list(vf.science_safe)
    # The fixes SciencePlots users get: no LaTeX, no cropping, TrueType fonts.
    assert science["text.usetex"] is False
    assert science["savefig.bbox"] == "standard"
    assert science["pdf.fonttype"] == 42


def test_science_like_applies(house):
    vf.use("science-like")
    assert mpl.rcParams["xtick.direction"] == "in"


# Sub- and superscripts --------------------------------------------------------------------


def test_scripts_are_raised_to_6_pt():
    _scripts.install()
    assert _scripts.is_installed()
    for size in (7, 8):
        sizes = script_sizes(r"$10^{-3}$", size)
        assert min(sizes) == pytest.approx(6.0, abs=1e-6)
        assert max(sizes) == size


def test_larger_text_keeps_matplotlib_script_size():
    _scripts.install()
    for size in (9, 10, 12):
        assert min(script_sizes(r"$10^{-3}$", size)) == pytest.approx(0.7 * size)


def test_second_level_scripts_can_still_be_small():
    _scripts.install()
    assert min(script_sizes(r"$e^{x^{2}}$", 8)) < 6


def test_tick_label_exponents_are_6_pt_in_a_figure(house):
    fig = make_figure()
    ax = fig.add_subplot()
    ax.plot([1, 10, 100, 1000], [1, 2, 3, 4])
    ax.set_xscale("log")
    report = vf.check(fig)
    assert report["text-size"].status == "pass"
    assert report["text-size"].value == pytest.approx(8.0)
    assert report["text-size"].values["script"] == pytest.approx(6.0, abs=1e-3)
