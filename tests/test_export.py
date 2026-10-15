import re

import matplotlib as mpl
import pytest
from conftest import clean_figure, make_figure
from PIL import Image

import visualific as vf
from visualific._export import measure_width_mm


def pdf_fonts(data: bytes):
    names = set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-_,]+)", data))
    subtypes = set(
        re.findall(rb"/Subtype\s*/(Type1|Type3|TrueType|CIDFontType0|CIDFontType2)", data)
    )
    return names, subtypes


def test_default_save_writes_pdf_and_600_dpi_png(tmp_path, house):
    fig = clean_figure()
    written = vf.save(fig, tmp_path / "fig1", width="elsevier-single")
    assert [p.name for p in written] == ["fig1.pdf", "fig1.png"]
    assert measure_width_mm(written[0], "pdf", 600) == pytest.approx(90, abs=1e-6)
    with Image.open(written[1]) as png:
        assert png.size[0] / 600 * 25.4 == pytest.approx(90, abs=0.5)
        assert png.info["dpi"][0] == pytest.approx(600, abs=0.01)


def test_pdf_embeds_truetype_fonts_only(tmp_path, house):
    (pdf,) = vf.save(clean_figure(), tmp_path / "fig1.pdf")
    names, subtypes = pdf_fonts(pdf.read_bytes())
    assert b"Type3" not in subtypes
    assert b"CIDFontType2" in subtypes
    assert any(b"TimesNewRoman" in n or b"LiberationSerif" in n for n in names), names


def test_pdf_with_bundled_font(tmp_path):
    with vf.style(font="Liberation Serif"):
        (pdf,) = vf.save(clean_figure(), tmp_path / "fig1.pdf")
    names, _ = pdf_fonts(pdf.read_bytes())
    assert any(b"LiberationSerif" in n for n in names)
    assert not any(b"TimesNewRoman" in n for n in names)


@pytest.mark.parametrize(
    ("content", "dpi"), [("line", 1000), ("combination", 500), ("halftone", 300)]
)
def test_tiff_resolution_by_content(tmp_path, house, content, dpi):
    assert vf.TIFF_DPI[content] == dpi
    fig = make_figure(width=40, height=25)
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    ax.set_axis_off()
    (tif,) = vf.save(fig, tmp_path / "fig1.tif", content=content)
    with Image.open(tif) as image:
        assert image.info["dpi"][0] == pytest.approx(dpi, abs=0.01)
        assert image.size[0] / dpi * 25.4 == pytest.approx(40, abs=0.5)


def test_suffix_selects_one_format(tmp_path, house):
    written = vf.save(clean_figure(), tmp_path / "only.png")
    assert [p.name for p in written] == ["only.png"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["only.png"]


def test_svg_text_is_paths(tmp_path, house):
    (svg,) = vf.save(clean_figure(), tmp_path / "fig.svg")
    data = svg.read_bytes()
    assert b"<text" not in data
    assert measure_width_mm(svg, "svg", 600) == pytest.approx(90, abs=1e-6)


def test_folders_are_created(tmp_path, house):
    (pdf,) = vf.save(clean_figure(), tmp_path / "a" / "b" / "fig.pdf")
    assert pdf.exists()


def test_jpeg_is_refused(tmp_path, house):
    with pytest.raises(ValueError, match="JPEG"):
        vf.save(clean_figure(), tmp_path / "fig.jpg")


def test_wrong_declared_width_saves_nothing(tmp_path, house):
    with pytest.raises(ValueError, match="declared 190 mm"):
        vf.save(clean_figure("elsevier-single"), tmp_path / "fig", width="elsevier-double")
    assert list(tmp_path.iterdir()) == []


def test_half_millimetre_tolerance(tmp_path, house):
    fig = make_figure(width=90.4)
    fig.add_subplot().plot([0, 1], [0, 1])
    assert vf.save(fig, tmp_path / "fig.pdf", width=90)


def test_tight_bbox_setting_is_ignored(tmp_path, house):
    fig = clean_figure()
    fig.text(0.99, 0.5, "label running past the right edge")
    mpl.rcParams["savefig.bbox"] = "tight"
    (pdf,) = vf.save(fig, tmp_path / "fig.pdf", width="elsevier-single")
    assert measure_width_mm(pdf, "pdf", 600) == pytest.approx(90, abs=1e-6)


def test_save_without_house_style_still_uses_truetype(tmp_path):
    fig = make_figure()
    fig.add_subplot().plot([0, 1], [0, 1])
    (pdf,) = vf.save(fig, tmp_path / "fig.pdf")
    assert b"Type3" not in pdf_fonts(pdf.read_bytes())[1]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"formats": ("pdf", "eps")}, ValueError, "Unknown formats"),
        ({"formats": ()}, ValueError, "formats is empty"),
        ({"formats": "pdf"}, TypeError, "sequence"),
        ({"content": "photo"}, ValueError, "content"),
    ],
)
def test_bad_arguments(tmp_path, house, kwargs, error, message):
    with pytest.raises(error, match=message):
        vf.save(clean_figure(), tmp_path / "fig", **kwargs)


def test_suffix_and_formats_together_are_refused(tmp_path, house):
    with pytest.raises(ValueError, match="not both"):
        vf.save(clean_figure(), tmp_path / "fig.pdf", formats=("png",))


def test_only_figures_are_accepted(tmp_path):
    with pytest.raises(TypeError, match="Figure"):
        vf.save("not a figure", tmp_path / "fig")
