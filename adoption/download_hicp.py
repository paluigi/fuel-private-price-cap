"""Download Eurostat HICP data for Italy, ECOICOP v2 class CP0722
("Fuels and lubricants for personal transport equipment") and its
children CP07221 (diesel) and CP07222 (petrol).

Two data flows (author instruction D12):
  prc_hicp_iw   - HICP item weights (annual reference year); the 2026
                  per-fuel weights replace the former 50/50 assumption
  prc_hicp_minr - monthly HICP: index, monthly rate of change, annual
                  rate of change (official validation of our
                  reference-day estimates)

Cached and idempotent: raw JSON responses are stored in data/external/
and reused unless --refresh. Parsed outputs:
  eurostat_hicp_weights_2026.csv  (per-fuel item weights, per mille)
  eurostat_hicp_monthly.csv       (all units x months)

Usage (repo root): uv run python -I adoption/download_hicp.py [--refresh]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import polars as pl

EXT = Path(__file__).resolve().parent.parent / "data" / "external"
GEO = "IT"
CODES = ["CP0722", "CP07221", "CP07222", "CP07223", "CP07224"]
LABELS = {"CP0722": "class", "CP07221": "diesel", "CP07222": "petrol",
          "CP07223": "other fuels", "CP07224": "lubricants"}
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
WEIGHT_YEAR = 2026


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except Exception:  # noqa: BLE001 - fall back to curl
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            subprocess.run(["curl", "-sSfL", "-o", tf.name, url], check=True)
            return json.loads(Path(tf.name).read_text())


def long_table(d: dict) -> list[dict]:
    """Flatten a Eurostat JSON-stat response into labelled rows."""
    dims = list(d["dimension"])
    idx = d["dimension"]
    cat = {k: idx[k]["category"]["index"] for k in dims}
    lab = {k: idx[k]["category"]["label"] for k in dims}
    inv = {k: {v: kk for kk, v in cat[k].items()} for k in dims}
    sizes = {k: len(cat[k]) for k in dims}
    out = []
    for flat, val in d["value"].items():
        pos = int(flat)
        coord = {}
        for k in reversed(dims):
            coord[k] = pos % sizes[k]
            pos //= sizes[k]
        row = {k: inv[k][coord[k]] for k in dims}
        row["value"] = val
        for k in dims:
            row[f"{k}_label"] = lab[k].get(row[k], "")
        out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    EXT.mkdir(parents=True, exist_ok=True)

    co = "&".join(f"coicop18={c}" for c in CODES)

    # ---- weights: prc_hicp_iw --------------------------------------------
    iw_path = EXT / f"eurostat_prc_hicp_iw_{GEO}.json"
    if args.refresh or not iw_path.exists():
        iw_path.write_text(json.dumps(fetch_json(
            f"{BASE}/prc_hicp_iw?format=JSON&lang=EN&geo={GEO}&{co}"
        )))
    iw = pl.DataFrame(long_table(json.loads(iw_path.read_text())))
    iw = iw.filter(pl.col("statinfo") == "IW")
    w26 = (
        iw.filter(pl.col("time").cast(pl.Int32) == WEIGHT_YEAR)
        .select(
            code=pl.col("coicop18"),
            item=pl.col("coicop18").replace_strict(LABELS),
            weight_permille=pl.col("value"),
        )
        .sort("item")
    )
    w26.write_csv(EXT / "eurostat_hicp_weights_2026.csv")
    print(f"== HICP {WEIGHT_YEAR} item weights (per mille), geo={GEO} ==")
    print(w26)
    tot = w26.filter(pl.col("item") == "class")["weight_permille"][0]
    ch = w26.filter(pl.col("item") != "class")["weight_permille"].sum()
    assert abs(tot - ch) < 0.02, f"class weight {tot} != children sum {ch}"

    # ---- monthly: prc_hicp_minr -------------------------------------------
    mi_path = EXT / f"eurostat_prc_hicp_minr_{GEO}.json"
    if args.refresh or not mi_path.exists():
        mi_path.write_text(json.dumps(fetch_json(
            f"{BASE}/prc_hicp_minr?format=JSON&lang=EN&geo={GEO}&{co}"
            "&sinceTimePeriod=2025-01"
        )))
    mi = pl.DataFrame(long_table(json.loads(mi_path.read_text())))
    mi = mi.select(
        code=pl.col("coicop18"),
        item=pl.col("coicop18").replace_strict(LABELS),
        unit=pl.col("unit"),
        month=pl.col("time"),
        value=pl.col("value"),
    ).sort("item", "unit", "month")
    mi.write_csv(EXT / "eurostat_hicp_monthly.csv")
    print("\n== HICP monthly (2026-08 onward) ==")
    print(mi.filter(pl.col("month") >= "2026-08"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
