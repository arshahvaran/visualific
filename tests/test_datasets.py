"""Tests for the synthetic gallery data in vf.datasets."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from visualific import datasets
from visualific.datasets import _generate, _meta

SHAPES = {
    "lakes_daily": (21912, 27),
    "lake_predictions": (13705, 8),
    "lake_annual": (15400, 8),
    "lake_inventory": (12046, 33),
}
PKG_DIR = Path(datasets.__file__).parent
ARCHIVE = PKG_DIR / "data" / _meta.ARCHIVE
LOADERS = {name: getattr(datasets, f"load_{name}") for name in datasets.list_datasets()}
#: Faithfulness of TRUE_DAG is checked on one lake only, and only for the buoy
#: chemistry nodes; lagged snowpack and heat storage are not in the same-day graph.
DAG_TEST_SITE = "L01"


@pytest.fixture(scope="module")
def tables():
    return {name: load() for name, load in LOADERS.items()}


@pytest.mark.parametrize("name", list(LOADERS))
def test_columns_and_dtypes_match_metadata(tables, name):
    df = tables[name]
    meta = datasets.describe(name)
    assert list(df.columns) == list(meta.column)
    for col, dtype in zip(meta.column, meta.dtype, strict=True):
        if dtype == "string":
            assert isinstance(df[col].dtype, pd.StringDtype), (col, df[col].dtype)
        else:
            assert str(df[col].dtype) == dtype, (col, df[col].dtype, dtype)
    assert df.attrs == {"synthetic": True, "seed": 2026, "version": "1"}


@pytest.mark.parametrize("name", list(SHAPES))
def test_shapes(tables, name):
    assert tables[name].shape == SHAPES[name]


def test_inventory_shape_and_roles(tables):
    inv = tables["lake_inventory"]
    assert len(inv) > 11000
    assert inv.lake_id.is_unique
    counts = inv.role.value_counts()
    assert counts["monitored"] == 12
    assert counts["partner"] == 96
    assert set(inv.loc[inv.role.eq("monitored"), "lake_id"]) == {f"L{i:02d}" for i in range(1, 13)}


def test_values_in_plausible_ranges(tables):
    d = tables["lakes_daily"]
    assert d.date.min() == pd.Timestamp("2019-01-01")
    assert d.date.max() == pd.Timestamp("2023-12-31")
    bounds = {
        "airt_c": (-50, 40),
        "precip_mm": (0, 200),
        "q_m3s": (0, 500),
        "tw_c": (0, 30),
        "do_mgL": (0, 20),
        "ph": (5.5, 10),
        "sc_uScm": (10, 2000),
        "tu_fnu": (0.1, 400),
        "chla_ugL": (0, 500),
        "wqi": (0, 100),
        "tp_ugL": (0, 1000),
    }
    for col, (lo, hi) in bounds.items():
        s = d[col].dropna()
        assert s.between(lo, hi).all(), (col, s.min(), s.max())
    inv = tables["lake_inventory"]
    assert inv.lat.between(-90, 90).all() and inv.lon.between(-180, 180).all()
    assert inv.bloom_likelihood.between(0, 1).all()
    ann = tables["lake_annual"]
    assert ann.year.between(1980, 2023).all()
    assert ann.loc[~ann.surveyed, "bloom"].isna().all()


def test_describe_and_list():
    assert datasets.list_datasets() == list(_meta.COLUMNS)
    desc = datasets.describe("lakes_daily")
    assert list(desc.columns) == ["column", "unit", "dtype", "description"]
    assert desc.description.str.len().gt(0).all()
    with pytest.raises(ValueError, match="unknown dataset"):
        datasets.describe("nope")
    with pytest.raises(ValueError, match="source"):
        datasets.load_lakes_daily(source="web")


def test_archive_is_small_sorted_and_deterministic():
    assert ARCHIVE.stat().st_size < 2_000_000
    with zipfile.ZipFile(ARCHIVE) as zf:
        names = zf.namelist()
        assert names == sorted(names)
        assert {i.date_time for i in zf.infolist()} == {(1980, 1, 1, 0, 0, 0)}
        for name in names:
            assert b"\r\n" not in zf.read(name)


def _numpy_matches_snapshot() -> bool:
    return ".".join(np.__version__.split(".")[:2]) == _meta.NUMPY_VERSION


@pytest.mark.skipif(
    not _numpy_matches_snapshot(),
    reason=f"snapshot was made with NumPy {_meta.NUMPY_VERSION}; other versions may "
    "draw different random streams",
)
@pytest.mark.parametrize("name", list(LOADERS))
def test_regeneration_matches_snapshot(tables, name):
    regenerated = LOADERS[name](source="generate")
    pd.testing.assert_frame_equal(regenerated, tables[name], check_exact=False, rtol=1e-9)


def test_place_names_are_fictional(tables):
    inv = tables["lake_inventory"]
    partners = inv[inv.role.eq("partner")]
    assert partners.district.astype(str).str.fullmatch(r"Partner cluster [A-N]").all()
    assert partners.lake_name.str.fullmatch(r"Partner cluster [A-N], lake \d+").all()
    assert set(partners.country) == {"ZZ"}
    others = set(inv.loc[inv.role.ne("partner"), "district"].astype(str))
    assert others <= set(_generate.DISTRICTS.district)
    assert set(inv.loc[inv.role.eq("monitored"), "lake_name"]) == set(_generate.MONITORED.lake_name)


def test_monitored_lakes_have_the_right_country(tables):
    inv = tables["lake_inventory"]
    mon = inv[inv.role.eq("monitored")].set_index("lake_id")
    assert set(mon.loc[mon.lat.gt(49), "country"]) == {"CA"}
    assert mon.loc["L04", "country"] == "US"


def test_inventory_classes_follow_their_rules(tables):
    inv = tables["lake_inventory"]
    expected = pd.cut(
        inv.tp_ugL,
        [0, 10, 35, 100, np.inf],
        labels=["Oligotrophic", "Mesotrophic", "Eutrophic", "Hypereutrophic"],
        right=False,
    ).astype(str)
    assert (inv.trophic_class.astype(str) == expected).all()
    rule = (inv.bloom_likelihood > 0.30) & (inv.depth_mean_m < 8)
    assert (inv.vulnerable == rule).all()


@pytest.mark.parametrize("name", list(LOADERS))
def test_category_levels_are_fixed(tables, name):
    levels = _meta.categories()[name]
    df = tables[name]
    cats = [c for c in df.columns if isinstance(df[c].dtype, pd.CategoricalDtype)]
    assert sorted(cats) == sorted(levels)
    for c in cats:
        assert list(df[c].cat.categories) == levels[c], c
        assert df[c].cat.ordered == (c in _meta.ORDERED), c


def test_model_and_target_order(tables):
    pred = tables["lake_predictions"]
    assert list(pred.model.cat.categories) == ["ANN", "SVR", "RF", "KAN", "XGBoost"]
    assert list(pred.target.cat.categories) == ["Turbidity", "TN", "TP", "DO"]


def test_prediction_units_match_metadata(tables):
    pred = tables["lake_predictions"]
    for target, (col, *_) in _generate.TARGETS.items():
        units = pred.loc[pred.target.eq(target), "unit"].astype(str).unique()
        assert list(units) == [_meta.COLUMNS["lakes_daily"][col][0]], target


def test_predictions_are_positive(tables):
    assert (tables["lake_predictions"].predicted > 0).all()


def test_inventory_lakes_are_not_in_the_great_lakes(tables):
    inv = tables["lake_inventory"]
    pts = inv[inv.role.eq("inventory")]
    assert not _generate.in_water(pts.lat, pts.lon).any()


def test_daily_precipitation_matches_the_inventory_climate(tables):
    d = tables["lakes_daily"]
    annual = d.groupby(["site_id", "year"], observed=True).precip_mm.sum()
    annual = annual.groupby("site_id", observed=True).mean()
    district = _generate.MONITORED.set_index("site_id").district
    expected = district.map(_generate.DISTRICTS.set_index("district").precip)
    ratio = annual / expected.reindex(annual.index.astype(str)).to_numpy()
    assert ratio.between(0.8, 1.25).all(), ratio


def test_gallery_counts(tables):
    """Pin the numbers that the template spec cards quote."""
    pred = tables["lake_predictions"]
    size = pred.groupby(["target", "model"], observed=True).size().unstack()
    assert (size.loc["Turbidity"] == 1757).all()
    turb = pred[pred.target.eq("Turbidity")]
    dates = [set(g.date) for _, g in turb.groupby("model", observed=True)]
    assert all(s == dates[0] for s in dates)
    test = pred[pred.split.eq("test")]
    assert set(test.date.dt.year) == {2023}
    tsize = test.groupby(["target", "model"], observed=True).size().unstack()
    assert (tsize.loc["TN"] == 66).all() and (tsize.loc["TP"] == 66).all()
    assert (tsize.loc["DO"] == 64).all()

    def nse(g):
        return (
            1
            - ((g.observed - g.predicted) ** 2).sum()
            / ((g.observed - g.observed.mean()) ** 2).sum()
        )

    scores = pred.groupby(["target", "model"], observed=True)[["observed", "predicted"]]
    scores = scores.apply(nse).unstack()
    ranges = {"Turbidity": (0.63, 0.92), "TN": (0.56, 0.87), "TP": (0.49, 0.85), "DO": (0.75, 0.91)}
    for target, (lo, hi) in ranges.items():
        assert scores.loc[target].between(lo, hi).all(), (target, scores.loc[target])
    daily = tables["lakes_daily"]
    sensors = daily.sat_sensor.value_counts(sort=False).to_dict()
    assert sensors == {"Landsat 7": 233, "Landsat 8": 383, "Landsat 9": 176, "Sentinel-2": 1015}
    assert daily.tn_ugL.notna().sum() == 331
    inv = tables["lake_inventory"]
    flags = inv[list(_generate.FLAG_PREV)].mean().round(2).tolist()
    assert flags == [0.98, 0.20, 0.30, 0.27, 0.02]


@pytest.mark.parametrize("name", list(LOADERS))
def test_generate_matches_schema_on_any_numpy(tables, name):
    gen = LOADERS[name](source="generate")
    ref = tables[name]
    assert list(gen.columns) == list(ref.columns)
    assert (gen.dtypes.astype(str) == ref.dtypes.astype(str)).all()
    if name in ("lakes_daily", "lake_annual"):
        assert gen.shape == ref.shape
    num = gen.select_dtypes("number").columns
    assert np.allclose(gen[num].median(), ref[num].median(), rtol=0.2, equal_nan=True)


def test_vf_datasets_is_importable_in_a_fresh_process():
    code = "import visualific as vf; vf.datasets.load_lakes_daily"
    subprocess.run([sys.executable, "-c", code], check=True)


def _std_ols(y, x):
    y = (y - y.mean()) / y.std()
    x = (x - x.mean(axis=0)) / x.std(axis=0)
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(y)), x]), y, rcond=None)
    return beta[1:]


@pytest.fixture(scope="module")
def l01():
    d = datasets.load_lakes_daily()
    d = d[d.site_id.eq(DAG_TEST_SITE)].copy()
    d["ice_cover"] = d.ice_cover.astype(float)
    # Log scale for the right-skewed variables, as the generator builds them
    for c in ["q_m3s", "chla_ugL", "tu_fnu", "sc_uScm"]:
        d[c] = np.log(d[c])
    return d


def test_true_dag_parents_have_clear_effects(l01):
    nodes = {n for edge in _generate.TRUE_DAG for n in edge}
    assert nodes <= set(l01.columns)
    for child in sorted(nodes):
        parents = [p for p, c in _generate.TRUE_DAG if c == child]
        if not parents:
            continue
        sub = l01[[child, *parents]].dropna()
        beta = _std_ols(sub[child].to_numpy(), sub[parents].to_numpy())
        for parent, b in zip(parents, beta, strict=True):
            assert abs(b) > 0.05, (parent, child, b)


def _descendants(node):
    out, stack = set(), [node]
    while stack:
        n = stack.pop()
        for p, c in _generate.TRUE_DAG:
            if p == n and c not in out:
                out.add(c)
                stack.append(c)
    return out


@pytest.mark.parametrize("child", ["ph", "tu_fnu", "chla_ugL", "do_mgL", "sc_uScm"])
def test_no_strong_undeclared_dependence(l01, child):
    """Residuals on the declared parents are nearly uncorrelated with non-descendants."""
    nodes = {n for edge in _generate.TRUE_DAG for n in edge}
    parents = [p for p, c in _generate.TRUE_DAG if c == child]
    others = sorted(nodes - set(parents) - _descendants(child) - {child})
    sub = l01[[child, *parents, *others]].dropna()
    y = (sub[child] - sub[child].mean()) / sub[child].std()
    x = sub[parents].to_numpy()
    x = (x - x.mean(axis=0)) / x.std(axis=0)
    design = np.column_stack([np.ones(len(y)), x])
    beta, *_ = np.linalg.lstsq(design, y.to_numpy(), rcond=None)
    resid = y.to_numpy() - design @ beta
    for other in others:
        r = np.corrcoef(resid, sub[other].to_numpy())[0, 1]
        assert abs(r) < 0.15, (child, other, r)


@pytest.mark.parametrize(
    ("parent", "child"),
    [
        ("tw_c", "ph"),
        ("precip_mm", "tu_fnu"),
        ("ice_cover", "chla_ugL"),
        ("ice_cover", "do_mgL"),
        ("ice_cover", "sc_uScm"),
        ("airt_c", "ice_cover"),
    ],
)
def test_previously_missing_edges_are_declared(parent, child):
    assert (parent, child) in _generate.TRUE_DAG


def test_true_dag_is_acyclic():
    edges = list(_generate.TRUE_DAG)
    nodes = {n for e in edges for n in e}
    indeg = {n: 0 for n in nodes}
    for _, c in edges:
        indeg[c] += 1
    ready = [n for n, k in indeg.items() if k == 0]
    seen = 0
    while ready:
        n = ready.pop()
        seen += 1
        for p, c in edges:
            if p == n:
                indeg[c] -= 1
                if indeg[c] == 0:
                    ready.append(c)
    assert seen == len(nodes)
