"""Build the H1-2026 MIMIT archive price extract.

Reads the official MIMIT ``prezzo_alle_8`` daily CSVs extracted from
``data/mimit_archives/2026_{1,2}_tr.tar.gz`` (1 January - 30 June 2026) and
writes ``data/prices_archive.parquet`` with exactly the schema of
``data/prices_raw.parquet`` (id_impianto, date, fuel, prezzo, dt_comu) so the
two extracts can be concatenated into one 2026 panel:

    pl.concat([prices_archive, prices_raw])

Filtering mirrors the MongoDB extraction in src/fuel_price_cap/data.py:
``isSelf = 1`` and carburante in {Benzina, Gasolio} only.

Usage (run from the repository root):

    uv run python -I adoption/build_archive_prices.py \
        --archive-root data/mimit_archives/extracted \
        --reference data/prices_raw.parquet \
        --out data/prices_archive.parquet

The archive files are treated as untrusted input: they are only read, never
execed; every anomaly (missing day, duplicate key, unparseable row) is
reported and fails the build unless --allow-missing-days is given.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl

FUELS = ("Benzina", "Gasolio")
PREVIOUS_FILENAME = "prezzo_alle_8-{ymd}.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--archive-root",
        type=Path,
        default=Path("data/mimit_archives/extracted"),
        help="directory containing the 2026_1/2026_2 extracted folders",
    )
    ap.add_argument(
        "--reference",
        type=Path,
        default=Path("data/prices_raw.parquet"),
        help="existing raw extract used for schema/validation checks",
    )
    ap.add_argument(
        "--out", type=Path, default=Path("data/prices_archive.parquet"),
        help="output parquet path",
    )
    ap.add_argument(
        "--allow-missing-days", action="store_true",
        help="tolerate missing daily files (recorded, not fatal)",
    )
    return ap.parse_args(argv)


def read_one(csv_path: Path, extract_date: date) -> pl.DataFrame:
    """Parse one MIMIT daily file into the prices_raw schema."""
    df = pl.read_csv(
        csv_path,
        separator="|",
        skip_rows=1,  # "Estrazione del ..." preamble
        schema_overrides={"idImpianto": pl.Int64, "prezzo": pl.Float64},
    )
    keep = (
        df.filter(
            (pl.col("isSelf") == 1) & pl.col("descCarburante").is_in(list(FUELS))
        )
        .select(
            id_impianto=pl.col("idImpianto"),
            date=pl.lit(extract_date, dtype=pl.Date),
            fuel=pl.col("descCarburante"),
            prezzo=pl.col("prezzo"),
            dt_comu=pl.col("dtComu"),
        )
    )
    return keep


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    csv_files: list[tuple[date, Path]] = []
    for sub in sorted(args.archive_root.iterdir()):
        if not sub.is_dir():
            continue
        for f in sorted(sub.rglob("prezzo_alle_8-*.csv")):
            ymd = f.stem.split("-")[1]
            csv_files.append((datetime.strptime(ymd, "%Y%m%d").date(), f))

    if not csv_files:
        print(f"ERROR: no prezzo_alle_8-*.csv under {args.archive_root}", file=sys.stderr)
        return 2
    csv_files.sort()

    # --- calendar continuity -------------------------------------------
    first, last = csv_files[0][0], csv_files[-1][0]
    have = {d for d, _ in csv_files}
    expected: list[date] = []
    d = first
    while d <= last:
        expected.append(d)
        d += timedelta(days=1)
    missing = [d for d in expected if d not in have]
    if missing and not args.allow_missing_days:
        print(f"ERROR: {len(missing)} calendar days without a file: {missing}", file=sys.stderr)
        return 2
    if missing:
        print(f"WARNING: tolerating missing days: {missing}")

    # --- parse and stack ------------------------------------------------
    frames, anomalies = [], []
    for d, f in csv_files:
        day = read_one(f, d)
        if day.height == 0:
            anomalies.append(f"{d}: zero Benzina/Gasolio isSelf rows")
        frames.append(day)
    prices = pl.concat(frames, how="vertical")

    # --- validation ------------------------------------------------------
    dup = (
        prices.group_by(["id_impianto", "date", "fuel"]).len().filter(pl.col("len") > 1)
    )
    if dup.height:
        print(f"ERROR: {dup.height} duplicate (id, date, fuel) keys", file=sys.stderr)
        return 2
    bad_dt = prices.filter(
        pl.col("dt_comu").str.strptime(pl.Datetime, "%d/%m/%Y %H:%M:%S", strict=False).is_null()
    )
    if bad_dt.height:
        print(
            f"ERROR: {bad_dt.height} rows with unparseable dtComu; sample:\n"
            f"{bad_dt.head(3)}",
            file=sys.stderr,
        )
        return 2
    # Placeholder prices (e.g. the 8.888 EUR/l test rows some stations send)
    # never appear in the MongoDB reference extract; drop them here too and
    # log the count so the two extracts share one convention.
    bad_price = prices.filter(
        pl.col("prezzo").is_null() | (pl.col("prezzo") <= 0) | (pl.col("prezzo") > 5)
    )
    if bad_price.height:
        print(
            f"NOTE: dropping {bad_price.height} rows with prezzo null/<=0/>5 EUR/l "
            f"({bad_price['id_impianto'].n_unique()} stations); sample:\n"
            f"{bad_price.head(3)}"
        )
        prices = prices.filter(
            pl.col("prezzo").is_not_null() & (pl.col("prezzo") > 0)
            & (pl.col("prezzo") <= 5)
        )

    # --- overlap with the July-November reference extract ----------------
    ref = pl.read_parquet(args.reference)
    archive_stations = set(prices["id_impianto"].unique())
    ref_stations = set(ref["id_impianto"].unique())
    overlap = len(archive_stations & ref_stations)
    print(f"archive: {prices.height:,} rows, {len(csv_files)} daily files, "
          f"{first} .. {last}")
    print(f"rows/fuel: {prices.group_by('fuel').len().sort('fuel').to_dicts()}")
    print(f"stations in archive: {len(archive_stations):,}; "
          f"overlap with reference: {overlap:,} "
          f"({100 * overlap / max(len(archive_stations), 1):.1f}%); "
          f"reference-only: {len(ref_stations - archive_stations):,}")
    print(f"dt_comu min/max: {prices['dt_comu'].min()} / {prices['dt_comu'].max()}")

    # schema must match the reference exactly
    if prices.schema != ref.schema:
        print(f"ERROR: schema mismatch vs reference\n{prices.schema}\n{ref.schema}",
              file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    prices.write_parquet(args.out)
    print(f"wrote {args.out} ({prices.height:,} rows)")
    for a in anomalies:
        print(f"NOTE: {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
