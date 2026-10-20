"""Synthetic gallery data: four tidy tables from one seeded generator.

All values are synthetic and describe a fictional lake observatory. The package
ships a frozen snapshot of the generator output in ``data/visualific_synthetic.zip``;
``source="generate"`` rebuilds the tables from the generator instead.

``TRUE_DAG`` is the generator's structural graph for same-day values. Snowpack and
heat storage act with lags, so ``q_m3s``, ``level_m``, ``ice_cover`` and ``tw_c`` keep
residual dependence on past air temperature that the graph does not show. Use one
lake at a time for conditional-independence demos.
"""

from __future__ import annotations

import functools
import io
import zipfile
from importlib import resources
from typing import Literal

import pandas as pd

from . import _generate, _meta
from ._generate import TRUE_DAG

Source = Literal["bundled", "generate"]

__all__ = [
    "TRUE_DAG",
    "describe",
    "list_datasets",
    "load_lake_annual",
    "load_lake_inventory",
    "load_lake_predictions",
    "load_lakes_daily",
]

_NAMES = tuple(_meta.COLUMNS)
_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
_CATEGORIES = _meta.categories()


def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


@functools.cache
def _generated_csv() -> dict[str, bytes]:
    daily = _generate.make_lakes_daily(_meta.SEED)
    inventory = _generate.make_lake_inventory(_meta.SEED)
    tables = {
        "lakes_daily": daily,
        "lake_predictions": _generate.make_lake_predictions(daily, _meta.SEED),
        "lake_inventory": inventory,
        "lake_annual": _generate.make_lake_annual(inventory, _meta.SEED),
    }
    return {name: _to_csv_bytes(df) for name, df in tables.items()}


def _write_archive(path) -> None:
    """Write the four generated tables to a reproducible zip.

    The zip is byte-identical for the same zlib build; the CSV members are
    identical everywhere.
    """
    with zipfile.ZipFile(path, "w") as zf:
        for name in sorted(_NAMES):
            info = zipfile.ZipInfo(f"{name}.csv", date_time=_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, _generated_csv()[name], compresslevel=9)


@functools.cache
def _bundled_csv(name: str) -> bytes:
    ref = resources.files(__name__).joinpath("data", _meta.ARCHIVE)
    with ref.open("rb") as fh, zipfile.ZipFile(io.BytesIO(fh.read())) as zf:
        return zf.read(f"{name}.csv")


def _parse(name: str, raw: bytes) -> pd.DataFrame:
    cols = _meta.COLUMNS[name]
    dtypes = {c: d for c, (_, d, _) in cols.items() if d in ("string", "Int8", "float64")}
    df = pd.read_csv(io.BytesIO(raw), dtype=dtypes, keep_default_na=True)
    for c, (_, d, _) in cols.items():
        if d == "datetime64[ns]":
            df[c] = pd.to_datetime(df[c], format="%Y-%m-%d").astype("datetime64[ns]")
        elif d == "category":
            levels = _CATEGORIES[name][c]
            cat = pd.Categorical(df[c], categories=levels, ordered=c in _meta.ORDERED)
            lost = df[c].notna() & pd.isna(cat)
            if lost.any():
                raise ValueError(f"unexpected values in {name}.{c}: {sorted(set(df[c][lost]))}")
            df[c] = cat
        elif d == "bool":
            if df[c].isna().any():
                raise ValueError(f"missing values in bool column {name}.{c}")
            df[c] = df[c].astype(bool)
    df = df[list(cols)]
    df.attrs = {"synthetic": True, "seed": _meta.SEED, "version": _meta.VERSION}
    return df


def _load(name: str, source: str) -> pd.DataFrame:
    if source == "bundled":
        raw = _bundled_csv(name)
    elif source == "generate":
        raw = _generated_csv()[name]
    else:
        raise ValueError(f"source must be 'bundled' or 'generate', not {source!r}")
    return _parse(name, raw)


_RETURNS = """
    Parameters
    ----------
    source : {"bundled", "generate"}, default "bundled"
        ``"bundled"`` reads the snapshot shipped with the package. ``"generate"``
        runs the seeded generator; with a different NumPy version the values
        may differ slightly from the snapshot.

    Returns
    -------
    pandas.DataFrame
        Dates are parsed; identifiers and lake names are strings, and other
        text columns are categorical with a fixed level order.
        ``df.attrs`` holds ``{"synthetic": True, "seed": 2026, "version": "1"}``.

    Raises
    ------
    ValueError
        If ``source`` is not ``"bundled"`` or ``"generate"``.

    See Also
    --------
    describe : Units, dtypes and a description of every column.
"""


def load_lakes_daily(source: Source = "bundled") -> pd.DataFrame:
    return _load("lakes_daily", source)


def load_lake_predictions(source: Source = "bundled") -> pd.DataFrame:
    return _load("lake_predictions", source)


def load_lake_inventory(source: Source = "bundled") -> pd.DataFrame:
    return _load("lake_inventory", source)


def load_lake_annual(source: Source = "bundled") -> pd.DataFrame:
    return _load("lake_annual", source)


load_lakes_daily.__doc__ = (
    "Load the daily records of the twelve monitored lakes (main table).\n\n"
    "    One row per lake and day, 2019 to 2023. Buoy, gauge, satellite and\n"
    "    monthly lab columns have realistic gaps.\n" + _RETURNS
)
load_lake_predictions.__doc__ = (
    "Load observed and predicted values from five models, in long form.\n\n"
    "    One row per lake, date, target and model.\n" + _RETURNS
)
load_lake_inventory.__doc__ = (
    "Load the inventory of fictional lakes with coordinates and covariates.\n\n"
    "    One row per lake, including the twelve monitored lakes and 96 lakes in\n"
    "    fictional partner clusters.\n" + _RETURNS
)
load_lake_annual.__doc__ = (
    "Load the lake-year panel, 1980 to 2023.\n\n"
    "    One row per lake and year for 50 inventory lakes in each of seven districts.\n" + _RETURNS
)


def list_datasets() -> list[str]:
    """Return the names of the synthetic tables.

    Returns
    -------
    list of str
        Names accepted by :func:`describe`.
    """
    return list(_NAMES)


def describe(name: str) -> pd.DataFrame:
    """Describe the columns of one synthetic table.

    Parameters
    ----------
    name : str
        One of the names from :func:`list_datasets`.

    Returns
    -------
    pandas.DataFrame
        One row per column with ``column``, ``unit``, ``dtype`` and ``description``.
        ``df.attrs["description"]`` describes the table itself.

    Raises
    ------
    ValueError
        If ``name`` is not one of the synthetic tables.
    """
    if name not in _meta.COLUMNS:
        raise ValueError(f"unknown dataset {name!r}; choose from {list(_NAMES)}")
    rows = [(c, u, d, t) for c, (u, d, t) in _meta.COLUMNS[name].items()]
    df = pd.DataFrame(rows, columns=["column", "unit", "dtype", "description"])
    df.attrs = {"description": _meta.DESCRIPTIONS[name]}
    return df
