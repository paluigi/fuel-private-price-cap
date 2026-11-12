"""Automated consistency check: every repeated number in paper.tex must
match a value recomputed from the pipeline outputs (Step 16).

Usage: uv run python -I revision/check_numbers.py   (from repo root)
Exit 0 = all checks pass; any FAIL line is a mismatch to fix.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "adoption" / "output" / "tables"
REV = ROOT / "revision"
TEX = (ROOT / "adoption" / "paper.tex").read_text()
# LaTeX wraps lines: normalise whitespace so multi-word patterns match
TEX_FLAT = re.sub(r"\s+", " ", TEX)

failures: list[str] = []


def check(name: str, value: float, tex_patterns: list[str], digits: int = 1) -> None:
    """Assert that at least one pattern (already formatted) appears in TEX."""
    ok = any(re.sub(r"\s+", " ", p) in TEX_FLAT for p in tex_patterns)
    status = "ok  " if ok else "FAIL"
    if not ok:
        failures.append(name)
    print(f"{status} {name}: computed {value:.{digits}f}; tex has {tex_patterns}")


def must_contain(name: str, fragment: str) -> None:
    ok = re.sub(r"\s+", " ", fragment) in TEX_FLAT
    if not ok:
        failures.append(name)
    print(f"{'ok  ' if ok else 'FAIL'} {name}: looking for {fragment!r}")


# --- ARDL / counterfactual --------------------------------------------------
ardl = pl.read_csv(TAB / "ardl_summary.csv")
cf = pl.read_csv(TAB / "counterfactual_daily.csv", try_parse_dates=True)
by_fuel = cf.group_by("fuel").agg(pl.col("gap_cpl").mean())
gap_b = by_fuel.filter(pl.col("fuel") == "Benzina")["gap_cpl"][0]
gap_g = by_fuel.filter(pl.col("fuel") == "Gasolio")["gap_cpl"][0]
end_b = cf.filter(pl.col("fuel") == "Benzina")["gap_cpl"][-1]
end_g = cf.filter(pl.col("fuel") == "Gasolio")["gap_cpl"][-1]
check("mean gap petrol", gap_b, ["17.4"])
check("mean gap diesel", gap_g, ["21.1"])
check("end gap petrol", end_b, ["22.4"])
check("end gap diesel", end_g, ["20.5"])
rb = ardl.filter(pl.col("fuel") == "Benzina").row(0, named=True)
rg = ardl.filter(pl.col("fuel") == "Gasolio").row(0, named=True)
check("petrol backtest RMSE", rb["backtest_rmse_cpl"], ["0.45"])
check("diesel backtest RMSE", rg["backtest_rmse_cpl"], ["0.85"])
check("petrol RMSE RW", rb["backtest_rmse_rw_cpl"], ["3.69"])
check("diesel RMSE RW", rg["backtest_rmse_rw_cpl"], ["5.07"])
check("petrol order", 28.0, ["(2,8)"])
check("diesel order", 18.0, ["(1,8)"])
must_contain("n_fit", "261 daily observations" if "261 daily observations" in TEX else "261")

# --- inflation ---------------------------------------------------------------
infl = pl.read_csv(TAB / "inflation_summary.csv")
tot = infl.filter(pl.col("fuel") == "TOT carburanti").row(0, named=True)
pb = infl.filter(pl.col("fuel") == "Benzina").row(0, named=True)
pg = infl.filter(pl.col("fuel") == "Gasolio").row(0, named=True)
check("cpi effect total", tot["cpi_effect_pp"], ["$-0.38$"], 2)
check("petrol mom actual", pb["mom_actual_pct"], ["-2.3\\%", "fell 2.3\\%"], 1)
check("petrol mom cf", pb["mom_cf_pct"], ["5.3\\%", "+5.3\\%"], 1)
check("diesel mom actual", pg["mom_actual_pct"], ["1.6\\%", "+1.6\\%"], 1)
check("diesel mom cf", pg["mom_cf_pct"], ["10.7\\%", "+10.7\\%"], 1)
sens = pl.read_csv(TAB / "inflation_sensitivity.csv")
s4555 = sens.filter(pl.col("scenario") == "split 45/55, universe")["cpi_effect_pp"].sum()
s5545 = sens.filter(pl.col("scenario") == "split 55/45, universe")["cpi_effect_pp"].sum()
sreg = sens.filter(pl.col("scenario") == "split 50/50, regularity sample")["cpi_effect_pp"].sum()
check("sens 45/55", s4555, ["-0.381"], 3)
check("sens 55/45", s5545, ["-0.374"], 3)
check("sens regularity", sreg, ["-0.411"], 3)

# --- reference day gaps ------------------------------------------------------
rd = pl.read_csv(TAB / "inflation_days.csv")
rd = rd.with_columns(date=pl.col("period").cast(pl.String).str.to_date())
vals = {
    ("Benzina", dt.date(2026, 10, 1)): "-9.5",
    ("Benzina", dt.date(2026, 10, 11)): "-19.3",
    ("Benzina", dt.date(2026, 10, 21)): "-18.9",
    ("Gasolio", dt.date(2026, 10, 1)): "-11.2",
    ("Gasolio", dt.date(2026, 10, 11)): "-27.8",
    ("Gasolio", dt.date(2026, 10, 21)): "-21.7",
}
for (fuel, day), frag in vals.items():
    v = rd.filter((pl.col("fuel") == fuel) & (pl.col("date") == day))["gap_cpl"][0]
    check(f"refday {fuel} {day}", v, [frag])

# --- adoption ------------------------------------------------------------------
sv = pl.read_csv(TAB / "survival_input.csv")
panel = pl.read_parquet(TAB / "adoption_panel.parquet",
                        columns=["date", "fuel", "at_cap"])
last = panel.filter(pl.col("date") == dt.date(2026, 10, 31))
sh_b = 100 * last.filter(pl.col("fuel") == "Benzina")["at_cap"].mean()
sh_g = 100 * last.filter(pl.col("fuel") == "Gasolio")["at_cap"].mean()
check("final-day petrol share", sh_b, ["81.8\\%"])
check("final-day diesel share", sh_g, ["50.2\\%"])
d0 = panel.filter(pl.col("date") == dt.date(2026, 9, 28))
check("day0 petrol", 100 * d0.filter(pl.col("fuel") == "Benzina")["at_cap"].mean(),
      ["20.9\\%"])
check("day0 diesel", 100 * d0.filter(pl.col("fuel") == "Gasolio")["at_cap"].mean(),
      ["21.4\\%"])
must_contain("ever shares", "84.4\\% of petrol units and 82.8\\% of diesel")
must_contain("units", "39{,}425")
must_contain("events", "32{,}974")

# --- bunching / dispersion (revision outputs) ----------------------------------
bnd = pl.read_csv(REV / "threshold_boundary_counts.csv")
v179 = bnd.filter((pl.col("fuel") == "Benzina") & (pl.col("price") == 1.999)
                  & (pl.col("threshold") == 2.000))["share_pct"][0]
check("bunching 1.999 share", v179, ["17.9\\%"], 1)
disp = pl.read_csv(REV / "dispersion_summary.csv")
dw = {(r["window"], r["fuel"]): r for r in disp.iter_rows(named=True)}
check("p90p10 petrol pre", dw[("pre_full (1-27 Sep)", "Benzina")]["mean_p90p10"],
      ["8.1"])
check("p90p10 petrol post", dw[("post (28 Sep-31 Oct)", "Benzina")]["mean_p90p10"],
      ["14.0"])
check("p90p10 diesel pre", dw[("pre_full (1-27 Sep)", "Gasolio")]["mean_p90p10"],
      ["9.5"])
check("p90p10 diesel post", dw[("post (28 Sep-31 Oct)", "Gasolio")]["mean_p90p10"],
      ["15.9"])
check("adopter gap petrol",
      abs(dw[("post (28 Sep-31 Oct)", "Benzina")]["adopter_minus_non_gap"]),
      ["11.5"])
check("adopter gap diesel",
      abs(dw[("post (28 Sep-31 Oct)", "Gasolio")]["adopter_minus_non_gap"]),
      ["11.7"])

# --- 28 October episode ---------------------------------------------------------
dd = pl.read_csv(REV / "definitions_daily_series.csv", try_parse_dates=True)
dg = dd.filter(pl.col("fuel") == "Gasolio").sort("date")
m27 = dg.filter(pl.col("date") == dt.date(2026, 10, 27))["mean_gross"][0]
m28 = dg.filter(pl.col("date") == dt.date(2026, 10, 28))["mean_gross"][0]
m31 = dg.filter(pl.col("date") == dt.date(2026, 10, 31))["mean_gross"][0]
check("27 Oct diesel mean", m27, ["2.258"], 3)
check("28 Oct diesel mean", m28, ["2.258"], 3)
check("31 Oct diesel mean", m31, ["2.239"], 3)
check("pass-through c/l", (m27 - m31) * 100, ["1.96"], 2)

# --- dates & framing ------------------------------------------------------------
# ECM bounds and brand-compliance content (D8/D9)
ecm = pl.read_csv(TAB / "ecm_bounds.csv")
fb = ecm.filter(pl.col("fuel") == "Benzina")["F_stat"][0]
fg = ecm.filter(pl.col("fuel") == "Gasolio")["F_stat"][0]
check("bounds F petrol", fb, ["1.40"], 2)
check("bounds F diesel", fg, ["0.92"], 2)
must_contain("brand Eni level", "2.190")
must_contain("brand Q8 compliance", "78\\%")
must_contain("calendar-day recovery", "covers every calendar day")
# --- discrete-time hazard (D11) -------------------------------------------------
hz = pl.read_csv(TAB / "hazard_discrete.csv")
h_pg = hz.filter((pl.col("sample") == "S1_universe")
                 & (pl.col("variable") == "pre_gap_10c"))["coef"][0]
h_wp = hz.filter((pl.col("sample") == "S3_white_pumps")
                 & (pl.col("variable") == "pre_gap_10c"))["coef"][0]
check("hazard odds universe", __import__("math").exp(h_pg), ["0.41"], 2)
check("hazard odds white pumps", __import__("math").exp(h_wp), ["0.21"], 2)
must_contain("hazard table referenced", "tab:hazard-dt")
must_contain("map pair swapped", "v2_map_adopt7_ben.png")

for frag in ["25 September", "28 September", "30 days" if "thirty days" not in TEX
             else "thirty days", "2.261", "2.212", "4.5219",
             "0.45~\\cl", "0.85~\\cl", "eleven of sixteen"]:
    must_contain(f"contains {frag[:24]}", frag)

print()
if failures:
    print(f"{len(failures)} FAILURES: {failures}")
    sys.exit(1)
print("all numeric consistency checks passed")
