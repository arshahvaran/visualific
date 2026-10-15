from datetime import date

import pytest

import visualific as vf


def test_presets_match_the_publishers_pages():
    expected = {
        "elsevier-single": 90,
        "elsevier-onehalf": 140,
        "elsevier-double": 190,
        "nature-single": 89,
        "nature-double": 183,
    }
    assert {name: w.mm for name, w in vf.WIDTHS.items()} == expected


@pytest.mark.parametrize("name", sorted(vf.WIDTHS))
def test_every_preset_has_a_source_and_access_date(name):
    width = vf.WIDTHS[name]
    assert width.name == name
    assert width.source.startswith("https://")
    assert date.fromisoformat(width.accessed) <= date(2026, 10, 15)
    assert width.publisher.lower() in width.source


def test_nature_presets_are_widths_only():
    for name in ("nature-single", "nature-double"):
        assert "Width only" in vf.WIDTHS[name].note


def test_figsize_from_preset_uses_house_proportions():
    w, h = vf.figsize("elsevier-single")
    assert w * 25.4 == pytest.approx(90)
    assert h * 25.4 == pytest.approx(65)


def test_figsize_with_height_and_aspect():
    assert vf.figsize(140, 80) == pytest.approx((140 / 25.4, 80 / 25.4))
    assert vf.figsize("elsevier-double", aspect=0.5) == pytest.approx((190 / 25.4, 95 / 25.4))
    assert vf.figsize() == pytest.approx((90 / 25.4, 65 / 25.4))


def test_preset_inches():
    assert vf.WIDTHS["nature-double"].inches == pytest.approx(183 / 25.4)


@pytest.mark.parametrize(
    ("args", "kwargs", "message"),
    [
        (("a4",), {}, "Unknown width"),
        ((-5,), {}, "positive"),
        ((90, 60), {"aspect": 0.5}, "not both"),
        ((90, 0), {}, "positive"),
    ],
)
def test_figsize_rejects_bad_input(args, kwargs, message):
    with pytest.raises(ValueError, match=message):
        vf.figsize(*args, **kwargs)


def test_width_mm():
    assert vf.width_mm("nature-single") == 89
    assert vf.width_mm(120) == 120.0
