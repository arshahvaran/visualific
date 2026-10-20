"""Column metadata for the synthetic gallery tables: unit, dtype and a short description."""

from __future__ import annotations

#: Version of the bundled snapshot. Bump it whenever the generator output changes.
VERSION = "1"
#: NumPy major.minor that produced the bundled snapshot; regeneration tests compare
#: values only under this version, because random streams may differ between versions.
NUMPY_VERSION = "2.5"
SEED = 2026
ARCHIVE = "visualific_synthetic.zip"

# table -> column -> (unit, dtype, description)
COLUMNS: dict[str, dict[str, tuple[str, str, str]]] = {
    "lakes_daily": {
        "site_id": ("", "category", "Monitored lake identifier, L01 to L12."),
        "date": ("", "datetime64[ns]", "Calendar day."),
        "year": ("", "int64", "Calendar year."),
        "month": ("", "int64", "Calendar month, 1 to 12."),
        "split": ("", "category", "Model split: 2023 is 'test', earlier years 'train'."),
        "ice_cover": ("", "bool", "True when the lake is ice-covered."),
        "airt_c": ("°C", "float64", "Daily mean air temperature."),
        "precip_mm": ("mm d⁻¹", "float64", "Daily precipitation."),
        "q_m3s": ("m³ s⁻¹", "float64", "Outflow discharge at the gauge."),
        "level_m": ("m", "float64", "Water level above the gauge datum."),
        "tw_c": ("°C", "float64", "Buoy surface water temperature."),
        "lswt_c": (
            "°C",
            "float64",
            "Satellite thermal lake surface water temperature; about 1.5 % of retrievals "
            "are cloud-contaminated cold outliers, some below 0 °C.",
        ),
        "do_mgL": ("mg L⁻¹", "float64", "Buoy dissolved oxygen."),
        "ph": ("", "float64", "Buoy pH."),
        "sc_uScm": ("µS cm⁻¹", "float64", "Buoy specific conductance."),
        "tu_fnu": ("FNU", "float64", "Buoy turbidity."),
        "chla_ugL": ("µg L⁻¹", "float64", "Buoy chlorophyll-a."),
        "orp_mV": ("mV", "float64", "Buoy oxidation-reduction potential."),
        "wqi": ("", "float64", "Synthetic water-quality index, 0 to 100."),
        "sat_sensor": ("", "category", "Optical sensor with a valid retrieval that day, if any."),
        "tn_ugL": ("µg L⁻¹", "float64", "Lab total nitrogen, surface sample."),
        "tp_ugL": ("µg L⁻¹", "float64", "Lab total phosphorus, surface sample."),
        "cod_mgL": (
            "mg L⁻¹",
            "float64",
            "Lab chemical oxygen demand, permanganate method (COD-Mn).",
        ),
        "colour_mgPtL": ("mg Pt L⁻¹", "float64", "Lab true colour."),
        "tn_hypo_ugL": ("µg L⁻¹", "float64", "Lab total nitrogen, hypolimnion sample."),
        "tp_hypo_ugL": ("µg L⁻¹", "float64", "Lab total phosphorus, hypolimnion sample."),
        "do_hypo_mgL": ("mg L⁻¹", "float64", "Dissolved oxygen in the hypolimnion."),
    },
    "lake_predictions": {
        "site_id": ("", "category", "Monitored lake identifier."),
        "date": ("", "datetime64[ns]", "Calendar day of the observation."),
        "target": ("", "category", "Predicted variable: Turbidity, TN, TP or DO."),
        "unit": ("", "category", "Unit of the observed and predicted values."),
        "split": ("", "category", "Model split, 'train' or 'test'."),
        "observed": ("see unit", "float64", "Observed value."),
        "model": ("", "category", "Model name: ANN, SVR, RF, KAN or XGBoost."),
        "predicted": ("see unit", "float64", "Predicted value."),
    },
    "lake_inventory": {
        "lake_id": ("", "string", "Lake identifier; monitored lakes keep their L01 to L12 ids."),
        "lake_name": ("", "string", "Name for monitored and partner lakes, missing otherwise."),
        "role": ("", "category", "'monitored', 'inventory' or 'partner'."),
        "district": ("", "category", "Physiographic district, or fictional partner cluster."),
        "country": ("", "category", "CA, US, or ZZ for the fictional partner clusters."),
        "lon": ("° E", "float64", "Longitude."),
        "lat": ("° N", "float64", "Latitude."),
        "elevation_m": ("m", "float64", "Elevation above sea level."),
        "lulc": ("", "category", "Dominant land use and land cover around the lake."),
        "area_km2": ("km²", "float64", "Surface area."),
        "depth_mean_m": ("m", "float64", "Mean depth."),
        "slope_deg": ("°", "float64", "Mean terrain slope around the lake."),
        "aspect_deg": ("°", "float64", "Mean terrain aspect; -1 where the terrain is flat."),
        "srad_wm2": ("W m⁻²", "float64", "Mean shortwave radiation."),
        "tmax_c": ("°C", "float64", "Mean daily maximum air temperature."),
        "wind_ms": ("m s⁻¹", "float64", "Mean wind speed."),
        "precip_mm": ("mm yr⁻¹", "float64", "Annual precipitation."),
        "pet_mm": ("mm yr⁻¹", "float64", "Annual potential evapotranspiration."),
        "humidity_kgkg": ("kg kg⁻¹", "float64", "Specific humidity."),
        "cwd_mm": ("mm yr⁻¹", "float64", "Climatic water deficit."),
        "soil_moisture_mm": ("mm", "float64", "Soil moisture."),
        "ndvi": ("", "float64", "Normalised difference vegetation index."),
        "pdsi": ("", "float64", "Palmer drought severity index."),
        "tp_ugL": ("µg L⁻¹", "float64", "Total phosphorus."),
        "trophic_class": ("", "category", "Trophic class from total phosphorus."),
        "bloom_likelihood": ("", "float64", "Modelled probability of an algal bloom, 0 to 1."),
        "bloom_frequency": ("", "float64", "Share of satellite images showing a bloom."),
        "vulnerable": ("", "bool", "Bloom likelihood above 0.30 and mean depth below 8 m."),
        "has_satellite": ("", "bool", "Satellite record available."),
        "has_insitu": ("", "bool", "In-situ sampling record available."),
        "has_bathymetry": ("", "bool", "Bathymetric survey available."),
        "has_gauge": ("", "bool", "Water-level or discharge gauge available."),
        "has_model": ("", "bool", "A calibrated lake model exists."),
    },
    "lake_annual": {
        "lake_id": ("", "string", "Lake identifier from the inventory."),
        "district": ("", "category", "Physiographic district."),
        "trophic_class": ("", "category", "Trophic class from the inventory."),
        "year": ("", "int64", "Calendar year, 1980 to 2023."),
        "srad_wm2": ("W m⁻²", "float64", "Annual mean shortwave radiation."),
        "surveyed": ("", "bool", "True when the lake was surveyed that year."),
        "bloom": ("", "Int8", "1 if a bloom was recorded, 0 if not, missing if not surveyed."),
        "hypoxia": ("", "Int8", "1 if hypoxia was recorded, 0 if not, missing if not surveyed."),
    },
}

DESCRIPTIONS = {
    "lakes_daily": "Daily records for twelve fictional monitored lakes, 2019 to 2023.",
    "lake_predictions": "Observed and predicted values from five models, long form.",
    "lake_inventory": "Inventory of fictional lakes with coordinates, covariates and flags.",
    "lake_annual": "Lake-year panel for 350 inventory lakes, 1980 to 2023.",
}


def categories() -> dict[str, dict[str, list[str]]]:
    """Return the fixed level order of every categorical column, table by table.

    The orders follow the gallery spec cards (model colours, panel order), not the
    alphabet, so templates that facet in category order draw panels consistently.
    """
    from . import _generate

    sites = [f"L{i:02d}" for i in range(1, 13)]
    splits = ["train", "test"]
    trophic = ["Oligotrophic", "Mesotrophic", "Eutrophic", "Hypereutrophic"]
    return {
        "lakes_daily": {
            "site_id": sites,
            "split": splits,
            "sat_sensor": ["Landsat 7", "Landsat 8", "Landsat 9", "Sentinel-2"],
        },
        "lake_predictions": {
            "site_id": sites,
            "target": list(_generate.TARGETS),
            "unit": ["FNU", "µg L⁻¹", "mg L⁻¹"],
            "split": splits,
            "model": list(_generate.MODELS),
        },
        "lake_inventory": {
            "role": ["monitored", "inventory", "partner"],
            "district": [*_generate.DISTRICTS.district, *_generate.PARTNER_NAMES],
            "country": ["CA", "US", "ZZ"],
            "lulc": list(_generate.LULC),
            "trophic_class": trophic,
        },
        "lake_annual": {
            "district": list(_generate.ANNUAL_DISTRICTS),
            "trophic_class": trophic,
        },
    }


#: Categorical columns whose levels are ordinal.
ORDERED = frozenset({"trophic_class"})
