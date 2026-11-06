"""Daily national price series: gross, net-of-tax, effective vs extract.

Builds the national daily average price per fuel used by the ARDL
counterfactual and the ISTAT reference-day inflation comparison.

Price concepts (per fuel x day, Stradale self-service sample):
  effective — price in force on day D = last communication with
              comu_date <= D (dtComu reconstruction, build_station_day.py);
  extract   — mean of the raw daily extract rows ('naive', the 8am-cut
              snapshot ISTAT-style measurement would see);
  net       — effective gross minus excise, VAT removed:
              net = prezzo / (1 + VAT) - excise(fuel, day)
              (mirrors src/fuel_price_cap/enrich.py NetPriceCalculator).
A balanced-panel variant (stations reporting on >= 95% of window days)
is computed as a composition-noise robustness check.

Inputs: repo parquet cache (prices_raw, stations, tax).
Output: adoption/output/tables/fuel_daily_prices.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402
from build_station_day import build_station_day  # noqa: E402

VAT = 1.22  # mirror src config.VAT_RATE
BALANCED_SHARE = 0.95  # station present on >= 95% of window days


def excise_long() -> pl.DataFrame:
    """Daily excise calendar per fuel (EUR/l), mirroring enrich.py."""
    prices = pl.read_parquet(config.PRICES_PARQUET, columns=["date"])
    lo, hi = (
        max(prices["date"].min(), config.SERIES_FROM),
        config.ANALYSIS_TO,
    )
    tax = pl.read_parquet(config.TAX_PARQUET).select(
        "application_date", "benzina_tax", "gasolio_tax"
    )
    calendar = (
        pl.date_range(lo, hi, "1d", eager=True)
        .alias("date")
        .to_frame()
        .join_asof(tax.sort("application_date"), left_on="date",
                   right_on="application_date", strategy="backward")
    )
    return (
        calendar.unpivot(
            index="date",
            on=("benzina_tax", "gasolio_tax"),
            variable_name="tax_col",
            value_name="excise",
        )
        .with_columns(
            fuel=pl.when(pl.col("tax_col") == "benzina_tax")
            .then(pl.lit(config.FUELS[0]))
            .otherwise(pl.lit(config.FUELS[1])),
            excise=pl.col("excise") / 1000.0,
        )
        .select("date", "fuel", "excise")
    )


def stradale_flag() -> pl.DataFrame:
    """Latest tipo_impianto per station from the weekly anagrafica."""
    stations = pl.read_parquet(
        config.STATIONS_PARQUET,
        columns=["id_impianto", "date", "tipo_impianto"],
    )
    return (
        stations.sort("date")
        .group_by("id_impianto")
        .last()  # most recent snapshot wins
        .select("id_impianto", "tipo_impianto")
    )


def agg(df: pl.DataFrame, prefix: str) -> pl.DataFrame:
    """Per (date x fuel) mean/count, columns prefixed with `prefix`."""
    exprs = [
        pl.col("prezzo").mean().alias(f"{prefix}_mean_gross"),
        pl.len().alias(f"{prefix}_n"),
    ]
    if "net_price" in df.columns:
        exprs.append(pl.col("net_price").mean().alias(f"{prefix}_mean_net"))
    return df.group_by("date", "fuel").agg(exprs)


def main() -> None:
    # 1. effective station-day panel (dtComu reconstruction), window-clipped
    panel = (
        build_station_day()
        .filter(pl.col("date") <= config.ANALYSIS_TO)
        .join(stradale_flag(), on="id_impianto", how="inner")
        .filter(pl.col("tipo_impianto") == config.TIPO_STRADALE)
    )
    panel = panel.join(excise_long(), on=["date", "fuel"], how="left").with_columns(
        net_price=pl.col("prezzo") / VAT - pl.col("excise")
    )

    # 2. naive extract-level series on the same stradale sample
    raw = (
        pl.read_parquet(config.PRICES_PARQUET)
        .filter(
            (pl.col("date") >= config.SERIES_FROM)
            & (pl.col("date") <= config.ANALYSIS_TO)
        )
        .join(stradale_flag(), on="id_impianto", how="inner")
        .filter(pl.col("tipo_impianto") == config.TIPO_STRADALE)
    )

    # 3. balanced-panel variant: stations reporting on >= BALANCED_SHARE days
    n_days = panel["date"].n_unique()
    presence = panel.group_by("id_impianto", "fuel").agg(
        pl.col("date").n_unique().alias("n_days")
    )
    keep = presence.filter(pl.col("n_days") >= BALANCED_SHARE * n_days)
    balanced = panel.join(
        keep.select("id_impianto", "fuel"),
        on=["id_impianto", "fuel"],
        how="semi",
    )

    daily = (
        agg(panel, "eff")
        .join(agg(raw, "naive"), on=["date", "fuel"], how="outer")
        .join(agg(balanced, "bal"), on=["date", "fuel"], how="left")
        .sort("date", "fuel")
    )
    daily.write_csv(config.FUEL_DAILY_CSV)

    # coverage summary
    summary = daily.group_by("fuel").agg(
        pl.col("date").min().alias("from"),
        pl.col("date").max().alias("to"),
        pl.col("eff_n").mean().round(0).alias("mean_stations_per_day"),
        pl.col("eff_mean_gross").last().alias("last_gross"),
        pl.col("eff_mean_net").last().alias("last_net"),
        pl.col("bal_n").mean().round(0).alias("mean_bal_per_day"),
    )
    print(summary)
    print(f"wrote {config.FUEL_DAILY_CSV} ({daily.height} rows)")


if __name__ == "__main__":
    main()
