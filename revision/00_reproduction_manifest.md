# 00 — Reproduction manifest (Step 01)

Date: 11 November 2026 · Branch `revision/v2-rewrite` (off `feat/counterfactual-brent-ardl` @ 5e6ea5e)
Original frozen at tag `paper-v1-2026-11-08` (`adoption/paper.tex`, 31 pp, 12 sections).

## Environment

| Component | Status |
|---|---|
| Python | `uv` project env (pyproject/uv.lock), polars etc. as locked |
| R | `~/Rlibs` (survival, data.table, fixest, sandwich, lmtest, zoo, ARDL) — all present |
| Data | cache only: `data/prices_raw.parquet` (5,115,727 rows, 2026-07-01→2026-11-05, 20,967 stations), `data/stations.parquet`, `data/tax.parquet`, `data/external/` FRED CSVs |
| MongoDB | not used for prices; `fuels.tax` queried once for the 2005→ excise history (see D6; values within Jul–Oct identical to the cached rows, so v1 outputs are unaffected) |
| Seed | 20260928 (`R/analysis_ardl.R:66`) |

## Reproduction chain (all re-run from cache on 11 Nov 2026)

```
uv run fuel-price-cap --cache            # (deferred — descriptive layer, not a paper input)
uv run python adoption/build_oil_series.py        # cached FRED, no refresh
uv run python adoption/build_station_day.py
uv run python adoption/build_fuel_daily.py
uv run python adoption/build_station_covariates.py
uv run python adoption/build_distances.py         # heavy (KDTree per fuel×day)
uv run python adoption/build_panel.py
Rscript adoption/R/analysis_survival.R            # cwd = repo root
cd adoption && Rscript R/analysis_panel.R && Rscript R/revision_samples.R \
  && Rscript R/analysis_ardl.R && Rscript R/spec_robustness.R   # cwd = adoption/
cd adoption && for s in revision_analysis make_fig1_v2 make_figs_update make_hist \
  make_maps make_report_figs make_sec57_figs make_counterfactual_figs make_tables \
  make_tables_cf; do uv run python $s.py; done
```

## Headline v1 numbers reproduced (vs 8 Nov paper)

| Claim (paper location) | Paper | Reproduced | Status |
|---|---|---|---|
| Ever at/below cap by 31 Oct (abstract, §5) | 84.5% of 39,423 units | 0.8446 (Benzina, 19,746) / 0.8454 (Gasolio, 19,677) | ✓ |
| Final-day shares | 81.8% petrol / 73.0% diesel | 81.8 / 73.0 (`make_fig1_v2` log) | ✓ |
| Median adoption day | day 4 | 4.0 / 4.0 | ✓ |
| ARDL orders (BIC, q≥7) | petrol (4,7), diesel (1,7) | same (`ardl_summary.csv`) | ✓ |
| Backtest RMSE vs random walk | 1.93 vs 3.69 (petrol); 4.01 vs 5.07 (diesel) | 1.9346/3.6873; 4.0137/5.0749 | ✓ |
| Long-run oil elasticity | 0.43 / 0.50 | 0.4280 / 0.5024 | ✓ |
| CPI contribution | −0.40 pp | −0.400845 (−0.1624 petrol −0.2384 diesel) | ✓ |
| Petrol/diesel MoM (actual vs cf) | −2.34% vs +4.85%; +1.58% vs +12.13% | identical (`inflation_summary.csv`) | ✓ |
| Oct mean gaps | 16.3 / 24.3 c/l | `counterfactual_daily.csv` means identical | ✓ |
| Cox/LPM tables | `paper_tables*.tex` | byte-identical regeneration | ✓ |

## Diffs vs tracked v1 outputs (git)

- `output/tables/fuel_daily_prices.csv` — 1 line, last-digit float artifact (1.3327106259469215→…242).
- `output/tables/province_dispersion.csv`, `nonadopter_competitiveness.csv` — sd/gap columns differ in the last 2–3 significant digits (polars parallel group-by summation order); counts, means, percentiles identical (verified on Milano rows).
- `output/figures/event_study_by_capdist.png` — matplotlib re-render, byte differences only.
- **All other tracked outputs and every auto-generated TeX table byte-identical.**

Verdict: **v1 fully reproduced from cache.**

## Known environmental notes

- README's `Rscript adoption/R/*.R` chain only works from repo root for `analysis_survival.R`; the other four need `cwd = adoption/` (to be fixed with the v2 chain).
- `adoption/mongo_refresh_incremental.py` hardcodes `/home/ubuntu/coding/...` (unused in this revision; left as-is, documented).
- Extract-day gap: `prices_raw` has 121 extract days 1 Jul–31 Oct (no extracts 16–17 Oct) → the post-cap daily path has 32 of 34 calendar days; the paper's "34 post-cap days" wording is a claim-ledger item (audit A-7).
