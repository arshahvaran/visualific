"""Seeded generator for the Visualific synthetic gallery data.

All values are synthetic. The storyline is a fictional "Northern Lakes
Observatory": twelve monitored lakes (L01-L12) with gauges, buoys, monthly lab
sampling and satellite overpasses (2019-2023); five competing models that
predict turbidity, TN, TP and DO; an inventory of about 12,000 fictional lakes
plus 96 lakes in 14 fictional partner clusters; and a 44-year lake-year panel.

Tables
  make_lakes_daily()       main table, one row = monitored lake x day
  make_lake_predictions()  one row = lake x date x target x model
  make_lake_inventory()    one row = lake (points with attributes and flags)
  make_lake_annual()       one row = lake x year (1980-2023)

Every table draws from its own child stream of one ``SeedSequence`` and every
monitored lake from its own grandchild stream, so changing one table never
changes another. Only NumPy and pandas are used.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 2026
TEST_YEAR = 2023
STUDY_START, STUDY_END = "2019-01-01", "2023-12-31"
SPINUP_START = "2018-01-01"  # one discarded year for snowpack / reservoir / lag spin-up


def _streams(seed: int = SEED) -> dict[str, np.random.SeedSequence]:
    names = ["daily", "predictions", "inventory", "annual", "hourly"]
    return dict(zip(names, np.random.SeedSequence(seed).spawn(len(names)), strict=True))


# --------------------------------------------------------------------------- #
# Monitored lakes (fixed metadata; the inventory reuses these 12 rows)
# --------------------------------------------------------------------------- #
MONITORED = pd.DataFrame(
    [
        # id, name, lat, lon, area, depth, TP, pH0, SC0, colour, Qb, TU0, winter buoy, district
        (
            "L01",
            "Aldmere",
            46.30,
            -79.60,
            85.0,
            11.0,
            14,
            7.35,
            190,
            30,
            25.0,
            1.0,
            True,
            "Canadian Shield",
        ),
        (
            "L02",
            "Birchmere",
            44.95,
            -78.40,
            12.0,
            9.0,
            8,
            7.10,
            80,
            25,
            3.5,
            0.8,
            False,
            "Canadian Shield",
        ),
        (
            "L03",
            "Cairnmere",
            43.62,
            -80.95,
            6.5,
            9.0,
            48,
            8.05,
            520,
            15,
            2.2,
            4.0,
            True,
            "Great Lakes Lowlands",
        ),
        (
            "L04",
            "Dunmere",
            48.65,
            -93.20,
            40.0,
            8.0,
            11,
            7.20,
            95,
            35,
            9.0,
            1.2,
            False,
            "Upper Midwest",
        ),
        (
            "L05",
            "Edenmere",
            50.20,
            -98.40,
            22.0,
            3.5,
            24,
            8.10,
            430,
            20,
            4.0,
            3.0,
            False,
            "Prairie Potholes",
        ),
        (
            "L06",
            "Fernmere",
            52.90,
            -105.70,
            9.0,
            2.5,
            98,
            8.45,
            610,
            10,
            1.6,
            6.5,
            False,
            "Prairie Potholes",
        ),
        (
            "L07",
            "Gorsemere",
            54.70,
            -112.40,
            35.0,
            6.0,
            19,
            7.90,
            280,
            40,
            6.5,
            2.0,
            False,
            "Boreal Plains",
        ),
        (
            "L08",
            "Heathmere",
            56.10,
            -116.90,
            18.0,
            12.0,
            6,
            7.60,
            210,
            45,
            3.0,
            1.0,
            False,
            "Boreal Plains",
        ),
        ("L09", "Ivymere", 58.80, -111.20, 27.0, 7.0, 12, 7.40, 150, 55, 5.0, 1.5, False, "Taiga"),
        ("L10", "Jaymere", 60.90, -115.30, 60.0, 14.0, 9, 7.25, 120, 50, 9.5, 1.1, False, "Taiga"),
        ("L11", "Kelmere", 62.40, -114.10, 15.0, 10.0, 5, 7.00, 60, 35, 2.5, 0.7, False, "Taiga"),
        ("L12", "Lynmere", 63.50, -112.60, 8.0, 16.0, 4, 6.90, 45, 30, 1.4, 0.6, False, "Taiga"),
    ],
    columns=[
        "site_id",
        "lake_name",
        "lat",
        "lon",
        "area_km2",
        "depth_mean_m",
        "tp_ugL",
        "ph_base",
        "sc_base",
        "colour_base",
        "q_base",
        "tu_base",
        "winter_buoy",
        "district",
    ],
)


# --------------------------------------------------------------------------- #
# Small numerical helpers (plain numpy; loops are short)
# --------------------------------------------------------------------------- #
def _ar1(rng, n, phi, sd):
    """Stationary AR(1) with marginal standard deviation `sd`."""
    e = rng.standard_normal(n) * sd * np.sqrt(1.0 - phi**2)
    x = np.empty(n)
    x[0] = rng.standard_normal() * sd
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def _ewma(x, tau):
    y = np.empty_like(x, dtype=float)
    y[0] = x[0]
    a = 1.0 / tau
    for i in range(1, len(x)):
        y[i] = y[i - 1] + a * (x[i] - y[i - 1])
    return y


def _do_sat(t):
    """Oxygen solubility in fresh water at sea level (mg/L), 0-30 degC polynomial."""
    return 14.652 - 0.41022 * t + 0.007991 * t**2 - 0.000077774 * t**3


def _round_to(x, step):
    """Round to a measurement resolution (e.g. 0.1 FNU, 10 ug/L) without float residue."""
    decimals = max(0, -int(np.floor(np.log10(step))))
    return np.round(np.round(np.asarray(x, float) / step) * step, decimals)


def _wqi(do, tu, chla, ph):
    """Synthetic 0-100 water-quality index (a SINK node in the true DAG)."""
    s_do = np.clip((do - 6.0) / 5.0 * 100, 0, 100)
    s_tu = np.clip(100 - 45 * np.log10(np.maximum(tu, 1.0)), 0, 100)
    s_ch = np.clip(100 - 55 * np.log10(np.maximum(chla, 2.5) / 2.5), 0, 100)
    s_ph = np.clip(
        100 - 30 * np.abs(ph - 7.5) - 120 * np.maximum(0, np.maximum(6.5 - ph, ph - 8.5)), 0, 100
    )
    return 0.30 * s_do + 0.25 * s_tu + 0.30 * s_ch + 0.15 * s_ph


# True causal structure used to generate the buoy / gauge block (exported for the DAG demo).
# TRUE_DAG is the generator's structural graph for same-day values. Snowpack and heat
# storage act with lags, so q_m3s, level_m, ice_cover and tw_c keep residual dependence
# on past air temperature that the graph does not show. Use one lake at a time (L01 in
# the tests) for conditional-independence demos.
TRUE_DAG = (
    ("precip_mm", "q_m3s"),
    ("airt_c", "q_m3s"),  # rain + snowmelt -> outflow
    ("q_m3s", "level_m"),  # rating curve
    ("airt_c", "ice_cover"),  # smoothed air temperature below -1 degC
    ("airt_c", "tw_c"),
    ("ice_cover", "tw_c"),  # lagged heat exchange; near 0 degC under ice
    ("tw_c", "chla_ugL"),
    ("ice_cover", "chla_ugL"),  # temperature-limited growth; dark under ice
    ("tw_c", "do_mgL"),
    ("chla_ugL", "do_mgL"),
    ("ice_cover", "do_mgL"),  # solubility, photosynthesis
    ("chla_ugL", "ph"),
    ("tw_c", "ph"),  # CO2 drawdown; temperature term
    ("q_m3s", "sc_uScm"),
    ("ice_cover", "sc_uScm"),  # dilution; solute exclusion under ice
    ("q_m3s", "tu_fnu"),
    ("chla_ugL", "tu_fnu"),
    ("precip_mm", "tu_fnu"),  # runoff, algae, storms
    ("do_mgL", "orp_mV"),  # redox
    ("do_mgL", "wqi"),
    ("tu_fnu", "wqi"),
    ("chla_ugL", "wqi"),
    ("ph", "wqi"),
)

SENSORS = {  # name: (first day, last day, daily probability of a valid ice-free retrieval)
    "Landsat 7": ("2018-01-01", "2022-04-06", 0.030),
    "Landsat 8": ("2018-01-01", "2023-12-31", 0.035),
    "Landsat 9": ("2022-02-10", "2023-12-31", 0.035),
    "Sentinel-2": ("2018-01-01", "2023-12-31", 0.090),
}

BUOY_COLS = ["tw_c", "do_mgL", "ph", "sc_uScm", "tu_fnu", "chla_ugL", "orp_mV", "wqi"]
LAB_COLS = [
    "tn_ugL",
    "tp_ugL",
    "cod_mgL",
    "colour_mgPtL",
    "tn_hypo_ugL",
    "tp_hypo_ugL",
    "do_hypo_mgL",
]


# --------------------------------------------------------------------------- #
# MASTER TABLE: lakes_daily
# --------------------------------------------------------------------------- #
def _site_daily(rng: np.random.Generator, s: pd.Series) -> pd.DataFrame:
    dates = pd.date_range(SPINUP_START, STUDY_END, freq="D")
    n = len(dates)
    doy = dates.dayofyear.to_numpy()
    yr = dates.year.to_numpy()

    # Meteorology (exogenous roots)
    t_ann, amp = 30.5 - 0.57 * s.lat, 3.0 + 0.28 * s.lat
    airt = t_ann - amp * np.cos(2 * np.pi * (doy - 20) / 365.25) + _ar1(rng, n, 0.70, 3.5)
    wet = rng.random(n) < 0.33
    p_ann = float(DISTRICTS.loc[DISTRICTS.district.eq(s.district), "precip"].iloc[0])
    precip = rng.gamma(0.8, 7.0 * p_ann / 680.0, n) * wet

    # Snowpack + linear reservoir -> outflow Q (right-skewed, spring freshet)
    swe, runoff = 0.0, np.empty(n)
    for i in range(n):
        if airt[i] < 0:
            swe += precip[i]
            runoff[i] = 0.0
        else:
            melt = min(swe, 3.0 * airt[i])
            swe -= melt
            runoff[i] = precip[i] + melt
    store = _ewma(runoff, 14.0)
    q = s.q_base * (0.30 + 0.70 * store / store.mean()) * np.exp(_ar1(rng, n, 0.9, 0.08))
    level = 1.0 + 0.35 * q**0.45 * (s.q_base / 25.0) ** -0.20 + _ar1(rng, n, 0.95, 0.01)

    # Ice and water temperature
    ice = _ewma(airt, 25.0) < -1.0
    tw_true = np.clip(_ewma(airt, 15.0 + 0.5 * s.depth_mean_m) + 2.0, 0.3, 27.0) + _ar1(
        rng, n, 0.8, 0.35
    )
    tw_true = np.where(ice, 0.3 + 0.7 * _ewma(rng.random(n), 10.0), np.clip(tw_true, 0.2, 28.5))

    # Chlorophyll-a (TP-driven baseline, temperature growth, late-summer bloom pulses)
    chla_base = 0.30 * s.tp_ugL**0.95
    log_chla = (
        np.log(chla_base) + 0.04 * (tw_true - 12.0) * ~ice - 1.0 * ice + _ar1(rng, n, 0.85, 0.50)
    )
    if s.tp_ugL > 30:
        for y in np.unique(yr):
            centre, width, height = rng.uniform(200, 245), rng.uniform(8, 16), rng.uniform(0.6, 1.3)
            log_chla += height * np.exp(-0.5 * ((doy - centre) / width) ** 2) * (yr == y)
    chla = np.exp(log_chla)

    # DO, pH, SC, turbidity, ORP (each follows TRUE_DAG parents)
    do = _do_sat(tw_true) * (
        1.0 + 0.08 * np.log(chla / chla_base) + _ar1(rng, n, 0.7, 0.04) - 0.08 * ice
    )
    ph = (
        s.ph_base
        + 0.30 * np.log10(chla / chla_base)
        + 0.008 * (tw_true - 10)
        + _ar1(rng, n, 0.8, 0.10)
    )
    q_rel = q / np.median(q)
    sc = s.sc_base * q_rel**-0.25 * (1 + 0.15 * ice) * np.exp(_ar1(rng, n, 0.9, 0.03))
    impulse = np.where(
        precip > 12, rng.lognormal(0.9, 0.7, n) * precip / 12, 0.0
    )  # storm sediment pulses
    storm = np.zeros(n)
    for i in range(1, n):
        storm[i] = storm[i - 1] * np.exp(-1 / 2.0) + impulse[i]
    log_tu = (
        np.log(s.tu_base)
        + 1.1 * np.log(q_rel)
        + 0.50 * np.log(chla / chla_base)
        + np.log1p(storm)
        + _ar1(rng, n, 0.8, 0.30)
    )
    tu = np.exp(log_tu)
    tu = np.maximum(0.1, tu / (1 + tu / 400))  # soft optical ceiling
    orp = 140 + 9.0 * (do - 9.0) + _ar1(rng, n, 0.9, 10.0)
    wqi = _wqi(do, tu, chla, ph)

    df = pd.DataFrame(
        {
            "site_id": s.site_id,
            "date": dates,
            "airt_c": _round_to(airt, 0.1),
            "precip_mm": _round_to(precip, 0.1),
            "q_m3s": np.round(q, 2),
            "level_m": np.round(level, 3),
            "ice_cover": ice,
            "tw_c": np.round(tw_true, 2),
            "do_mgL": np.round(do, 2),
            "ph": np.round(ph, 2),
            "sc_uScm": np.round(sc, 0),
            "tu_fnu": _round_to(tu, 0.1),
            "chla_ugL": np.round(chla, 2),
            "orp_mV": np.round(orp, 0),
            "wqi": np.round(wqi, 1),
        }
    )

    # Satellite: daily thermal LSWT (cloud gaps, skin effect, 1.5 % cloud-contaminated)
    valid = ~ice & (rng.random(n) < 0.50)
    lswt = tw_true - 0.4 + rng.normal(0, 0.5, n) - (rng.random(n) < 0.015) * rng.uniform(2, 6, n)
    df["lswt_c"] = np.where(valid, np.round(lswt, 2), np.nan)

    # Satellite: high-resolution optical overpass with a valid retrieval (one sensor per day max)
    sensor = np.full(n, None, dtype=object)
    u = rng.random(n)
    acc = np.zeros(n)
    for name, (d0, d1, p) in SENSORS.items():
        live = (dates >= d0) & (dates <= d1) & ~ice
        hit = live & (u >= acc) & (u < acc + p) & pd.isna(sensor)
        sensor[hit] = name
        acc = acc + p * live
    df["sat_sensor"] = sensor

    # Buoy availability: removed under ice unless winter_buoy, plus random outages
    ok = np.ones(n, bool) if s.winter_buoy else ~ice
    for _ in range(rng.poisson(2.5 * 6)):
        start = rng.integers(0, n)
        ok[start : start + rng.geometric(1 / 6)] = False
    df.loc[~ok, BUOY_COLS] = np.nan
    gauge_gap = np.zeros(n, bool)
    for _ in range(rng.poisson(6)):
        start = rng.integers(0, n)
        gauge_gap[start : start + rng.integers(1, 4)] = True
    df.loc[gauge_gap, ["q_m3s", "level_m"]] = np.nan

    # Monthly lab sampling, ice-free May-October (surface + hypolimnion)
    for c in LAB_COLS:
        df[c] = np.nan
    tn_lake = 110 * s.tp_ugL**0.5 + 50
    for y in range(2018, 2024):
        ice_y = ice[yr == y]
        doy_y = doy[yr == y]
        open_after = doy_y[(~ice_y) & (doy_y > 60)]
        ice_off = int(open_after.min()) if len(open_after) else 90
        for m in range(5, 11):
            d = pd.Timestamp(y, m, int(rng.integers(8, 21)))
            i = int((d - dates[0]).days)
            if ice[i]:
                continue
            season = 1 + 0.25 * np.sin(2 * np.pi * (doy[i] - 150) / 365.25)
            tp = s.tp_ugL * season * np.exp(rng.normal(0, 0.30))
            tn = tn_lake * np.exp(rng.normal(0, 0.18))
            colour = s.colour_base * np.exp(rng.normal(0, 0.25))
            cod = max(0.5, 1.5 + 0.08 * colour + rng.normal(0, 0.6))
            if s.depth_mean_m > 6:  # stratified: hypolimnetic O2 depletion since ice-off
                k = np.clip(0.10 + 0.025 * s.tp_ugL, 0.15, 0.97)
                prog = np.clip((doy[i] - ice_off) / 110, 0, 1)
                do_h = 12.5 * (1 - k * prog) + rng.normal(0, 0.6)
            else:  # polymictic: bottom ~ surface
                do_h = (
                    _do_sat(tw_true[i]) - 0.5 - 0.06 * s.tp_ugL * rng.random() + rng.normal(0, 0.5)
                )
            do_h = max(0.2, do_h)
            anox = max(0.0, 3.0 - do_h) / 3.0
            df.loc[i, LAB_COLS] = [
                _round_to(tn, 10),
                _round_to(tp, 0.5 if tp < 20 else 1.0),
                round(cod, 1),
                _round_to(colour, 5),
                _round_to(tn * (1 + 0.4 * anox) * np.exp(rng.normal(0, 0.1)), 10),
                _round_to(tp * (1 + 2.5 * anox) * np.exp(rng.normal(0, 0.2)), 0.5),
                round(do_h, 1),
            ]

    df = df[df.date >= STUDY_START].reset_index(drop=True)
    return df


def make_lakes_daily(seed: int = SEED) -> pd.DataFrame:
    """MASTER: one row = one monitored lake x one day (12 lakes x 2019-2023)."""
    site_seeds = _streams(seed)["daily"].spawn(len(MONITORED))
    parts = [
        _site_daily(np.random.default_rng(ss), s)
        for ss, (_, s) in zip(site_seeds, MONITORED.iterrows(), strict=True)
    ]
    df = pd.concat(parts, ignore_index=True)
    df.insert(2, "year", df.date.dt.year)
    df.insert(3, "month", df.date.dt.month)
    df.insert(4, "split", np.where(df.year == TEST_YEAR, "test", "train"))
    df["date"] = df.date.dt.date
    order = [
        "site_id",
        "date",
        "year",
        "month",
        "split",
        "ice_cover",
        "airt_c",
        "precip_mm",
        "q_m3s",
        "level_m",
        "tw_c",
        "lswt_c",
        "do_mgL",
        "ph",
        "sc_uScm",
        "tu_fnu",
        "chla_ugL",
        "orp_mV",
        "wqi",
        "sat_sensor",
    ] + LAB_COLS
    return df[order]


# --------------------------------------------------------------------------- #
# AUX 1: lake_predictions (long; one row = lake x date x target x model)
# --------------------------------------------------------------------------- #
# (rho_train, rho_test), sd ratio (transformed space), bias (sd units), AR(1) phi of error
MODELS = {
    "ANN": dict(rho=(0.90, 0.84), sd=1.00, bias=0.04, phi=0.55),
    "SVR": dict(rho=(0.86, 0.81), sd=0.82, bias=-0.08, phi=0.70),
    "RF": dict(rho=(0.96, 0.82), sd=0.88, bias=0.00, phi=0.60),
    "KAN": dict(rho=(0.89, 0.86), sd=0.98, bias=0.03, phi=0.50),
    "XGBoost": dict(rho=(0.95, 0.88), sd=0.95, bias=-0.02, phi=0.60),
}
# column, unit, error space ('pow' = Box-Cox 0.3 for skewed targets), difficulty, rows
TARGETS = {
    "Turbidity": ("tu_fnu", "FNU", "pow", 1.0, "L01"),
    "TN": ("tn_ugL", "µg L⁻¹", "pow", 1.4, "lab"),
    "TP": ("tp_ugL", "µg L⁻¹", "pow", 1.7, "lab"),
    "DO": ("do_mgL", "mg L⁻¹", "identity", 0.7, "lab"),
}


def make_lake_predictions(daily: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(_streams(seed)["predictions"])
    out = []
    for target, (col, unit, tf, mult, rows) in TARGETS.items():
        sub = daily[daily.site_id.eq("L01")] if rows == "L01" else daily[daily.tn_ugL.notna()]
        sub = sub[sub[col].notna()].sort_values(["site_id", "date"])
        obs = sub[col].to_numpy(float)
        g = obs**0.3 if tf == "pow" else obs
        mu, sd = g.mean(), g.std()
        z = (g - mu) / sd
        test = sub.split.eq("test").to_numpy()
        for model, p in MODELS.items():
            rho = np.where(test, p["rho"][1], p["rho"][0])
            rho = np.clip(1 - (1 - rho) * mult, 0.30, 0.99)
            e = _ar1(rng, len(z), p["phi"] if rows == "L01" else 0.5 * p["phi"], 1.0)
            zp = p["bias"] + p["sd"] * (rho * z + np.sqrt(1 - rho**2) * e)
            gp = mu + sd * zp
            pred = np.maximum(gp, 0.8 * g.min()) ** (1 / 0.3) if tf == "pow" else gp
            out.append(
                pd.DataFrame(
                    {
                        "site_id": sub.site_id.to_numpy(),
                        "date": sub.date.to_numpy(),
                        "target": target,
                        "unit": unit,
                        "split": sub.split.to_numpy(),
                        "observed": obs,
                        "model": model,
                        "predicted": np.round(pred, 3),
                    }
                )
            )
    return pd.concat(out, ignore_index=True)


# --------------------------------------------------------------------------- #
# AUX 2: lake_inventory (one row = lake; geospatial points + attributes + flags)
# --------------------------------------------------------------------------- #
LULC = [
    "Tree cover",
    "Shrubland",
    "Grassland",
    "Cropland",
    "Built-up",
    "Bare / sparse vegetation",
    "Snow and ice",
    "Permanent water bodies",
    "Herbaceous wetland",
    "Moss and lichen",
]
LULC_EFFECT = dict(
    zip(LULC, [-0.35, 0.0, 0.15, 0.55, 0.45, 0.0, 0.0, 0.0, 0.10, 0.0], strict=True)
)  # on bloom logit
LULC_TP = dict(zip(LULC, [0.8, 1.0, 1.1, 1.6, 1.4, 1.0, 0.9, 1.0, 1.2, 0.9], strict=True))
LULC_NDVI = dict(
    zip(LULC, [0.15, 0.02, 0.0, 0.05, -0.15, -0.25, -0.35, -0.2, 0.05, -0.1], strict=True)
)

DISTRICTS = pd.DataFrame(
    [  # name, lon, lat, sd_lon, sd_lat, n, elev, elev_sd, slope, wind, precip, tp_med, lulc weights
        (
            "Canadian Shield",
            -78.5,
            47.8,
            3.2,
            1.5,
            2600,
            360,
            90,
            3.0,
            3.3,
            920,
            10,
            [60, 8, 3, 3, 1, 2, 0, 6, 12, 5],
        ),
        (
            "Great Lakes Lowlands",
            -80.8,
            44.1,
            1.4,
            0.5,
            1100,
            260,
            50,
            1.2,
            4.0,
            860,
            30,
            [20, 4, 10, 50, 10, 1, 0, 1, 4, 0],
        ),
        (
            "Upper Midwest",
            -91.5,
            46.2,
            2.2,
            1.0,
            1600,
            420,
            60,
            1.5,
            3.8,
            780,
            22,
            [45, 6, 10, 25, 3, 1, 0, 2, 8, 0],
        ),
        (
            "New England",
            -72.2,
            44.3,
            0.9,
            0.8,
            800,
            320,
            120,
            4.0,
            3.6,
            1120,
            12,
            [70, 5, 4, 6, 6, 1, 0, 2, 6, 0],
        ),
        (
            "Boreal Plains",
            -111.0,
            54.8,
            3.8,
            1.4,
            1700,
            620,
            90,
            1.0,
            3.9,
            460,
            35,
            [50, 10, 12, 15, 1, 1, 0, 2, 9, 0],
        ),
        (
            "Prairie Potholes",
            -101.0,
            49.8,
            3.0,
            1.1,
            1500,
            560,
            70,
            0.6,
            5.0,
            430,
            65,
            [5, 5, 30, 52, 2, 2, 0, 1, 3, 0],
        ),
        (
            "Taiga",
            -115.5,
            62.0,
            4.5,
            1.6,
            1300,
            260,
            80,
            1.5,
            3.4,
            320,
            9,
            [40, 22, 6, 0, 0, 6, 1, 4, 8, 13],
        ),
        (
            "Rocky Mountains",
            -106.0,
            39.6,
            1.4,
            1.4,
            500,
            2850,
            400,
            11.0,
            3.6,
            520,
            9,
            [35, 15, 25, 3, 2, 14, 5, 0, 1, 0],
        ),
        (
            "Pacific Northwest",
            -121.8,
            47.4,
            0.8,
            1.4,
            450,
            520,
            300,
            7.0,
            3.1,
            1600,
            12,
            [65, 10, 8, 6, 7, 3, 1, 0, 0, 0],
        ),
        (
            "Florida",
            -81.6,
            28.4,
            0.6,
            0.9,
            400,
            25,
            10,
            0.3,
            3.4,
            1320,
            40,
            [25, 5, 15, 20, 15, 1, 0, 2, 17, 0],
        ),
    ],
    columns=[
        "district",
        "lon",
        "lat",
        "sd_lon",
        "sd_lat",
        "n",
        "elev",
        "elev_sd",
        "slope",
        "wind",
        "precip",
        "tp_med",
        "lulc_w",
    ],
)
# Fictional partner clusters for the world pin-map template. Sizes only; the
# centres are drawn from the inventory stream (see _partner_centres), so no
# cluster sits at, or is named after, a real place.
PARTNER_SIZES = [14, 13, 10, 9, 9, 8, 7, 6, 5, 4, 4, 3, 2, 2]
PARTNER_NAMES = [f"Partner cluster {chr(ord('A') + i)}" for i in range(len(PARTNER_SIZES))]
# Latitude / longitude boxes that are mostly land: (lat0, lat1, lon0, lon1)
_LAND_BOXES = [
    (35.0, 55.0, -120.0, -85.0),  # interior North America
    (-30.0, -5.0, -65.0, -45.0),  # interior South America
    (45.0, 60.0, 10.0, 40.0),  # central and eastern Europe
    (5.0, 15.0, -5.0, 30.0),  # Sahel and Sudan belt
    (-30.0, -18.0, 120.0, 145.0),  # interior Australia
    (22.0, 30.0, 75.0, 90.0),  # Indo-Gangetic plain
]


def _partner_centres(rng: np.random.Generator) -> list[tuple[float, float]]:
    """Draw one (lat, lon) centre per partner cluster from the land-like boxes."""
    centres = []
    for _ in PARTNER_SIZES:
        lat0, lat1, lon0, lon1 = _LAND_BOXES[int(rng.integers(len(_LAND_BOXES)))]
        centres.append((float(rng.uniform(lat0, lat1)), float(rng.uniform(lon0, lon1))))
    return centres


FLAG_PREV = {
    "has_satellite": 0.98,
    "has_insitu": 0.20,
    "has_bathymetry": 0.30,
    "has_gauge": 0.27,
    "has_model": 0.03,
}


def _z(x):
    x = np.asarray(x, float)
    return (x - np.nanmean(x)) / np.nanstd(x)


# Crude boxes over the open water of the Great Lakes: (lat0, lat1, lon0, lon1).
# Inventory points drawn inside them are redrawn so that no lake sits in a Great Lake.
WATER_BOXES = [
    (46.6, 48.3, -91.5, -84.6),  # Superior
    (41.6, 45.8, -87.6, -86.0),  # Michigan
    (43.2, 46.0, -83.4, -81.75),  # Huron
    (44.6, 45.9, -81.3, -79.9),  # Georgian Bay
    (41.4, 42.85, -83.5, -78.9),  # Erie
    (43.2, 43.65, -79.8, -76.2),  # Ontario
]


def in_water(lat, lon) -> np.ndarray:
    """Return True where (lat, lon) falls inside one of the WATER_BOXES."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    out = np.zeros(lat.shape, bool)
    for la0, la1, lo0, lo1 in WATER_BOXES:
        out |= (lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1)
    return out


def _district_points(rng: np.random.Generator, d, k: int) -> tuple[np.ndarray, np.ndarray]:
    lon = np.clip(rng.normal(d.lon, d.sd_lon, k), d.lon - 2.2 * d.sd_lon, d.lon + 2.2 * d.sd_lon)
    lat = np.clip(rng.normal(d.lat, d.sd_lat, k), d.lat - 2.2 * d.sd_lat, d.lat + 2.2 * d.sd_lat)
    return lon, lat


def make_lake_inventory(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(_streams(seed)["inventory"])
    rows = []
    for d in DISTRICTS.itertuples():
        lon, lat = _district_points(rng, d, d.n)
        for _ in range(1000):
            wet = in_water(lat, lon)
            if not wet.any():
                break
            lon[wet], lat[wet] = _district_points(rng, d, int(wet.sum()))
        else:
            raise RuntimeError(f"could not place the {d.district} lakes on land")
        w = np.array(d.lulc_w, float)
        rows.append(
            pd.DataFrame(
                {
                    "role": "inventory",
                    "district": d.district,
                    "country": np.where(lat > 49.0, "CA", "US"),
                    "lon": lon,
                    "lat": lat,
                    "elevation_m": np.maximum(-5, rng.normal(d.elev, d.elev_sd, d.n)),
                    "lulc": rng.choice(LULC, d.n, p=w / w.sum()),
                    "_slope": d.slope,
                    "_wind": d.wind,
                    "_precip": d.precip,
                    "_tp": d.tp_med,
                }
            )
        )
    for name, k, (la, lo) in zip(PARTNER_NAMES, PARTNER_SIZES, _partner_centres(rng), strict=True):
        rows.append(
            pd.DataFrame(
                {
                    "role": "partner",
                    "district": name,
                    "country": "ZZ",
                    "lon": rng.normal(lo, 0.25, k),
                    "lat": rng.normal(la, 0.20, k),
                    "elevation_m": rng.uniform(5, 1100, k),
                    "lulc": rng.choice(["Built-up", "Cropland", "Tree cover"], k),
                    "_slope": 2.0,
                    "_wind": 3.5,
                    "_precip": 700.0,
                    "_tp": 30.0,
                }
            )
        )
    inv = pd.concat(rows, ignore_index=True)
    # Canadian districts straddle the border: fix country by longitude band for the eastern ones
    inv.loc[
        inv.district.isin(["Canadian Shield", "Great Lakes Lowlands"]) & (inv.lat > 43.0), "country"
    ] = "CA"
    n = len(inv)

    inv["area_km2"] = np.clip(np.exp(rng.normal(np.log(0.6), 1.1, n)), 0.05, 3000)
    inv["depth_mean_m"] = np.clip(
        (2 + 2.5 * inv.area_km2**0.25)
        * np.exp(rng.normal(0, 0.4, n))
        * np.where(inv.district.eq("Prairie Potholes"), 0.5, 1.0)
        * np.where(inv.district.eq("Rocky Mountains"), 1.6, 1.0),
        0.5,
        120,
    )
    inv["slope_deg"] = np.round(np.minimum(rng.gamma(1.2, inv._slope / 1.2), 45), 1)
    inv["aspect_deg"] = np.where(inv.slope_deg < 0.5, -1.0, np.round(rng.uniform(0, 360, n)))
    lat, elev = (
        inv.lat.abs().to_numpy(),
        inv.elevation_m.to_numpy(),
    )  # |lat| so partner lakes stay sane
    inv["srad_wm2"] = 255 - 2.3 * lat + 0.004 * elev + rng.normal(0, 4, n)
    inv["tmax_c"] = 41 - 0.70 * lat - 0.0060 * (elev - 300) + rng.normal(0, 1.0, n)
    inv["wind_ms"] = np.clip(inv._wind + rng.normal(0, 0.5, n), 1.3, 9.4)
    inv["precip_mm"] = inv._precip * np.exp(rng.normal(0, 0.12, n))
    inv["pet_mm"] = 300 + 22 * inv.tmax_c + rng.normal(0, 30, n)
    inv["humidity_kgkg"] = 0.0040 * np.exp(0.055 * inv.tmax_c) * np.exp(rng.normal(0, 0.06, n))
    inv["cwd_mm"] = np.maximum(0.4, inv.pet_mm - 0.7 * inv.precip_mm + rng.normal(0, 20, n))
    inv["soil_moisture_mm"] = np.clip(
        20 + 0.12 * inv.precip_mm - 0.3 * inv.cwd_mm + rng.normal(0, 10, n), 4, 190
    )
    inv["ndvi"] = np.clip(
        0.15
        + 0.035 * inv.tmax_c
        + 0.0002 * inv.precip_mm
        + inv.lulc.map(LULC_NDVI)
        + rng.normal(0, 0.05, n),
        -0.10,
        0.85,
    )
    district_wetness = dict(
        zip(inv.district.unique(), rng.normal(0, 0.5, inv.district.nunique()), strict=True)
    )
    inv["pdsi"] = (
        inv.district.map(district_wetness) + rng.normal(0, 0.9, n) + 0.6 * rng.standard_t(5, n)
    )
    inv["tp_ugL"] = np.round(inv._tp * inv.lulc.map(LULC_TP) * np.exp(rng.normal(0, 0.5, n)), 1)
    inv["trophic_class"] = pd.cut(
        inv.tp_ugL,
        [0, 10, 35, 100, np.inf],
        labels=["Oligotrophic", "Mesotrophic", "Eutrophic", "Hypereutrophic"],
        right=False,
    ).astype(str)

    # Bloom model (KNOWN coefficients -> importance & SHAP demos recover them)
    eta = (
        -1.1
        - 1.20 * _z(inv.wind_ms)
        + 0.80 * _z(np.log(inv.tp_ugL))
        + 0.35 * _z(inv.tmax_c)
        + 0.25 * _z(inv.srad_wm2)
        - 0.30 * _z(np.log(inv.depth_mean_m))
        - 0.15 * _z(inv.precip_mm)
        + inv.lulc.map(LULC_EFFECT)
        + rng.normal(0, 0.5, n)
    )
    inv["bloom_likelihood"] = np.round(1 / (1 + np.exp(-eta)), 4)
    n_img = rng.integers(30, 220, n)
    inv["bloom_frequency"] = np.round(
        rng.binomial(
            n_img,
            np.clip((0.01 + 0.20 * inv.bloom_likelihood) * np.exp(rng.normal(0, 0.55, n)), 0, 1),
        )
        / n_img,
        4,
    )
    inv["vulnerable"] = (inv.bloom_likelihood > 0.30) & (inv.depth_mean_m < 8)

    # Data-availability flags: Gaussian copula on a shared latent "accessibility" factor
    latent = 0.6 * _z(np.log(inv.area_km2)) + 0.4 * inv.district.isin(
        ["Great Lakes Lowlands", "New England", "Upper Midwest", "Pacific Northwest"]
    ).astype(float)
    latent = _z(latent)
    load = {
        "has_satellite": 0.5,
        "has_insitu": 0.6,
        "has_bathymetry": 0.5,
        "has_gauge": 0.45,
        "has_model": 0.6,
    }
    for k, prev in FLAG_PREV.items():
        u = load[k] * latent + np.sqrt(1 - load[k] ** 2) * rng.standard_normal(n)
        inv[k] = u > np.quantile(u, 1 - prev)
    inv["has_model"] &= inv.has_insitu | (rng.random(n) < 0.15)  # models mostly need in-situ data

    # Raster-gap NaNs in climate covariates (for pairwise-deletion demos)
    for c in [
        "srad_wm2",
        "tmax_c",
        "wind_ms",
        "precip_mm",
        "pet_mm",
        "humidity_kgkg",
        "cwd_mm",
        "soil_moisture_mm",
        "ndvi",
        "pdsi",
    ]:
        inv.loc[rng.random(n) < rng.uniform(0.003, 0.02), c] = np.nan

    inv = inv.drop(columns=[c for c in inv if c.startswith("_")])
    inv.insert(0, "lake_id", [f"NL{i:05d}" for i in range(1, n + 1)])
    inv.insert(1, "lake_name", pd.Series(pd.NA, index=inv.index, dtype="string"))
    # Overwrite the first 12 Canadian-Shield / district rows with the monitored lakes
    for j, m in enumerate(MONITORED.itertuples()):
        i = inv.index[inv.district.eq(m.district) & inv.role.eq("inventory")][j]
        inv.loc[
            i, ["lake_id", "lake_name", "role", "lon", "lat", "area_km2", "depth_mean_m", "tp_ugL"]
        ] = [
            m.site_id,
            m.lake_name,
            "monitored",
            m.lon,
            m.lat,
            m.area_km2,
            m.depth_mean_m,
            m.tp_ugL,
        ]
        inv.loc[i, list(FLAG_PREV)] = [True, True, True, True, j < 5]
        inv.loc[i, "country"] = "US" if m.district == "Upper Midwest" else "CA"
    inv.loc[inv.role.eq("partner"), "lake_name"] = [
        f"{d}, lake {k + 1}"
        for d, k in zip(
            inv.loc[inv.role.eq("partner"), "district"],
            inv[inv.role.eq("partner")].groupby("district").cumcount(),
            strict=True,
        )
    ]
    decimals = dict(
        lon=4,
        lat=4,
        elevation_m=0,
        area_km2=3,
        depth_mean_m=1,
        srad_wm2=1,
        tmax_c=2,
        wind_ms=2,
        precip_mm=0,
        pet_mm=0,
        humidity_kgkg=5,
        cwd_mm=1,
        soil_moisture_mm=1,
        ndvi=3,
        pdsi=2,
        tp_ugL=1,
    )
    for c, k in decimals.items():
        inv[c] = inv[c].astype(float).round(k)
    # Derive both classes from the stored (rounded) values, after the monitored
    # lakes have been written in, so the documented rules hold on every row.
    inv["trophic_class"] = pd.cut(
        inv.tp_ugL,
        [0, 10, 35, 100, np.inf],
        labels=["Oligotrophic", "Mesotrophic", "Eutrophic", "Hypereutrophic"],
        right=False,
    ).astype(str)
    inv["vulnerable"] = (inv.bloom_likelihood > 0.30) & (inv.depth_mean_m < 8)
    return inv


# --------------------------------------------------------------------------- #
# AUX 3: lake_annual (one row = lake x year, 1980-2023)
# --------------------------------------------------------------------------- #
ANNUAL_DISTRICTS = [
    "Taiga",
    "Boreal Plains",
    "Prairie Potholes",
    "Canadian Shield",
    "Upper Midwest",
    "Great Lakes Lowlands",
    "Rocky Mountains",
]
INTERVENTION_YEAR = 2016  # fictional regional nutrient-management plan
BREAK_YEAR = 2000  # radiation dimming -> brightening


def make_lake_annual(
    inventory: pd.DataFrame, seed: int = SEED, per_district: int = 50
) -> pd.DataFrame:
    rng = np.random.default_rng(_streams(seed)["annual"])
    years = np.arange(1980, 2024)
    pool = inventory[inventory.role.eq("inventory") & inventory.srad_wm2.notna()]
    parts = []
    for d in ANNUAL_DISTRICTS:
        lakes = pool[pool.district.eq(d)].sample(
            per_district, random_state=int(rng.integers(1 << 31))
        )
        s1, s2 = rng.uniform(-0.25, 0.0), rng.uniform(0.05, 0.30)  # W m-2 yr-1 before / after 2000
        trend = np.where(years < BREAK_YEAR, s1 * (years - BREAK_YEAR), s2 * (years - BREAK_YEAR))
        anomaly = _ar1(rng, len(years), 0.4, 2.5)
        for lk in lakes.itertuples():
            srad = lk.srad_wm2 + trend + anomaly + rng.normal(0, 1.2, len(years))
            p_survey = 0.08 + 0.85 / (1 + np.exp(-(years - 2005) / 5.0))
            surveyed = rng.random(len(years)) < p_survey
            base = np.log(lk.bloom_likelihood / (1 - lk.bloom_likelihood))
            after = years >= INTERVENTION_YEAR
            nutrient = lk.trophic_class in ("Eutrophic", "Hypereutrophic")
            slope_after = -0.08 if nutrient else 0.03
            eta = (
                base
                + 0.04 * (years - 1980)
                + after * (-0.25 + slope_after * (years - INTERVENTION_YEAR))
            )
            bloom = rng.random(len(years)) < 1 / (1 + np.exp(-eta))
            troph = {
                "Oligotrophic": -1.0,
                "Mesotrophic": 0.0,
                "Eutrophic": 1.2,
                "Hypereutrophic": 2.0,
            }[lk.trophic_class]
            eta_h = -2.2 + 1.5 * bloom + troph + 0.02 * (years - 1980)
            hyp = rng.random(len(years)) < 1 / (1 + np.exp(-eta_h))
            parts.append(
                pd.DataFrame(
                    {
                        "lake_id": lk.lake_id,
                        "district": d,
                        "trophic_class": lk.trophic_class,
                        "year": years,
                        "srad_wm2": np.round(srad, 2),
                        "surveyed": surveyed,
                        "bloom": pd.array(
                            np.where(surveyed, bloom.astype(int), pd.NA), dtype="Int8"
                        ),
                        "hypoxia": pd.array(
                            np.where(surveyed, hyp.astype(int), pd.NA), dtype="Int8"
                        ),
                    }
                )
            )
    return pd.concat(parts, ignore_index=True)


# --------------------------------------------------------------------------- #
# Derived on load (not stored): hourly buoy series for the high-frequency template
# --------------------------------------------------------------------------- #
def make_lakes_hourly(
    daily: pd.DataFrame, sites=("L01", "L06", "L11"), var="do_mgL", seed: int = SEED
):
    rng = np.random.default_rng(_streams(seed)["hourly"])
    out = []
    for sid in sites:
        d = daily[daily.site_id.eq(sid)][["date", var, "chla_ugL"]].copy()
        t = (
            pd.to_datetime(d.date).to_numpy()[:, None]
            + (np.arange(24) * np.timedelta64(1, "h"))[None, :]
        )
        amp = 0.15 + 0.08 * np.log1p(d.chla_ugL.to_numpy())[:, None]  # diel O2 swing
        v = d[var].to_numpy()[:, None] + amp * np.sin(2 * np.pi * (np.arange(24) - 9) / 24)[None, :]
        v = v + _ar1(rng, v.size, 0.9, 0.12).reshape(v.shape)
        out.append(
            pd.DataFrame({"site_id": sid, "datetime": t.ravel(), var: np.round(v.ravel(), 2)})
        )
    return pd.concat(out, ignore_index=True)
