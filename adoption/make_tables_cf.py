"""Regenerate the counterfactual LaTeX tables from the pipeline outputs.

Reads output/tables/ardl_summary.csv and output/tables/inflation_summary.csv
(written by R/analysis_ardl.R) and output/tables/spec_robustness.csv +
spec_block_tests.csv (written by R/spec_robustness.R); rewrites
paper_tables_cf.tex, paper_tables_infl.tex and paper_appendix_ardl.tex.
Run after every data refresh.
"""
import math

import polars as pl

FUEL_EN = {"Benzina": "Petrol", "Gasolio": "Diesel",
           "TOT carburanti": "Motor fuels (combined)"}
OUT_ARDL = "paper_tables_cf.tex"
OUT_INFL = "paper_tables_infl.tex"

ardl = pl.read_csv("output/tables/ardl_summary.csv")
infl = pl.read_csv("output/tables/inflation_summary.csv")

head = (
    "% Auto-generated: do not edit by hand.\n"
    "% Source: R/analysis_ardl.R -> output/tables/{ardl,inflation}_summary.csv\n"
    "% Fit window 2026-07-01..2026-09-27; projection 2026-09-28..2026-10-31;\n"
    "% backtest window 2026-09-14..2026-09-27.\n\n"
)

# ---- table: ARDL estimates and backtest ------------------------------------
rows = []
for r in ardl.iter_rows(named=True):
    f = FUEL_EN[r["fuel"]]
    order_aic = f"({r['p']},{r['q']})"
    order = order_aic if r["order_bic"] == order_aic else f"{order_aic} / {r['order_bic']}"
    rows.append(
        f"{f} & {order} & {r['lr_elasticity']:.3f} & "
        f"{r['backtest_rmse_cpl']:.2f} & {r['backtest_rmse_rw_cpl']:.2f} & "
        f"{r['n_fit']} \\\\"
    )
ardl_table = f"""{head}\\begin{{table}}[htbp]
\\centering\\small\\setlength{{\\tabcolsep}}{{4pt}}
\\caption{{ARDL net-price models: specification and out-of-sample fit}}
\\label{{tab:ardl}}
\\begin{{tabular}}{{lccccc}}
\\toprule
 & Order ($p,q$) & Long-run elasticity & {{RMSE ARDL}} & {{RMSE random walk}} & $N$ \\\\
 & (AIC / BIC) & (net price vs Brent \\euro/bbl) & (c/l) & (c/l) & \\\\
\\midrule
{chr(10).join(rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Dependent variable: log national average net price
(self-service, stradale), daily, 1 Jul--27 Sep 2026; regressor: log Brent
in \\euro/bbl (ECB reference rate), lags as shown. The target is net of
excise and VAT by construction, so no tax dummy enters the regression.
Lag orders selected by AIC and by BIC over $(p,q)\\in[0,10]^2$ (the AIC
selection is used throughout; where the two differ both are shown).
Backtest: refit to 13 Sep, projected 14--27 Sep (pre-cap) recursively;
RMSE on the net price in c/l against a no-change random walk. See
\\cref{{sec:counterfactual}}.
\\end{{table}}

"""

# ---- table: inflation reference days ---------------------------------------
cols = ["mom_actual_pct", "mom_cf_pct", "cap_effect_pp",
        "cpi_actual_pp", "cpi_cf_pp", "cpi_effect_pp"]
rows = []
for r in infl.iter_rows(named=True):
    f = FUEL_EN[r["fuel"]]
    cells = [f"${r[c]:+.2f}$" for c in cols]
    rows.append(f"{f} & " + " & ".join(cells) + r" \\")
infl_table = f"""{head}\\begin{{table}}[htbp]
\\centering\\small\\setlength{{\\tabcolsep}}{{3pt}}
\\caption{{Month-on-month inflation on ISTAT reference days (1st, 11th, 21st): actual vs counterfactual}}
\\label{{tab:inflation}}
\\begin{{tabular}}{{lcccccc}}
\\toprule
 & \\multicolumn{{3}}{{c}}{{MoM change, Sep vs Oct avg (\\%)}} &
\\multicolumn{{3}}{{c}}{{Contribution to headline MoM CPI (pp)}} \\\\
\\cmidrule(lr){{2-4}}\\cmidrule(lr){{5-7}}
 & Actual & No cap & Difference & Actual & No cap & Difference \\\\
\\midrule
{chr(10).join(rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Monthly averages over the three ISTAT reference days
(1, 11, 21 September vs 1, 11, 21 October 2026), national mean pump prices
(self-service, stradale). Pre-cap reference days have no counterfactual
(the no-cap path is the observed path). CPI contributions use the NIC 2026
definitive weight of ECOICOP 07.2.2 ``Carburanti e lubrificanti'' (4.5219\\%
of the basket), split evenly between petrol and diesel.
\\end{{table}}

"""

open(OUT_ARDL, "w").write(ardl_table)
open(OUT_INFL, "w").write(infl_table)
print(f"wrote {OUT_ARDL} and {OUT_INFL}")

# ---- appendix table: specification robustness -------------------------------
OUT_ROBUST = "paper_appendix_ardl.tex"
rob = pl.read_csv("output/tables/spec_robustness.csv")
blk = pl.read_csv("output/tables/spec_block_tests.csv")


def p_fmt(p):
    if p < 1e-4:
        exp = math.floor(math.log10(p))
        mant = p / 10**exp
        return f"$p={mant:.1f}\\times10^{{{exp}}}$"
    return f"$p={p:.3f}$"

VARIANT_LABEL = {
    "V1_baseline": "Baseline (max 10)",
    "V2_max15": "Max 15 lags",
    "V3_minq2": "Min 2 oil lags",
    "V4_dl_only": "DL only (no AR)",
    "V5_ar_only": "AR only (no oil)",
}
VARIANT_ORDER = list(VARIANT_LABEL)

rows = []
for f in ("Benzina", "Gasolio"):
    for key in VARIANT_ORDER:
        r = rob.filter(
            (pl.col("fuel") == f) & (pl.col("variant") == key)
        ).row(0, named=True)
        order = f"({r['p']},{r['q']})" if r["q"] is not None else f"({r['p']},.)"
        elas = f"{r['lr_elasticity']:.3f}" if r["lr_elasticity"] is not None else "--"
        rows.append(
            f"{FUEL_EN[f]} & {VARIANT_LABEL[key]} & {order} & {elas} & "
            f"{r['backtest_rmse_cpl']:.2f} & {r['backtest_rmse_rw_cpl']:.2f} & "
            f"${r['mean_gap_cpl']:+.1f}$ & ${r['mom_cf_pct']:+.1f}$ \\\\"
        )

blk_txt = " ; ".join(
    f"{FUEL_EN[r['fuel']]}: $F={r['oil_block_F']:.1f}$, {p_fmt(r['oil_block_p'])}"
    for r in blk.iter_rows(named=True)
)

robust_table = f"""{head}\\begin{{table}}[H]
\\centering\\footnotesize\\setlength{{\\tabcolsep}}{{3pt}}
\\caption{{ARDL specification robustness: lag grids, forced oil lags, and distributed-lag / autoregression-only extremes}}
\\label{{tab:ardl-robust}}
\\begin{{tabular}}{{llcccccc}}
\\toprule
 & Specification & Order (AIC) & Long-run & {{RMSE}} & {{RMSE RW}} & Mean gap & {{MoM no cap}} \\\\
 & & & elasticity & (c/l) & (c/l) & (c/l) & (\\%) \\\\
\\midrule
{chr(10).join(rows)}
\\bottomrule
\\end{{tabular}}

\\medskip
\\footnotesize Each row re-selects $(p,q)$ by AIC on the stated grid,
refits the placebo backtest (14--27 Sep) and the no-cap projection.
``Order'' counts oil lags beyond the contemporaneous term. ``DL only''
= pure distributed lag (no autoregressive term); ``AR only'' has no oil
term at all and is an economically misspecified reference, not a
counterfactual. HAC block-exclusion of the Brent terms
in the baseline models: {blk_txt}. RW: no-change random walk.
\\end{{table}}

"""
open(OUT_ROBUST, "w").write(robust_table)
print(f"wrote {OUT_ROBUST}")
