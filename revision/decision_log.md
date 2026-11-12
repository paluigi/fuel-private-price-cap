# Decision log — v2 revision (branch revision/v2-rewrite)

Working contract: `.zcode/FUEL_CAP_REVISED_REVIEW_AND_AGENT_INSTRUCTIONS_v2.md`
(16-step pack in `.zcode/fuel_cap_agent_pack_v2/`). Original paper frozen at
git tag `paper-v1-2026-11-08` (8 Nov 2026 draft, adoption/paper.tex, 31 pp).

## D1 — Gate cadence (11 Nov 2026, author)
16 per-step STOP gates consolidated into 4 gates: (1) after Steps 01-06,
(2) after Steps 07-09, (3) at Step 12 outline, (4) final Step 16 delivery.
Steps 06 and 12 remain genuine author sign-offs.

## D2 — Workspace (11 Nov 2026, author)
New branch `revision/v2-rewrite` off `feat/counterfactual-brent-ardl` HEAD
(5e6ea5e). Rewrite `adoption/paper.tex` in place; `revision/` holds ledgers,
logs, step reports and memos only. Original tagged, not copied.

## D3 — Boundary rule: strict < (11 Nov 2026, author)
Compliance becomes `prezzo < threshold` (petrol < 2.000; diesel < 2.200 /
< 2.261 / < 2.212). Previously inclusive `<=` (build_station_day.py:113,
build_panel.py:38, src/analysis.py:188). Historical adoption statistics
recomputed under the strict rule; boundary counts (exact 2.000 / 2.200 /
2.261 / 2.221 rows) reported at Gate 1 before any paper number is finalised.

## D4 — Diesel ceiling steps (11 Nov 2026, author)
Operational gross ceiling: 2.200 from 28 Sep; 2.261 from 6 Oct
(2.200 + 0.05 × 1.22); **2.212 from 28 Oct** (2.261 − 0.04 × 1.22 = 2.2122,
rounded to 3 dp), reflecting the 28 Oct diesel excise cut (672.90 → 632.90
EUR/1000 l). Third step added to THRESHOLD_BY_DATE in adoption/config.py and
src/fuel_price_cap/config.py. Note: pre-6-Oct value 2.20 and post-6-Oct
2.261 are "rounded-up operational cutoffs" over the announced nominal
1.99/2.19; the 28-Oct step follows the same mechanical translation rule the
author applies, in the opposite direction.

## D5 — Duration framing (11 Nov 2026, author)
The hard commitment on the cap level ran through 31 October 2026 (author's
institutional knowledge); oil-company communications after 31 Oct are less
clear about continued commitment. Paper therefore: drop the "two months"
claim; state the initial 30-day announcement (25 Sep, Eni) and treat
1 Jul–31 Oct as the analysis window. Web-verify the press release (record
only; the author's statement governs framing).

## D6 — Extended data (11 Nov 2026, author)
`data/mimit_archives/2026_1_tr.tar.gz` + `2026_2_tr.tar.gz` (MIMIT price
archives from 1 Jan 2026) joined to the cached Jul–Oct parquets. Longer
pre-cap window used for ARDL estimation; max lag order raised 10 → 21
(grid p ∈ [0,21], q ∈ [7,21], BIC; oil-lag floors 2/5/7 retained as
sensitivity). Price data otherwise cache-only; MongoDB queried only for
`fuels.tax` (2005 onwards) to refresh data/tax.parquet with full statutory
coverage from January.

## Environment / reproduction premises
- R scripts use `~/Rlibs`; seed 20260928 (analysis_ardl.R:66).
- v1 reproduction must complete from cache BEFORE the D3/D4 config switch.

## D7 — Missing 16–17 October downloads (12 Nov 2026, author)
The two missing MIMIT *extracts* do not create missing *days*: effective
prices are assigned by communication date, so 16–17 October are recovered
from the communications carried by surrounding extracts. The station-day
calendar is therefore built over all calendar days between a pair's first
and last extract appearance (previously: extract dates only). Only a price
change communicated and fully superseded within the two-day gap would be
lost — immaterial, disclosed in a §3.2 footnote. All averages now cover
the full 34 post-cap days (headline numbers essentially unchanged:
gaps 17.45/21.13 c/l, CPI −0.378 pp).

## D8 — Brand compliance at the 28 October ceiling (12 Nov 2026, author)
Author requested an Eni-vs-others compliance check after the excise cut.
Added `brand_compliance_28oct` to `analysis_decomposition.py`, appendix
Table `tab:brand-28oct`, and a §7 paragraph. Finding: Eni ends October at
2.190 €/l (99% compliant, already at the nominal); followers' cuts range
3.8 c/l (Q8, 78%) to 1.8 c/l (white pumps, 15%) — the aggregate
incomplete pass-through is entirely a follower phenomenon.

## D9 — ECM/bounds-test appendix (12 Nov 2026, author)
Added `R/ecm_bounds.R` and appendix Section "Levels relationship: bounds
tests" with Table `tab:ecm-bounds`. Pesaran–Shin–Smith bounds tests
(case 3, same window): F = 1.40 (petrol) / 0.92 (diesel) vs I(0) bound
≈4.92; t = −1.63 / −0.60; ECT insignificant. No levels relationship over
2026 → long-run elasticities not identified; formalizes the paper's
range-reporting + forecast-validation stance.

## D10 — January window confirmed (12 Nov 2026, author)
Author confirmed the January fit as the baseline (item 1 of the memo);
July remains the shown sensitivity. Title reorder and map pair also
confirmed.

## D11 — Additions round (13 Nov 2026, author)
Author instructions: include the discrete-time hazard model (placement
decided on results) and keep one province-map pair in the appendix;
November data dropped from scope. Outcome: hazard model confirmatory
(every Cox gradient intact; baseline spikes at the 1 Oct wave and the
6 Oct excise step) -> appendix table tab:hazard-dt + one section-7
sentence. Maps restyled (make_v2_maps.py, sequential blues, common
scale); old amap_* files retained on disk for the audit trail but no
longer referenced.
