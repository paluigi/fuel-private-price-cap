"""Decomposition and bunching analyses (Steps 10-11).

1. 6 October diesel compliance jump: mechanical (ceiling 2.200 -> 2.261 moves
   the compliant band) vs behavioural (stations re-communicating on the day).
2. Exact price-ending frequencies pre vs post cap (bunching one decimal below
   the ceiling vs generic 9-endings).
3. Contribution of brand groups to the national mean price movement
   (descriptive decomposition of actual minus no-cap by group share).
4. Dispersion with consistent windows: SD / p90-p10 / adopter-nonadopter gap,
   pre = 1-27 Sep and 21-27 Sep, post = 28 Sep-31 Oct.

Output: revision/decomposition_6oct.csv, revision/price_endings.csv,
        revision/group_decomposition.csv, revision/dispersion_summary.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "revision"
VAT = 1.22

GROUPS = {
    "Agip Eni": "Eni",
    "Q8": "Q8",
    "Api-Ip": "Api-Ip",
    "Esso": "Esso",
    "Tamoil": "Tamoil",
    "Pompe Bianche": "White pumps",
}


def load_panel() -> pl.DataFrame:
    return pl.read_parquet(
        config.ADOPTION_PANEL,
        columns=["date", "fuel", "id_impianto", "prezzo", "at_cap",
                 "bandiera", "comu_day"],
    )


def jump_decomposition(p: pl.DataFrame) -> None:
    d = p.filter(
        (pl.col("fuel") == "Gasolio")
        & pl.col("date").is_between(pl.date(2026, 10, 4), pl.date(2026, 10, 7))
    ).with_columns(
        below_old=pl.col("prezzo") < 2.200,
        below_new=pl.col("prezzo") < 2.261,
        fresh=pl.col("comu_day") >= pl.date(2026, 10, 6),
    )
    rows = (
        d.group_by("date")
        .agg(
            n=pl.len(),
            below_old=(100 * pl.col("below_old").mean()).round(2),
            below_new=(100 * pl.col("below_new").mean()).round(2),
            in_band=(100 * ((pl.col("prezzo") >= 2.200) & (pl.col("prezzo") < 2.261)).mean()).round(2),
            in_band_stale=(
                100
                * (
                    (pl.col("prezzo") >= 2.200)
                    & (pl.col("prezzo") < 2.261)
                    & ~pl.col("fresh")
                ).mean()
            ).round(2),
            in_band_fresh=(
                100
                * (
                    (pl.col("prezzo") >= 2.200)
                    & (pl.col("prezzo") < 2.261)
                    & pl.col("fresh")
                ).mean()
            ).round(2),
            moved_4_8=(
                100 * (pl.col("prezzo").is_between(2.24, 2.28)).mean()
            ).round(2),
        )
        .sort("date")
    )
    rows.write_csv(OUT / "decomposition_6oct.csv")
    print("== 6 Oct diesel jump decomposition ==")
    print(rows)


def endings(p: pl.DataFrame) -> None:
    post = p.filter(pl.col("date") >= config.CAP_DATE)
    pre = p.filter(
        pl.col("date").is_between(pl.date(2026, 9, 1), pl.date(2026, 9, 27))
    )
    for tag, df in (("pre", pre), ("post", post)):
        e = (
            df.with_columns(
                ending=pl.col("prezzo").round(2).mod(1.0).round(2)
            )
            .group_by("fuel", "ending")
            .agg(n=pl.len())
            .with_columns((100 * pl.col("n") / df.height).round(3).alias("pct_of_fuel"))
            .filter(pl.col("pct_of_fuel") > 0.8)
            .sort("fuel", "pct_of_fuel", descending=True)
        )
        (e.drop("n")).write_csv(OUT / f"price_endings_{tag}.csv")
        print(f"== top price endings {tag}-cap ==")
        print(e.head(12))


def group_decomposition(p: pl.DataFrame) -> None:
    cf = pl.read_csv(
        config.OUT_DIR / "tables" / "counterfactual_daily.csv",
        try_parse_dates=True,
    )
    grp = p.with_columns(
        group=pl.col("bandiera").replace_strict(GROUPS, default="Other brands")
    )
    # 27 Sep actual -> 31 Oct actual, and mean gap vs counterfactual by group
    first = grp.filter(pl.col("date") == pl.date(2026, 9, 27)).group_by(
        "fuel", "group"
    ).agg(p0=pl.col("prezzo").mean(), n0=pl.len())
    last = grp.filter(pl.col("date") == pl.date(2026, 10, 31)).group_by(
        "fuel", "group"
    ).agg(p1=pl.col("prezzo").mean(), n1=pl.len())
    base = first.join(last, on=["fuel", "group"], how="inner").with_columns(
        share=pl.col("n1") / pl.col("n1").sum().over("fuel"),
        delta=(pl.col("p1") - pl.col("p0")) * 100,
    )
    # contribution of each group to the fuel-level mean change
    tot = base.group_by("fuel").agg(tot_delta=pl.col("delta").dot(pl.col("share")))
    base = base.join(tot, on="fuel").with_columns(
        contrib=pl.col("delta") * pl.col("share"),
        pct_of_move=100 * pl.col("delta") * pl.col("share") / pl.col("tot_delta"),
    )
    base.sort("fuel", "share", descending=True).write_csv(
        OUT / "group_decomposition.csv"
    )
    print("== group decomposition of 27 Sep -> 31 Oct mean move (c/l) ==")
    print(base.sort("fuel", "share", descending=True).head(16))
    print("fuel-level total moves:", tot.sort("fuel"))


def dispersion(p: pl.DataFrame) -> None:
    prov = pl.read_parquet(
        config.OUT_DIR / "tables" / "adoption_panel.parquet",
        columns=["date", "fuel", "id_impianto", "prezzo", "provincia_istat",
                 "at_cap"],
    )
    wins = {
        "pre_full (1-27 Sep)": (pl.date(2026, 9, 1), pl.date(2026, 9, 27)),
        "pre_week (21-27 Sep)": (pl.date(2026, 9, 21), pl.date(2026, 9, 27)),
        "post (28 Sep-31 Oct)": (config.CAP_DATE, config.ANALYSIS_TO),
    }
    rows = []
    for wname, (a, b) in wins.items():
        for f in config.FUELS:
            d = prov.filter(
                (pl.col("fuel") == f) & pl.col("date").is_between(a, b)
            )
            day_sd = d.group_by("date", "provincia_istat").agg(
                sd=pl.col("prezzo").std()
            )
            day_gap = d.group_by("date", "provincia_istat").agg(
                p90=pl.col("prezzo").quantile(0.9),
                p10=pl.col("prezzo").quantile(0.1),
            )
            na_gap = d.filter(pl.col("date") >= config.CAP_DATE).group_by(
                "date", "provincia_istat"
            ).agg(
                g_ado=pl.col("prezzo").filter(pl.col("at_cap")).mean(),
                g_non=pl.col("prezzo").filter(~pl.col("at_cap")).mean(),
            ) if wname.startswith("post") else None
            row = {
                "window": wname, "fuel": f,
                "pooled_sd": round(d["prezzo"].std() * 100, 2),
                "mean_within_prov_sd": round(day_sd["sd"].mean() * 100, 2),
                "median_within_prov_sd": round(day_sd["sd"].median() * 100, 2),
                "mean_p90p10": round((day_gap["p90"] - day_gap["p10"]).mean() * 100, 2),
            }
            if na_gap is not None:
                row["adopter_minus_non_gap"] = round(
                    (na_gap["g_ado"] - na_gap["g_non"]).mean() * 100, 2
                )
            rows.append(row)
    pl.DataFrame(rows).write_csv(OUT / "dispersion_summary.csv")
    print("== dispersion summary (c/l) ==")
    print(pl.DataFrame(rows))


def main() -> int:
    p = load_panel()
    jump_decomposition(p)
    endings(p)
    group_decomposition(p)
    dispersion(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
