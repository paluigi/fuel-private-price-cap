"""Download and prepare the Brent crude + USD/EUR series for the counterfactual.

Sources (FRED CSV endpoints, full history):
  DCOILBRENTEU — Crude Oil Prices: Brent - Europe (EIA), USD per barrel.
  DEXUSEU      — U.S. Dollars to One Euro (ECB reference rate), USD per EUR.

Counterfactual regressor: brent_eur = brent_usd / usd_per_eur (EUR/bbl).
Business-day files keep the source frequency; a calendar-day variant
forward-fills weekends/holidays so it joins one-to-one with the daily
fuel-price calendar (documented: oil is assumed constant on non-TARGET days).

Fallbacks if FRED is unreachable: EIA API for Brent, ECB eurofxref-hist.csv
for USD/EUR (not implemented — FRED endpoints are stable).

Outputs (committed):
  data/external/brent_usd_daily.csv          full history, as downloaded
  data/external/usd_eur_daily.csv            full history, as downloaded
  adoption/output/tables/oil_fx_daily.csv         business days, window
  adoption/output/tables/oil_fx_daily_ffill.csv   calendar days, forward-filled
"""

from __future__ import annotations

import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SERIES = {
    "DCOILBRENTEU": ("brent_usd", "USD/bbl"),
    "DEXUSEU": ("usd_per_eur", "USD/EUR"),
}


def fetch(url: str, attempts: int = 3, timeout: int = 60) -> bytes:
    """GET with retries; falls back to curl (urllib is blocked on some hosts)."""
    last_err: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            print(f"  attempt {i}/{attempts} failed: {e}", flush=True)
    # curl fallback (different TLS/proxy stack)
    try:
        out = subprocess.run(
            ["curl", "-sS", "-f", "-m", str(timeout), "-A", "Mozilla/5.0", url],
            capture_output=True, check=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  curl fallback failed: {e}", flush=True)
        raise RuntimeError(
            f"download failed after {attempts} attempts: {url}"
        ) from last_err or e


def download_raw(force: bool = False) -> dict[str, Path]:
    """Fetch the two FRED CSVs into data/external/.

    Existing non-empty files are kept unless force=True (pass --refresh).
    Note: on hosts where urllib/curl-within-Python are flaky, seed the files
    with `curl -o` from the shell first and run this script without --refresh.
    """
    config.EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for series_id, (name, _unit) in SERIES.items():
        dest = config.EXTERNAL_DIR / f"{name}_daily.csv"
        if force or not dest.exists() or dest.stat().st_size == 0:
            url = FRED_CSV.format(series_id)
            print(f"downloading {series_id} -> {dest}", flush=True)
            dest.write_bytes(fetch(url))
        else:
            print(f"using existing {dest}", flush=True)
        paths[series_id] = dest
    return paths


def load_fred(path: Path, value_name: str) -> pl.DataFrame:
    """Parse a fredgraph.csv: first column date, second value ('.' = missing).

    DEXUSEU is the Fed H.10 series: no publication on US federal holidays;
    EIA Brent occasionally skips a day. Both gaps are forward-filled later.
    """
    df = pl.read_csv(path, infer_schema_length=0)  # read all as strings
    df.columns = ["date", "value"]
    return (
        df.with_columns(
            date=pl.col("date").str.to_date("%Y-%m-%d"),
            **{value_name: pl.when(pl.col("value") == ".")
               .then(None)
               .otherwise(pl.col("value")).cast(pl.Float64)},
        )
        .filter(pl.col("date").is_not_null())
        .select("date", value_name)
        .sort("date")
    )


def main() -> None:
    force = "--refresh" in sys.argv
    raw = download_raw(force=force)
    brent = load_fred(raw["DCOILBRENTEU"], "brent_usd")
    fx = load_fred(raw["DEXUSEU"], "usd_per_eur")

    # window + EUR conversion on days where both series are published
    daily = (
        brent.join(fx, on="date", how="inner")
        .filter(
            (pl.col("date") >= config.SERIES_FROM)
            & (pl.col("date") <= config.ANALYSIS_TO)
        )
        .sort("date")
        .with_columns(brent_eur=pl.col("brent_usd") / pl.col("usd_per_eur"))
    )
    daily.write_csv(config.OIL_FX_CSV)

    # calendar-day variant: forward-fill onto the daily fuel-price calendar;
    # drop null-value rows first so holidays inherit the last published values
    calendar = pl.date_range(
        config.SERIES_FROM, config.ANALYSIS_TO, "1d", eager=True
    ).alias("date").to_frame()
    ffill = (
        calendar.join_asof(
            daily.drop_nulls(["brent_usd", "usd_per_eur", "brent_eur"]),
            on="date", strategy="backward",
        )
        .sort("date")
    )
    ffill.write_csv(config.OIL_FX_FFILL_CSV)

    n_null_fx = daily.filter(pl.col("usd_per_eur").is_null()).height
    n_ffill_null = ffill.filter(pl.col("brent_eur").is_null()).height
    print(f"\nbusiness days: {daily.height} "
          f"({daily['date'].min()} .. {daily['date'].max()})")
    print(f"nulls in window: brent {daily.filter(pl.col('brent_usd').is_null()).height}, "
          f"fx {n_null_fx} (US-holiday gaps, forward-filled in calendar file)")
    print(f"calendar days: {ffill.height}, rows with no oil yet (leading): {n_ffill_null}")
    print(f"last brent_eur: {daily['brent_eur'][-1]:.3f} EUR/bbl "
          f"on {daily['date'][-1]}")
    print(f"wrote {config.OIL_FX_CSV} and {config.OIL_FX_FFILL_CSV}")


if __name__ == "__main__":
    main()
