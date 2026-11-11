"""Configuration and shared paths for the cap-adoption analysis.

All scripts in adoption/ import from here. Data conventions follow the
repo's italian-open-data skill notes (MIMIT quirks, dtComu semantics).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

ADOPTION_DIR = Path(__file__).resolve().parent
DATA_DIR = ADOPTION_DIR / "data"
OUT_DIR = ADOPTION_DIR / "output"
R_DIR = ADOPTION_DIR / "R"
for _p in (DATA_DIR, OUT_DIR, OUT_DIR / "tables", OUT_DIR / "figures", R_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- #
# Analysis window
# ---------------------------------------------------------------- #
SERIES_FROM = dt.date(2026, 1, 1)  # extended window: H1 archives + H2 cache (D6)
ANALYSIS_TO = dt.date(2026, 10, 31)  # analysis window end (user override)
CAP_DATE = dt.date(2026, 9, 28)  # self-imposed cap effective date
PRE_WINDOW = (dt.date(2026, 9, 21), dt.date(2026, 9, 27))  # 7d pre-cap
# Pre phase for the DESCRIPTIVE dispersion/competitiveness tables and maps
# (sec 7 + appendix D): the full September run-up. Kept separate from
# PRE_WINDOW, which feeds the pre_gap_vs_cap covariate in the survival/LPM
# models and must stay the 7-day window closest to the cap.
PRE_WINDOW_DISP = (dt.date(2026, 9, 1), dt.date(2026, 9, 27))
# Micro (station-level) layer anchor: the panel/survival/distances keep the
# v1 span (1 Jul - 31 Oct) regardless of SERIES_FROM, so covariates such as
# mean nearest-neighbour distance are not silently redefined when the macro
# estimation window extends back to January (D6b).
MICRO_FROM = dt.date(2026, 7, 1)
# Nominal cap thresholds announced by Eni on 2026-09-25 (EUR/l, Stradale
# self-service): 1.99 petrol / 2.19 diesel. Operational study cutoffs are the
# rounded-up 2.00 / 2.20 gross levels; compliance uses a STRICT inequality,
# prezzo < threshold (author rule D3): with 3-decimal prices this means
# petrol <= 1.999, diesel <= 2.199 are compliant, 2.000/2.200 are not.
THRESHOLDS = {"Benzina": 2.00, "Gasolio": 2.20}
# Gasolio cap tracks the excise calendar (mechanical VAT translation):
#   2026-10-06: the 5 c/l discount is removed (622.90 -> 672.90 EUR/1000 l),
#               cap +0.05 * 1.22 = +6.1 c/l -> 2.261;
#   2026-10-28: excise cut 672.90 -> 632.90 (D.L. rollback), cap
#               -0.04 * 1.22 = -4.88 c/l -> 2.261 - 0.0488 = 2.2122, taken to
#               the 3-decimal operational grid as 2.212 (author rule D4).
GASOLIO_TAX_BACK = dt.date(2026, 10, 6)
GASOLIO_CAP_ADJ = 0.05 * 1.22  # EUR/l
GASOLIO_TAX_CUT = dt.date(2026, 10, 28)
GASOLIO_CAP_ADJ_DOWN = 0.04 * 1.22  # EUR/l
GASOLIO_CAP_FINAL = round(2.20 + GASOLIO_CAP_ADJ - GASOLIO_CAP_ADJ_DOWN, 3)  # 2.212
THRESHOLD_BY_DATE = {
    fuel: [
        (dt.date(2026, 9, 28), th),
        (GASOLIO_TAX_BACK, th + (GASOLIO_CAP_ADJ if fuel == "Gasolio" else 0.0)),
        (GASOLIO_TAX_CUT, th + (GASOLIO_CAP_ADJ - GASOLIO_CAP_ADJ_DOWN if fuel == "Gasolio" else 0.0)),
    ]
    for fuel, th in THRESHOLDS.items()
}
# The 3-decimal grid value above is exact for display; use the rounded final
# level so code and prose quote the same 2.212 (see D4).
THRESHOLD_BY_DATE["Gasolio"][2] = (GASOLIO_TAX_CUT, GASOLIO_CAP_FINAL)


def cap_threshold(fuel: str, day: dt.date) -> float:
    """Effective cap threshold for a fuel on a given day."""
    steps = THRESHOLD_BY_DATE[fuel]
    eff = steps[0][1]
    for from_d, th in steps:
        if day >= from_d:
            eff = th
    return eff


TIPO_STRADALE = "Stradale"
FUELS = ("Benzina", "Gasolio")

# ---------------------------------------------------------------- #
# Inputs (repo root cache; ../data relative to adoption/)
# ---------------------------------------------------------------- #
_REPO_ROOT = ADOPTION_DIR.parent
# Full-2026 price panel: H1 MIMIT archives (build_archive_prices.py) joined
# with the H2 MongoDB cache. Built by `make_prices_full.py`; the raw H2-only
# extract stays at data/prices_raw.parquet for the src/ descriptive layer.
PRICES_PARQUET = _REPO_ROOT / "data" / "prices_full_2026.parquet"
PRICES_ARCHIVE = _REPO_ROOT / "data" / "prices_archive.parquet"  # H1 (Jan-Jun)
PRICES_RAW = _REPO_ROOT / "data" / "prices_raw.parquet"  # H2 (Jul-Nov cache)
STATIONS_PARQUET = _REPO_ROOT / "data" / "stations.parquet"  # weekly anagrafica
TAX_PARQUET = _REPO_ROOT / "data" / "tax.parquet"  # excise calendar
EXTERNAL_DIR = _REPO_ROOT / "data" / "external"  # committed raw downloads
ANAGRAFICA_CSV = DATA_DIR / "anagrafica_impianti_attivi.csv"  # MIMIT, has Comune
GRID_CSV = DATA_DIR / "istat_grid" / "GrigliaPop2021_Ind_ITA_CSV.txt"
# NOTE: the 2026 zip extracts WITHOUT a top-level folder (unlike earlier
# vintages) — the four layer dirs sit directly in istat_borders/.
BORDERS_DIR = DATA_DIR / "istat_borders"

# ---------------------------------------------------------------- #
# Outputs
# ---------------------------------------------------------------- #
STATION_DAY = OUT_DIR / "tables" / "station_day_prices.parquet"
OIL_FX_CSV = OUT_DIR / "tables" / "oil_fx_daily.csv"  # business days
OIL_FX_FFILL_CSV = OUT_DIR / "tables" / "oil_fx_daily_ffill.csv"  # calendar days
FUEL_DAILY_CSV = OUT_DIR / "tables" / "fuel_daily_prices.csv"
COUNTERFACTUAL_CSV = OUT_DIR / "tables" / "counterfactual_daily.csv"
BACKTEST_CSV = OUT_DIR / "tables" / "backtest_daily.csv"
INFLATION_DAYS_CSV = OUT_DIR / "tables" / "inflation_days.csv"
INFLATION_SUMMARY_CSV = OUT_DIR / "tables" / "inflation_summary.csv"
STATION_STATIC = OUT_DIR / "tables" / "station_covariates.parquet"
DISTANCES = OUT_DIR / "tables" / "station_day_distances.parquet"
ADOPTION_PANEL = OUT_DIR / "tables" / "adoption_panel.parquet"
SURVIVAL_INPUT = OUT_DIR / "tables" / "survival_input.csv"
PROV_DISPERSION = OUT_DIR / "tables" / "province_dispersion.csv"
COMPETITIVENESS = OUT_DIR / "tables" / "nonadopter_competitiveness.csv"
