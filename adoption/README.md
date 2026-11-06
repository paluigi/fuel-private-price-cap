# adoption/ — Voluntary price cap: adoption, counterfactual prices, inflation

Station-level study of Agip Eni's self-imposed price cap (2026-09-28:
Benzina ≤ 2.00, Gasolio ≤ 2.20 EUR/l, Stradale): who adopted and how it
diffused, an oil-based ARDL counterfactual for what pump prices would
have been without it, and the resulting contribution to measured
(ISTAT reference-day) inflation. Companion to the main repo analysis
(root README); feeds the paper `paper.tex` → `paper.pdf`.

## Reproducing the paper end-to-end

Requirements: Python ≥ 3.12 with [uv](https://docs.astral.sh/uv/),
R ≥ 4.4, ~2 GB disk, internet access (MIMIT/ISTAT/FRED downloads).

```
# 0. Price cache (repo root; needs MongoDB in .env)
uv run fuel-price-cap

# 1. ISTAT inputs: 2026 admin boundaries + 2021 1-km population grid
uv run python adoption/download_istat.py

# 1b. External series: Brent (FRED DCOILBRENTEU) + USD/EUR (FRED DEXUSEU)
#     -> data/external/*.csv, adoption/output/tables/oil_fx_daily{,_ffill}.csv
#     (if downloads are flaky inside Python, seed data/external/ with curl:
#      the script reuses existing files unless --refresh is passed)
uv run python adoption/build_oil_series.py

# 2. Station-day effective-price panel from dtComu (2026-07-01 → 10-12)
uv run python adoption/build_station_day.py

# 2b. Daily national price series (gross/net, effective vs extract,
#     balanced-panel robustness) -> output/tables/fuel_daily_prices.csv
uv run python adoption/build_fuel_daily.py

# 3. Covariates: province/region (2026 borders), population, chain size
uv run python adoption/build_station_covariates.py

# 4. Daily distances: nearest station, nearest at-cap station
uv run python adoption/build_distances.py

# 5. Analysis panel, survival input, dispersion/competitiveness tables
uv run python adoption/build_panel.py

# 6. Econometrics (R). Packages: see note below.
Rscript adoption/R/analysis_survival.R     # Cox/AFT, main sample
Rscript adoption/R/analysis_panel.R        # station-FE event study
Rscript adoption/R/revision_samples.R      # 3-sample Cox + LPM (paper tables)
Rscript adoption/R/analysis_ardl.R         # ARDL counterfactual + backtest
                                           # + ISTAT reference-day inflation
Rscript adoption/R/spec_robustness.R       # lag-grid / DL-only / no-oil
                                           # specification robustness

# 7. Figures and tables for the paper
uv run python adoption/revision_analysis.py    # event-study coefs + tercile fig
uv run python adoption/make_fig1_v2.py         # Fig 1 (fuel panels, tax line)
uv run python adoption/make_figs_update.py     # brand price fig + tercile fig
uv run python adoption/make_hist.py            # §7 dispersion histograms
uv run python adoption/make_maps.py            # province choropleths (blue-red)
uv run python adoption/make_tables.py          # LaTeX tables from R outputs
uv run python adoption/make_report_figs.py     # numbered English report figures
                                               # (1_benzina..., 7_...) -> output/figures
uv run python adoption/make_counterfactual_figs.py  # Brent/net index + actual vs
                                                    # counterfactual (paper figs)
uv run python adoption/make_tables_cf.py       # ARDL + inflation LaTeX tables

# 8. Paper PDF (pdflatex + biber)
cd adoption && pdflatex paper && biber paper && pdflatex paper && pdflatex paper
```

R packages (installed to `~/Rlibs` if not in the system library):

```
Rscript -e 'dir.create("~/Rlibs", showWarnings=FALSE); install.packages(c("survival","data.table","fixest","sandwich","lmtest","zoo","ARDL"), lib="~/Rlibs")'
```

`data/` holds the downloaded ISTAT/MIMIT/FRED raw inputs (~28 MB — not
committed; steps 1/1b re-create them). `output/` tables and figures are
regenerable and mostly not committed.

## Layout

- `config.py` — paths, analysis window, thresholds.
- `download_istat.py` — ISTAT inputs (2026 borders, 2021 population grid).
- `build_oil_series.py` — Brent USD→EUR conversion + calendar ffill
  (FRED CSVs cached in `data/external/`, committed).
- `crs.py` — CRS harmonization (WGS84 storage, EPSG:3035 metric work;
  2026 borders are UTM 32N despite the `_WGS84` filename).
- `build_station_day.py` — dtComu-effective station-day price panel
  (immune to the daily extract's pre-08:00 snapshot bias).
- `build_fuel_daily.py` — daily national gross/net price series
  (effective vs extract vs balanced panel), net = prezzo/1.22 − excise.
- `build_station_covariates.py` — geography, population, chain size.
- `build_distances.py` — daily nearest-station / nearest-adopter distances.
- `build_panel.py` — analysis panel + survival input + province tables.
- `R/analysis_survival.R` — Cox/AFT time-to-adoption (main sample).
- `R/analysis_panel.R` — daily event study (fixest).
- `R/revision_samples.R` — Cox + LPM on 3 samples (universe / excl.
  Agip Eni+Q8 / Pompe Bianche) → `output/revision_{cox,lpm}.txt`.
- `R/analysis_ardl.R` — log-log ARDL net price ~ Brent EUR (AIC/BIC lag
  grid + `auto_ardl` cross-check), recursive no-cap projection with
  bootstrap bands, placebo backtest, ISTAT reference-day MoM/CPI table.
- `R/spec_robustness.R` — re-runs selection/backtest/projection under
  alternative grids (max 15 lags; min 2 oil lags; DL-only; AR-only
  no-oil reference) + HAC block-exclusion Wald tests for the Brent terms.
- `revision_analysis.py` — event-study coefficients + tercile figure.
- `make_fig1_v2.py` — Fig 1 (per-fuel panels; diesel carries the
  6 Oct excise line, petrol none).
- `make_figs_update.py` — brand daily-price figure + tercile figure.
- `make_hist.py` — §7 dispersion/gap histograms.
- `make_tables.py` — regenerates the adoption LaTeX tables from the R outputs.
- `make_counterfactual_figs.py` — `fig_brent_net_index.png` (Brent/net
  prices indexed to 1 Jul = 100) and `fig_counterfactual.png` (actual vs
  counterfactual with 95% band, cap lines, reference days).
- `make_tables_cf.py` — `paper_tables_cf.tex` (ARDL spec/backtest) and
  `paper_tables_infl.tex` (reference-day MoM + CPI contribution).
- `make_maps.py` — province choropleths, blue→red scale (all stations,
  Pompe Bianche, and the by-fuel appendix series).
- `literature/` — reference pool, curated selection, `references.bib`.
- `paper.tex` / `paper.pdf` / `paper_tables*.tex` — the paper.

## Key numbers

Adoption (communications 2026-09-28 → 10-12; diesel cap 2.261 from 10-06):

- 39,423 station×fuel units; 70.2% priced at or below the (tax-adjusted)
  cap on at least one day within 15 days; final-day shares 52.9% petrol /
  70.3% diesel (median adoption: day 3). The 6 Oct excise change lifts
  diesel compliance by ~11 pp overnight — verified as genuine repricing
  (fresh dtComu on 6 Oct, +4–8 c/l moves into the new band), not a
  threshold artifact.
- Adoption hazard falls with distance to competitors/adopters, rises
  with population density and chain size; pre-cap gap dominates
  (Cox; holds in all three samples, strongest for Pompe Bianche).
- Province SD of effective prices rose in 214/220 province×fuel cells
  (median 50 → 90 c/l); non-adopters' gap to provincial mean
  +1.1 → +6.6 c/l.

Counterfactual and inflation (effective prices 2026-07-01 → 10-31):

- Brent EUR/bbl: index 100 (1 Jul) → 173 (cap date) → 177 (31 Oct).
- ARDL net price ~ Brent EUR (no tax dummy: the target is net of excise
  and VAT by construction): petrol ARDL(4,5) by AIC, (5,0) by BIC,
  long-run elasticity 0.44, half-life ~25 d; diesel ARDL(1,1) by both,
  0.63, half-life ~9 d. Placebo backtest (14–27 Sep): RMSE 1.80 / 5.03
  c/l vs random-walk 3.69 / 5.07 (diesel excl. excise-transition days
  18–20/26–27 Sep: 4.05).
- No-cap counterfactual pump prices average 16.5 (petrol) / 27.5
  (diesel) c/l above realised over 28 Sep–31 Oct; gap at window end
  20.7 / 31.8 c/l.
- ISTAT reference days (avg of 1/11/21): MoM Sep→Oct realised −2.34%
  (petrol) / +1.58% (diesel) vs counterfactual +4.92% / +13.37%;
  cap effect −7.26 / −11.79 pp; headline CPI contribution ≈ −0.43 pp
  (weight of ECOICOP 07.2.2 = 4.5219%, split evenly across fuels).
- Specification robustness (R/spec_robustness.R): max-15-lag grid
  re-selects the same orders; min-2-oil-lags moves the diesel gap to
  −24.7 c/l; DL-only leaves petrol at −15.1 c/l (best backtest) but
  degrades diesel; a no-oil AR (economically untenable) understates the
  effect. Oil block significant everywhere (HAC Wald p < 1e-6). Combined
  CPI effect across sensible specs: −0.41 to −0.46 pp.
- Snapshot bias on 1 Oct (stradale sample): recorded extract average
  overstates effective average by 4.2 / 4.9 c/l (3.47 / 4.06 c/l on the
  all-station sample).
