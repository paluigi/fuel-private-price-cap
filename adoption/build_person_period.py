"""Person-period dataset for the discrete-time hazard model (next step).

One row per station-fuel unit per day AT RISK: from the cap date (day 0)
until the day of first compliance (event) or the unit's last observed day
(censored). event = 1 on the adoption day. Covariates from
survival_input.csv (as in the Cox/LPM models), rescaled to the paper's
readable units: pre-gap per 10 c/l, chain per 10 stations, population per
1,000 residents.

Output: output/tables/adoption_person_period.parquet
Run from adoption/: uv run python build_person_period.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

OUT = config.OUT_DIR / "tables" / "adoption_person_period.parquet"


def main() -> int:
    panel = pl.read_parquet(
        config.ADOPTION_PANEL,
        columns=["date", "fuel", "id_impianto", "at_cap", "post", "adopt_date",
                 "days_since_cap"],
    ).filter(pl.col("post"))
    sv = pl.read_csv(
        config.SURVIVAL_INPUT,
        columns=["id_impianto", "fuel", "nn_dist_km", "cap_dist_km_d0",
                 "pop_cell", "pre_gap_vs_cap", "n_stations_gestore",
                 "bandiera", "gestore", "regione"],
    ).with_columns(
        pre_gap_10c=pl.col("pre_gap_vs_cap") * 10,
        chain_10=pl.col("n_stations_gestore") / 10,
        pop_1000=pl.col("pop_cell") / 1000,
    )

    # first below-ceiling day and last observed day per unit
    firsts = (
        panel.filter(pl.col("at_cap"))
        .group_by("id_impianto", "fuel")
        .agg(adopt_day=pl.col("days_since_cap").min())
    )
    lasts = panel.group_by("id_impianto", "fuel").agg(
        last_day=pl.col("days_since_cap").max()
    )
    spans = lasts.join(firsts, on=["id_impianto", "fuel"], how="left").with_columns(
        adopted=pl.col("adopt_day").is_not_null(),
        # at risk through the adoption day (event) or last observed day
        end_day=pl.when(pl.col("adopt_day").is_not_null())
        .then(pl.col("adopt_day"))
        .otherwise(pl.col("last_day")),
    )

    # day grid per unit, event flag on the terminal day for adopters
    grid = (
        spans.join(
            pl.int_range(0, 35, eager=True).alias("day").to_frame(),
            how="cross",
        )
        .filter(pl.col("day") <= pl.col("end_day"))
        .with_columns(event=(pl.col("adopted") & (pl.col("day") == pl.col("end_day"))))
        .select("id_impianto", "fuel", "day", "event")
    )

    pp = grid.join(sv, on=["id_impianto", "fuel"], how="inner")
    pp.write_parquet(OUT)
    # CSV twin for the R layer (no R parquet reader in ~/Rlibs)
    pp.write_csv(OUT.with_suffix(".csv"))
    print(
        f"wrote {OUT}: {pp.height:,} rows, {pp['id_impianto'].n_unique():,} "
        f"station-days per unit avg {pp.height / pp['id_impianto'].n_unique():.1f}, "
        f"events {pp['event'].sum():,}"
    )
    # sanity: events must equal adopted units
    adopted_units = spans["adopted"].sum()
    assert pp["event"].sum() == adopted_units, (
        f"events {pp['event'].sum()} != adopted units {adopted_units}"
    )
    print(f"sanity ok: {adopted_units:,} events = adopted units")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
