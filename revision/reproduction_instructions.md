# Reproduction instructions — revised paper (v2)

Branch `revision/v2-rewrite`. Seed 20260928. R packages in `~/Rlibs`
(survival, data.table, fixest, sandwich, lmtest, zoo, ARDL). Python via
`uv` (locked environment; `fastexcel` only for the optional xlsx weight
check). Data sources: MIMIT archives in `data/mimit_archives/` (tars),
cached parquets `data/*.parquet`, FRED CSVs in `data/external/`, MongoDB
`fuels.tax` for the excise history (2005→).

## One-off inputs

```bash
# 1. H1-2026 price archives -> parquet (untrusted-input protocol)
tar -xzf data/mimit_archives/2026_1_tr.tar.gz -C <empty dir>   # then point
tar -xzf data/mimit_archives/2026_2_tr.tar.gz -C <empty dir>   # --archive-root
uv run python -I adoption/build_archive_prices.py \
    --archive-root data/mimit_archives/extracted \
    --reference data/prices_raw.parquet --out data/prices_archive.parquet
uv run python -I adoption/make_prices_full.py          # data/prices_full_2026.parquet

# 2. excise calendar from MongoDB (cached values verified unchanged)
uv run python -I adoption/refresh_tax.py
```

## Full chain (from repository root)

```bash
# data builders
uv run python adoption/build_oil_series.py            # cached FRED inputs
(cd adoption && uv run python build_station_day.py)   # effective-day panel, Jan-Nov
(cd adoption && uv run python build_fuel_daily.py)    # national series + reg/bal variants
(cd adoption && uv run python build_station_covariates.py)
(cd adoption && uv run python build_distances.py)     # micro window (Jul-Oct)
(cd adoption && uv run python build_panel.py)         # adoption panel, survival input
(cd adoption && uv run python build_definitions_series.py)   # Step 04 series
(cd adoption && uv run python -I tests/test_price_arithmetic.py)

# econometrics
Rscript adoption/R/analysis_survival.R               # cwd = repo root
cd adoption
Rscript R/analysis_panel.R                           # event study (leads fixed)
Rscript R/revision_samples.R                         # Cox/LPM by sample
Rscript R/analysis_ardl.R                            # ARDL + placebo + inflation
Rscript R/spec_robustness.R                          # floors / DL / AR grid
Rscript R/uncertainty_ardl.R                         # origins + bootstraps + scenarios

# decomposition and exhibits
uv run python -I analysis_decomposition.py           # 6-Oct, endings, groups, dispersion
uv run python make_fig1_v2.py make_figs_update.py make_maps.py   # legacy figs (appendix maps)
uv run python make_paper_v2_figs.py                  # Figures 1-4
uv run python make_tables.py                         # Cox/LPM tables (rescaled units)
uv run python make_paper_v2_tables.py                # macro + appendix tables

# paper
pdflatex paper && biber paper && pdflatex paper && pdflatex paper

# numeric consistency gate (53 checks, must exit 0)
cd .. && uv run python -I revision/check_numbers.py
```

Note: R scripts other than `analysis_survival.R` must run with
`cwd = adoption/`; `analysis_survival.R` reads a repo-root-relative path.
The v1 README chain is superseded by this file.
