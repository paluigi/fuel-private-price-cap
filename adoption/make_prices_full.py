"""Concatenate the H1-2026 MIMIT archive with the H2 MongoDB cache.

Builds ``data/prices_full_2026.parquet`` = prices_archive (Jan-Jun, from
``build_archive_prices.py``) + prices_raw (Jul-Nov cache), the input the
adoption pipeline reads (``config.PRICES_PARQUET``) since decision D6.

Usage (repository root): uv run python -I adoption/make_prices_full.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402


def main() -> int:
    arch = pl.read_parquet(config.PRICES_ARCHIVE)
    raw = pl.read_parquet(config.PRICES_RAW)
    if arch.schema != raw.schema:
        print(f"ERROR: schema mismatch\n{arch.schema}\n{raw.schema}", file=sys.stderr)
        return 2
    overlap = arch["date"].max(), raw["date"].min()
    if overlap[0] >= overlap[1]:
        print(f"ERROR: date ranges overlap ({overlap[0]} >= {overlap[1]})",
              file=sys.stderr)
        return 2
    full = pl.concat([arch, raw.select(*arch.columns)], how="vertical").sort(
        "date", "id_impianto", "fuel"
    )
    dup = (
        full.group_by(["id_impianto", "date", "fuel"]).len().filter(pl.col("len") > 1)
    )
    if dup.height:
        print(f"ERROR: {dup.height} duplicate keys after concat", file=sys.stderr)
        return 2
    full.write_parquet(config.PRICES_PARQUET)
    print(
        f"wrote {config.PRICES_PARQUET}: {full.height:,} rows, "
        f"{full['date'].min()} .. {full['date'].max()}, "
        f"{full['date'].n_unique()} extract days, "
        f"{full['id_impianto'].n_unique():,} stations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
