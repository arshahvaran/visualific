import numpy as np
import pytest

from visualific import _colour

# Test pairs from Sharma, Wu and Dalal (2005), Table 1 (a subset).
SHARMA = [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
    ((50.0, -1.3802, -84.2814), (50.0, 0.0, -82.7485), 1.0000),
    ((50.0, 2.49, -0.001), (50.0, -2.49, 0.0009), 7.1792),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((22.7233, 20.0904, -46.6940), (23.0331, 14.9730, -42.5619), 2.0373),
    ((90.9257, -0.5406, -0.9208), (88.6381, -0.8985, -0.7239), 1.5381),
]


@pytest.mark.parametrize(("lab1", "lab2", "expected"), SHARMA)
def test_ciede2000_matches_sharma_2005(lab1, lab2, expected):
    assert float(_colour.delta_e2000(lab1, lab2)) == pytest.approx(expected, abs=1e-4)
    assert float(_colour.delta_e2000(lab2, lab1)) == pytest.approx(expected, abs=1e-4)


def test_ciede2000_vectorised():
    first = np.array([p[0] for p in SHARMA])
    second = np.array([p[1] for p in SHARMA])
    expected = [p[2] for p in SHARMA]
    assert _colour.delta_e2000(first, second) == pytest.approx(expected, abs=1e-4)


def test_identical_colours_differ_by_zero():
    for vision in (*_colour.VISIONS, "greyscale"):
        assert _colour.difference("#598fb6", "#598fb6", vision) == pytest.approx(0, abs=1e-9)


def test_white_lab_and_round_trip():
    assert _colour.lab("#ffffff")[0] == pytest.approx([100, 0, 0], abs=1e-3)
    colours = ["#333a80", "#d96e4c", "#808080", "#07187b"]
    back = _colour.lab_to_srgb(_colour.lab(colours))
    assert back == pytest.approx(_colour.to_srgb(colours), abs=1e-6)


@pytest.mark.parametrize("vision", ["protan", "deutan", "tritan"])
def test_machado_keeps_white_and_black(vision):
    assert _colour.simulate("#ffffff", vision)[0] == pytest.approx([1, 1, 1], abs=1e-5)
    assert _colour.simulate("#000000", vision)[0] == pytest.approx([0, 0, 0], abs=1e-12)


def test_unknown_vision_is_refused():
    with pytest.raises(ValueError, match="Unknown vision"):
        _colour.simulate("#ffffff", "achromat")


def test_greyscale_keeps_luminance_only():
    grey = _colour.simulate("#d96e4c", "greyscale")[0]
    assert grey[0] == grey[1] == grey[2]
    assert _colour.linear_to_lab(grey)[0] == pytest.approx(_colour.lightness("#d96e4c"), abs=0.01)


def test_wcag_contrast():
    assert _colour.contrast_ratio("#000000") == pytest.approx(21)
    assert _colour.contrast_ratio("#ffffff") == pytest.approx(1)
    assert _colour.contrast_ratio("#808080") == pytest.approx(3.95, abs=0.01)


def test_separation_needs_two_colours():
    with pytest.raises(ValueError):
        _colour.separation(["#333a80"])


def test_separation_reports_the_closest_pair():
    result = _colour.separation(["#00b945", "#ff9500", "#0c5da5"])
    assert result.colours == ("#00b945", "#ff9500")
    assert result.vision == "protan"
    assert "protan" in str(result)
