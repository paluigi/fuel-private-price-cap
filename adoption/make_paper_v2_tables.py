"""Generate the v2 paper's macro tables and appendix tables (Step 15).

Main (paper_v2_tables.tex):
  tab:data    data/sample definitions (computed counts)
  tab:ardl    ARDL specification, backtests and October gaps
  tab:inflation  reference-day inflation results with sensitivities

Appendix (paper_v2_appendix.tex):
  tab:es-leads   event-study coefficients incl. pre-period leads
  tab:spec-range specification grid + fit-window/sample/Brent scenarios
  tab:bt-origins expanding-origin backtests
  tab:boundary   exact-boundary and bunching-bin counts
  tab:endings    price-ending frequencies pre/post

Run from adoption/: uv run python make_paper_v2_tables.py
Sources: output/tables/* (R + Python pipeline), revision/*.csv (Step 04/11).
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

TAB = config.OUT_DIR / "tables"
REV = Path(__file__).resolve().parent.parent / "revision"
FUEL_EN = {"Benzina": "Petrol", "Gasolio": "Diesel"}
HEAD = (
    "% Auto-generated: do not edit by hand.\n"
    "% Sources: output/tables/{ardl,inflation}*_summary/sensitivity.csv,\n"
    "% counterfactual_daily.csv, backtest_origins.csv, spec_robustness.csv,\n"
    "% spec_range.csv, cf_bands_bootstrap.csv, event_study_coefs.csv,\n"
    "% revision/{threshold_boundary_counts,price_endings_*,dispersion_summary}.csv\n\n"
)

ardl = pl.read_csv(TAB / "ardl_summary.csv")
infl = pl.read_csv(TAB / "inflation_summary.csv")
sens = pl.read_csv(TAB / "inflation_sensitivity.csv")
cf = pl.read_csv(TAB / "counterfactual_daily.csv", try_parse_dates=True)

# ------------------------------------------------------------------ tab:data
sv = pl.read_csv(TAB / "survival_input.csv")
fd = pl.read_csv(TAB / "fuel_daily_prices.csv", try_parse_dates=True)
full = pl.read_parquet(config.PRICES_PARQUET, columns=["date", "id_impianto"])
data_rows = [
    "Price communications (rows) & 12.4\\,million & 1 Jan--5 Nov 2026 \\\\",
    f"Stations reporting prices & {full['id_impianto'].n_unique():,} & unique MIMIT plant IDs \\\\".replace(",", "\\,"),
    f"Extract days & {full['date'].n_unique():,} & none 16--17 Oct \\\\".replace(",", "\\,"),
    f"Station--fuel units (micro panel) & {sv.height:,} & 28 Sep--31 Oct \\\\".replace(",", "\\,"),
    f"Estimation observations & {ardl['n_fit'][0]} per fuel & 2 Jan--27 Sep, after lags \\\\",
    "Reference days & 3 per month & 1st, 11th, 21st \\\\",
    "Ceilings (petrol) & 2.000 & strict, from 28 Sep \\\\",
    "Ceilings (diesel) & 2.200 / 2.261 / 2.212 & from 28 Sep / 6 Oct / 28 Oct \\\\",
]

# ----------------------------------------------------------------- tab:ardl
ardl_rows = []
for r in ardl.iter_rows(named=True):
    f = FUEL_EN[r["fuel"]]
    c = cf.filter(pl.col("fuel") == r["fuel"])
    mean_gap = c["gap_cpl"].mean()
    end_gap = c["gap_cpl"][-1]
    ardl_rows.append(
        f"{f} & ({r['p']},{r['q']}) & {r['n_fit']} & "
        f"{r['backtest_rmse_cpl']:.2f} & {r['backtest_rmse_rw_cpl']:.2f} & "
        f"{r['backtest_bias_cpl']:+.2f} & ${mean_gap:.1f}$ & ${end_gap:.1f}$ \\\\"
    )

# ------------------------------------------------------------- tab:inflation
def fmt_pm(x, digits=2):
    return f"${x:+.{digits}f}$"

infl_rows = []
for r in infl.iter_rows(named=True):
    f = FUEL_EN.get(r["fuel"], "Motor fuels (combined)")
    infl_rows.append(
        f"{f} & {fmt_pm(r['mom_actual_pct'])} & {fmt_pm(r['mom_cf_pct'])} & "
        f"{fmt_pm(r['cap_effect_pp'], 1)} & {fmt_pm(r['cpi_effect_pp'], 2)} \\\\"
    )
infl_rows.append("\\midrule")
scen_label = {
    "split 45/55, universe": "Weight split 45/55 (petrol/diesel)",
    "split 55/45, universe": "Weight split 55/45 (petrol/diesel)",
    "split 50/50, regularity sample": "Regularity-filtered stations (50/50)",
}
for lbl in scen_label:
    rows_ = sens.filter(pl.col("scenario") == lbl)
    tot_pp = rows_["cpi_effect_pp"].sum()
    infl_rows.append(
        f"\\multicolumn{{4}}{{l}}{{\\emph{{{scen_label[lbl]}}}}} & {fmt_pm(tot_pp, 2)} \\\\"
    )

main_tex = f"""{HEAD}% ---------- main tables (v2) ----------
\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Data and sample definitions}}
\\label{{tab:data}}
\\begin{{tabular}}{{lll}}
\\toprule
Item & Value & Notes \\\\
\\midrule
{chr(10).join(data_rows)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Oil pass-through models: selection, out-of-sample fit and October price gaps}}
\\label{{tab:ardl}}
\\begin{{tabular}}{{lccccccc}}
\\toprule
 & Order & $N$ & \\multicolumn{{3}}{{c}}{{Placebo backtest 14--27 Sep (c/l)}} &
 \\multicolumn{{2}}{{c}}{{Gap, 28 Sep--31 Oct (c/l)}} \\\\
\\cmidrule(lr){{4-6}}\\cmidrule(lr){{7-8}}
 & (BIC) & & RMSE & RMSE RW & Bias & Mean & 31 Oct \\\\
\\midrule
{chr(10).join(ardl_rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Dependent variable: log national mean net-of-tax price
(self-service, roadside); regressors: own lags and contemporaneous plus
lagged log Brent in \\euro. Estimation 2 Jan--27 Sep 2026 (261 observations
after lags); BIC over $p\\in[0,21]$, $q\\in[7,21]$. Backtest: refit to
13 Sep, recursive projection over 14--27 Sep, compared with a no-change
random walk. Gap: actual minus counterfactual gross price, days available
(32 of 34; no extracts 16--17 Oct).
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Reference-day inflation: actual versus no-cap, and the estimated contribution to headline NIC inflation}}
\\label{{tab:inflation}}
\\begin{{tabular}}{{lcccc}}
\\toprule
 & \\multicolumn{{3}}{{c}}{{Sep--Oct change (\\%)}} & Contribution \\\\
\\cmidrule(lr){{2-4}}
 & Actual & No cap & Difference & (pp of NIC) \\\\
\\midrule
{chr(10).join(infl_rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Month-on-month changes over the 1st/11th/21st reference days,
national mean gross prices, equal station weights. Contributions use the
NIC 2026 weight of ECOICOP 07.2.2 (4.5219\\%, verified from ISTAT's
published weighting structure) split evenly between petrol and diesel.
September no-cap prices equal observed prices by construction.
\\end{{table}}
"""
Path("paper_v2_tables.tex").write_text(main_tex)
print("wrote paper_v2_tables.tex")

# ------------------------------------------------------------------ appendix
es = pl.read_csv(TAB / "event_study_coefs.csv")
es_rows = "\n".join(
    f"Day {r['event_time']:+d} & {r['coef']:+.3f}{r['stars']} & {r['se']:.3f} \\\\"
    for r in es.iter_rows(named=True)
)

rob = pl.read_csv(TAB / "spec_robustness.csv")
rng = pl.read_csv(TAB / "spec_range.csv")
bt = pl.read_csv(TAB / "backtest_origins.csv", try_parse_dates=True)

VLABEL = {
    "V1_baseline": "No oil-lag floor",
    "V2_minq2": "Min 2 oil lags",
    "V3_minq5": "Min 5 oil lags",
    "V4_minq7": "Min 7 oil lags (main)",
    "V5_dl_only": "Distributed lag only",
    "V6_ar_only": "Autoregression only (no oil)",
}
spec_rows = []
for f in ("Benzina", "Gasolio"):
    for v, lab in VLABEL.items():
        r = rob.filter((pl.col("fuel") == f) & (pl.col("variant") == v)).row(0, named=True)
        order = f"({r['p']},{r['q']})" if r["q"] is not None else f"({r['p']},.)"
        spec_rows.append(
            f"{FUEL_EN[f]} & {lab} & {order} & {r['backtest_rmse_cpl']:.2f} & "
            f"${r['mean_gap_cpl']:+.1f}$ & ${r['cpi_effect_pp']:+.3f}$ \\\\"
        )
    spec_rows.append("\\midrule")
for r in rng.iter_rows(named=True):
    # escape % in scenario labels (e.g. "Brent +5% post-cap"): a raw %
    # comments out the rest of the row including its terminator
    label = r["variant"].replace("%", "\\%")
    spec_rows.append(
        f"{FUEL_EN[r['fuel']]} & {label} & ({r['p']},{r['q']}) & -- & "
        f"${r['mean_gap_cpl']:+.1f}$ & ${r['cpi_effect_pp']:+.3f}$ \\\\"
    )

bt_rows = "\n".join(
    f"{FUEL_EN[r['fuel']]} & {r['origin'].strftime('%d %b')} & {r['horizon']} & "
    f"{r['rmse_ardl_cpl']:.2f} & {r['rmse_rw_cpl']:.2f} & {r['bias_ardl_cpl']:+.2f} \\\\"
    for r in bt.iter_rows(named=True)
    if r["rmse_ardl_cpl"] is not None
)

bnd = pl.read_csv(REV / "threshold_boundary_counts.csv")
bnd_rows = "\n".join(
    f"{FUEL_EN.get(r['fuel'], r['fuel'])} & {r['threshold']} & "
    f"{r['price']} & {r['n_obs']:,} & {r['share_pct']:.2f}\\% \\\\".replace(",", "\\,")
    for r in bnd.iter_rows(named=True)
)

end_rows = []
for tag, lab in (("pre", "Pre-cap (1--27 Sep)"), ("post", "Post-cap (28 Sep--31 Oct)")):
    e = pl.read_csv(REV / f"price_endings_{tag}.csv")
    for f in ("Benzina", "Gasolio"):
        top = (e.filter(pl.col("fuel") == f)
               .sort("pct_of_fuel", descending=True).head(3))
        cells = " & ".join(
            f".{int(round(100 * r['ending'])):02d}: {r['pct_of_fuel']:.1f}\\%"
            for r in top.iter_rows(named=True))
        end_rows.append(f"{lab} & {FUEL_EN[f]} & {cells} \\\\")

app_tex = f"""{HEAD}% ---------- appendix tables (v2) ----------
\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Station-fixed-effects event study: adoption below the ceiling (leads and lags)}}
\\label{{tab:es-leads}}
\\begin{{tabular}}{{lcc}}
\\toprule
Event time & $\\hat\\beta_k$ & Std.~error \\\\
\\midrule
{es_rows}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Dependent variable: indicator for pricing below the ceiling;
station--fuel fixed effects; gestore-clustered errors; day $-1$
(27 September) omitted.
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\footnotesize
\\caption{{Specification grid and scenarios: October mean gaps and implied NIC effects}}
\\label{{tab:spec-range}}
\\begin{{tabular}}{{llcccc}}
\\toprule
 & & Order & Backtest & Mean gap & NIC \\\\
 & & (BIC) & RMSE (c/l) & (c/l) & effect (pp) \\\\
\\midrule
{chr(10).join(spec_rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Upper block: oil-lag floors and distributed-lag /
autoregression-only extremes (all re-selected by BIC on the extended
window, max lag 21). Lower block: fit window, sample and Brent-path
scenarios. The autoregression-only row is a mechanical persistence
benchmark, not an admissible no-oil counterfactual. NIC effects per fuel
use the 50/50 split.
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Expanding-origin backtests (all evaluation windows end before 28 September)}}
\\label{{tab:bt-origins}}
\\begin{{tabular}}{{llcccc}}
\\toprule
 & Origin & Horizon & RMSE & RMSE RW & Bias \\\\
 & & (days) & (c/l) & (c/l) & (c/l) \\\\
\\midrule
{bt_rows}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Models re-selected by BIC on each subsample; recursive
projection over the stated horizon; comparison against a no-change random
walk.
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Exact prices at the ceiling and in the bunching bin below it}}
\\label{{tab:boundary}}
\\begin{{tabular}}{{lllrl}}
\\toprule
Fuel & Ceiling & Price & Obs. & Share \\\\
\\midrule
{bnd_rows}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Shares within each fuel--ceiling segment; compliance is
strict, so the ceiling price itself is not compliant. The bunching bin
(one tenth of a cent below the ceiling: 1.999, 2.199, 2.260, 2.211)
concentrates up to 17.9\\% of petrol observations.
\\end{{table}}

\\begin{{table}}[htbp]
\\centering\\small
\\caption{{Most frequent price endings before and after the cap (share of observations)}}
\\label{{tab:endings}}
\\begin{{tabular}}{{lllll}}
\\toprule
Window & Fuel & \\multicolumn{{3}}{{l}}{{Top endings (cent-decimal: share)}} \\\\
\\midrule
{chr(10).join(end_rows)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
Path("paper_v2_appendix.tex").write_text(app_tex)
print("wrote paper_v2_appendix.tex")
