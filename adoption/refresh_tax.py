"""Refresh data/tax.parquet from the MongoDB ``fuels.tax`` collection.

The cached parquet starts in May 2026 (``src`` pipeline ``TAX_FROM``), but the
collection holds the statutory excise calendar from 2005 onwards. The extended
January-October 2026 estimation window (revision D6) needs net-of-tax prices
from 1 January, so this script re-extracts the full history with the same
projection/dedup convention as ``FuelDataRepository._fetch_tax``
(application_date, benzina_tax, gasolio_tax; EUR per 1000 litres; keep=last
per date; sorted), then verifies every previously cached row is unchanged
before overwriting ``data/tax.parquet``.

Usage (repository root):

    uv run python -I adoption/refresh_tax.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from pymongo import MongoClient

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "tax.parquet"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="validate only; do not overwrite the parquet")
    args = ap.parse_args(argv)

    load_dotenv(REPO / ".env")
    uri = os.environ.get("MONGO_URI")
    if not uri:
        print("ERROR: MONGO_URI not set in .env", file=sys.stderr)
        return 2

    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)
    pipeline = [
        {"$project": {"_id": 0, "application_date": 1,
                      "benzina_tax": 1, "gasolio_tax": 1}},
        {"$sort": {"application_date": 1}},
    ]
    docs = list(client["fuels"]["tax"].aggregate(pipeline))
    if not docs:
        print("ERROR: fuels.tax returned no documents", file=sys.stderr)
        return 2
    fresh = (
        pl.DataFrame(docs)
        .select(
            pl.col("application_date").str.to_date("%Y-%m-%d"),
            pl.col("benzina_tax").cast(pl.Float64),
            pl.col("gasolio_tax").cast(pl.Float64),
        )
        .unique(subset=["application_date"], keep="last")
        .sort("application_date")
    )

    old = pl.read_parquet(OUT)
    merged = old.join(fresh, on="application_date", how="left",
                      suffix="_new", validate="1:1")
    changed = merged.filter(
        (pl.col("benzina_tax") != pl.col("benzina_tax_new"))
        | (pl.col("gasolio_tax") != pl.col("gasolio_tax_new"))
    )
    print(f"collection rows: {fresh.height} "
          f"({fresh['application_date'].min()} .. {fresh['application_date'].max()})")
    print(f"cached rows: {old.height}; changed vs collection: {changed.height}")
    print("rows in 2026:")
    print(fresh.filter(pl.col("application_date") >= pl.date(2025, 12, 1)))
    if changed.height:
        diff_cols = ["application_date", "benzina_tax", "benzina_tax_new",
                     "gasolio_tax", "gasolio_tax_new"]
        print("ERROR: cached tax rows differ from the collection — "
              "old values would be silently replaced:\n"
              f"{changed.select(diff_cols)}",
              file=sys.stderr)
        return 2

    if args.dry_run:
        print("dry run: parquet left unchanged")
        return 0
    fresh.write_parquet(OUT)
    print(f"wrote {OUT} ({fresh.height} rows, from "
          f"{fresh['application_date'].min()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
