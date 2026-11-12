# Data lineage — from MIMIT source files to analysis series (Step 03)

## Source layers

| Layer | Content | Coverage | Path |
|---|---|---|---|
| MIMIT official archives | daily `prezzo_alle_8-YYYYMMDD.csv`, pipe-separated, one row per station × fuel × service type | 2026-01-01 → 2026-06-30 (181 files, no gaps) | `data/mimit_archives/extracted/2026_{1,2}_*/` (from user-supplied tars) |
| MongoDB `fuels.prices` cache | same MIMIT rows, pre-filtered `isSelf=1`, `{Benzina, Gasolio}` | 2026-07-01 → 2026-11-05 | `data/prices_raw.parquet` |
| Combined panel | archive + cache, identical schema | 2026-01-01 → 2026-11-05, 12,425,091 rows, 307 extract days, 21,766 stations | `data/prices_full_2026.parquet` (`adoption/make_prices_full.py`) |
| Weekly anagrafica snapshots | gestore/bandiera/tipo_impianto/provincia/lat-lon per station per week | 2026-03-10 → 2026-11-02 (35 snapshots, 24,773 stations) | `data/stations.parquet` |
| Excise calendar | application_date + EUR/1000 l rates | 2005-02-21 → 2026-11-10 | `data/tax.parquet` (refreshed from `fuels.tax`, D6) |
| Brent + USD/EUR | FRED `DCOILBRENTEU`, `DEXUSEU` → `brent_eur = USD/bbl ÷ USD/EUR`, calendar-day forward-fill | full 2026 | `data/external/*.csv` → `output/tables/oil_fx_daily_ffill.csv` |

Archive-vs-cache conventions were aligned: 136 placeholder prices (>5 EUR/l,
5 stations, e.g. 8.888) dropped from the archive side; the MongoDB extract
contains none. 96.2% of archive stations also appear in the H2 cache
(487 H2-only: later entrants/rebrands). Schema, dedup and dtComu parsing are
identical by construction (`build_archive_prices.py` asserts parity).

## Timing semantics (the core measurement point)

- Each MIMIT file dated D is published on D and refers to prices **in force at
  08:00 on D−1**; a row's `dtComu` field is the operator's communication
  timestamp (when the price was last set).
- A raw extract therefore mixes prices communicated at very different times;
  on high-churn days (cap day, post-excise days, 1 Oct) the extract mean is
  biased relative to prices actually in force on any given day.
- **Effective-day reconstruction** (`build_station_day.py`): dedup
  communications on (station, fuel, dtComu) keeping max price; for every
  station × fuel × extract-day D, the effective price is the last
  communication with `comu_date ≤ D` (backward `join_asof`). A station-day is
  kept only from its first in-window communication (no indefinite carry-forward).
- The analysis uses effective prices throughout; naive extract means are kept
  only as a measurement comparison.

Worked example (station 3464, petrol, cap week):

| extract date | price in file | dtComu (communication) |
|---|---|---|
| 2026-09-28 | 2.309 | 2026-09-25 20:00 |
| 2026-09-29 | 2.309 | 2026-09-28 10:02 |
| 2026-09-30 | **2.049** | 2026-09-29 20:30 |
| 2026-10-01 | 2.049 | 2026-09-29 20:30 |
| 2026-10-02 | **1.990** | 2026-10-01 20:00 |

The cap-day extract still carries the pre-cap price; the cuts arrive via the
29 Sep and 1 Oct evening communications. Snapshot vs effective means on
1 October (Stradale self-service): petrol 2.1102 vs 2.0683 (4.2 c/l), diesel
2.3151 vs 2.2660 (4.9 c/l) — the reference-day measurement correction.

## Known coverage gaps (documented, never interpolated)

- **16–17 October 2026**: no MIMIT extracts exist (the only gap in 307 days).
  The effective panel and the counterfactual path therefore have 32 of the 34
  post-cap calendar days; averages are over available days and figures show
  the gap. Reference days (1/11/21) are unaffected.
- January–early-March rows are classified Stradale/Autostradale via the
  station's **latest** weekly snapshot (first snapshot: 2026-03-10); ~0.5–0.8%
  of H1 rows cannot be typed and drop from the national series. Coverage is
  otherwise stable (39.1k Stradale rows/day in January vs 39.5k in October).

## Reproducibility anchors

- Seed 20260928 for all bootstrap simulation; R packages in `~/Rlibs`.
- One command chain (see `revision/reproduction_instructions.md` at delivery).
- v1 reproduction record: `revision/00_reproduction_manifest.md`.
