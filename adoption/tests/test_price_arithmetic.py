"""Unit tests for the price/tax/threshold arithmetic (Step 04).

Run: cd adoption && uv run python -I tests/test_price_arithmetic.py
Exit code 0 = all assertions pass.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

VAT = 1.22


def test_threshold_steps() -> None:
    assert config.cap_threshold("Benzina", dt.date(2026, 9, 27)) == 2.000
    assert config.cap_threshold("Benzina", dt.date(2026, 9, 28)) == 2.000
    assert config.cap_threshold("Benzina", dt.date(2026, 10, 31)) == 2.000
    assert config.cap_threshold("Gasolio", dt.date(2026, 9, 27)) == 2.200
    assert config.cap_threshold("Gasolio", dt.date(2026, 9, 28)) == 2.200
    assert config.cap_threshold("Gasolio", dt.date(2026, 10, 5)) == 2.200
    assert config.cap_threshold("Gasolio", dt.date(2026, 10, 6)) == 2.261
    assert config.cap_threshold("Gasolio", dt.date(2026, 10, 27)) == 2.261
    assert config.cap_threshold("Gasolio", dt.date(2026, 10, 28)) == 2.212
    assert config.cap_threshold("Gasolio", dt.date(2026, 10, 31)) == 2.212
    # mechanical translation identities
    assert abs(2.200 + 0.05 * VAT - 2.261) < 1e-12
    assert abs((2.261 - 0.04 * VAT) - 2.2122) < 1e-12  # -> 2.212 on 3-dp grid


def test_strict_rule_boundaries() -> None:
    for thr in (2.000, 2.200, 2.261, 2.212):
        assert round(thr - 0.001, 3) < thr          # highest compliant price
        assert not (thr < thr)                       # exact ceiling NOT compliant
    assert 1.999 < 2.000 and not (2.000 < 2.000)
    assert 2.199 < 2.200 and not (2.200 < 2.200)
    assert 2.260 < 2.261 and not (2.261 < 2.261)
    assert 2.211 < 2.212 and not (2.212 < 2.212)


def test_tax_calendar() -> None:
    import polars as pl

    tax = pl.read_parquet(config.TAX_PARQUET).sort("application_date")
    cal = (
        pl.date_range(dt.date(2026, 1, 1), dt.date(2026, 11, 5), "1d", eager=True)
        .alias("date")
        .to_frame()
        .join_asof(tax, left_on="date", right_on="application_date",
                   strategy="backward")
    )
    at = lambda d, c: cal.filter(pl.col("date") == dt.date(2026, *d))[c][0] / 1000.0  # noqa: E731
    assert abs(at((1, 1), "gasolio_tax") - 0.6729) < 1e-9
    assert abs(at((3, 18), "gasolio_tax") - 0.6729) < 1e-9   # day before spring cut
    assert abs(at((3, 19), "gasolio_tax") - 0.4729) < 1e-9   # -20 c/l spring cut
    assert abs(at((7, 3), "benzina_tax") - 0.6229) < 1e-9
    assert abs(at((7, 4), "benzina_tax") - 0.6729) < 1e-9    # +5 both fuels
    assert abs(at((7, 28), "gasolio_tax") - 0.5329) < 1e-9   # diesel discount
    assert abs(at((10, 5), "gasolio_tax") - 0.6229) < 1e-9
    assert abs(at((10, 6), "gasolio_tax") - 0.6729) < 1e-9   # post-event step 1
    assert abs(at((10, 27), "benzina_tax") - 0.6729) < 1e-9
    assert abs(at((10, 28), "gasolio_tax") - 0.6329) < 1e-9  # post-event step 2
    # NO petrol change in the outcome period
    petrol = cal.filter(pl.col("date") >= dt.date(2026, 9, 28))["benzina_tax"]
    assert petrol.n_unique() == 1 and abs(petrol[0] / 1000.0 - 0.6729) < 1e-9


def test_net_price_roundtrip() -> None:
    # net = gross/1.22 - excise  =>  gross = (net + excise) * 1.22
    for gross, excise in ((2.000, 0.6729), (2.199, 0.6729), (1.999, 0.6729)):
        net = gross / VAT - excise
        assert abs((net + excise) * VAT - gross) < 1e-12
    # the 6 Oct ceiling translation: +5 c/l excise -> +6.1 c/l gross
    assert abs(0.05 * VAT - 0.061) < 1e-12


if __name__ == "__main__":
    test_threshold_steps()
    test_strict_rule_boundaries()
    test_tax_calendar()
    test_net_price_roundtrip()
    print("all price-arithmetic tests passed")
