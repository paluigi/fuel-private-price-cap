"""Per fuel x day definition series for the revised paper (Step 04).

From the effective station-day panel, computes for each fuel and day:
  n_obs                  station-fuel observations (Stradale handled downstream)
  mean_gross / mean_net  equal-weighted means (net = gross/1.22 - excise)
  share_below            share priced strictly below the day's ceiling
  share_newly_below      share below the ceiling today and not below yesterday
  exact_bin_share        share priced exactly 0.001 below the day's ceiling
                         (the bunching bin: 1.999 / 2.199 / 2.260 / 2.211)
  persistence            among stations below the ceiling yesterday, the
                         share still below today
  boundary_exact         count priced exactly at the ceiling (non-compliant
                         under the strict rule)

Output: revision/definitions_daily_series.csv (analysis window 28 Sep-31 Oct
plus the September pre-period for context).
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

VAT = 1.22
OUT = Path(__file__).resolve().parent.parent / "revision" / "definitions_daily_series.csv"


def excise_table() -> pl.DataFrame:
    tax = pl.read_parquet(config.TAX_PARQUET)
    cal = (
        pl.date_range(pl.date(2026, 9, 1), config.ANALYSIS_TO, "1d", eager=True)
        .alias("date")
        .to_frame()
    )
    out = cal.join_asof(
        tax.sort("application_date"),
        left_on="date",
        right_on="application_date",
        strategy="backward",
    )
    return out.select(
        "date",
        benzina_excise=pl.col("benzina_tax") / 1000.0,
        gasolio_excise=pl.col("gasolio_tax") / 1000.0,
    )


def main() -> int:
    panel = pl.read_parquet(
        config.STATION_DAY,
        columns=["date", "fuel", "id_impianto", "prezzo", "cap_threshold",
                 "compliance_at_cap"],
    ).filter(
        (pl.col("date") >= pl.date(2026, 9, 1)) & (pl.col("date") <= config.ANALYSIS_TO)
    )
    exc = excise_table()
    panel = (
        panel.join(exc, on="date", how="left")
        .with_columns(
            excise=pl.when(pl.col("fuel") == "Benzina")
            .then(pl.col("benzina_excise"))
            .otherwise(pl.col("gasolio_excise")),
        )
        .with_columns(net_price=pl.col("prezzo") / VAT - pl.col("excise"))
        .sort("id_impianto", "fuel", "date")
        .with_columns(
            below=pl.col("prezzo") < pl.col("cap_threshold"),
            below_prev=(
                pl.col("prezzo").shift(1) < pl.col("cap_threshold").shift(1)
            ).fill_null(False),
            same_unit=(
                (pl.col("id_impianto") == pl.col("id_impianto").shift(1))
                & (pl.col("fuel") == pl.col("fuel").shift(1))
            ).fill_null(False),
        )
        .with_columns(
            newly_below=pl.col("below") & ~pl.col("below_prev") & pl.col("same_unit"),
            stayed_below=pl.col("below") & pl.col("below_prev") & pl.col("same_unit"),
            was_below=pl.col("below_prev") & pl.col("same_unit"),
        )
    )

    daily = (
        panel.group_by("fuel", "date")
        .agg(
            n_obs=pl.len(),
            mean_gross=pl.col("prezzo").mean(),
            mean_net=pl.col("net_price").mean(),
            share_below=pl.col("below").mean(),
            share_newly_below=pl.col("newly_below").mean(),
            exact_bin_share=(
                (pl.col("prezzo") == (pl.col("cap_threshold") - 0.001).round(3)).mean()
            ),
            boundary_exact=(pl.col("prezzo") == pl.col("cap_threshold")).sum(),
            n_was_below=pl.col("was_below").sum(),
            n_stayed_below=pl.col("stayed_below").sum(),
        )
        .with_columns(
            persistence=pl.when(pl.col("n_was_below") > 0)
            .then(pl.col("n_stayed_below") / pl.col("n_was_below"))
            .otherwise(None)
        )
        .drop("n_was_below", "n_stayed_below")
        .sort("fuel", "date")
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    daily.write_csv(OUT)
    print(f"wrote {OUT} ({daily.height} rows)")
    tail = daily.filter(pl.col("date") >= config.CAP_DATE).group_by("fuel").agg(
        days=pl.len(),
        mean_share_below=pl.col("share_below").mean().round(4),
        final_share=pl.col("share_below").last().round(4),
        max_newly=pl.col("share_newly_below").max().round(4),
    )
    print(tail.sort("fuel"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
