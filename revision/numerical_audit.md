# Numerical audit — v1 claims vs code/data (Step 05)

Legend: **status** = confirmed-error (fix in rewrite) | confirmed-correct |
resolved-by-decision (D1–D6) | superseded (number regenerated from extended
data / new rules; new value quoted where already available).

| # | v1 claim (location) | Finding | Status → action |
|---|---|---|---|
| A-1 | 84.5% ever below cap; final-day 81.8%/73.0% (abstract, §5) | Denominators differ legitimately (39,423 ever-entrants vs ~19.6k present on 31 Oct) but were never stated. New rules change values: ever 84.4% (petrol), 82.8% (diesel); final-day 81.8% petrol, **50.2% diesel** (2.212 ceiling). | superseded; rewrite states denominators explicitly |
| A-2 | Diesel share jump 6 Oct 55.1→66.3 pp (§5) | Partly threshold mechanics (ceiling 2.200→2.261), partly repricing; v1 already showed 42% moved +4–8 c/l. Formal decomposition table to be produced with new panel (Phase 3). | superseded; decomposition planned |
| A-3 | "province-level dispersion doubled" (§11) vs §8: petrol SD 6.8→7.8, diesel SD 10.1→8.2, pooled median unchanged 8.0 | Contradiction confirmed; "doubled" traces to the stale Oct draft's IQR claims. | confirmed-error; quantified replacement in Phase 3 |
| A-4 | Appendix Table 5 footnote: "pre-cap coefficients are small and insignificant" | Table displays only days +0…+7; no leads shown. Coefficients exist in the estimation window [−7,+7]. | confirmed-error; regenerate table with leads |
| A-5 | "no-oil reference … forecasts worse out of sample (petrol RMSE 3.19 versus 1.93)" (App. C) | Table 8: AR-only diesel RMSE 3.19 **beats** every oil model (4.01–5.43). Prose quotes petrol only. | confirmed-error; report AR-only fairly as mechanical benchmark (D-decision: never the economic no-cap spec) |
| A-6 | "capped … for two months" (abstract) | Eni announced 30 days initial, extension possible; commitment level hard through 31 Oct (author). | resolved-by-decision D5 |
| A-7 | "Averaged over the 34 post-cap days" (§9.3) | The 16–17 Oct *downloads* are missing, but effective prices are assigned by communication date, so those days are recovered from later extracts (author correction D7). Panel calendar now spans all calendar days; only same-gap double repricing could be lost — immaterial. | reframed-per-author; footnote in §3.2; v2 numbers average over all 34 days |
| A-8 | Abstract: snapshot bias "up to 4 c/l"; §4.2: 3.47/4.06 all-stations, 4.2/4.9 stradale estimation sample | Verified on extended pipeline (unchanged: Oct-1 naive−effective = 4.20/4.91 c/l). Abstract understates its own §4.2 number. | confirmed-error (wording); quote ~5 c/l max |
| A-9 | NIC weight 4.5219% hardcoded | Verified from `istat_ponderazioni_2026.xlsx`: ECOICOP 07.2.2 "Carburanti e lubrificanti" = 45,219‰. Class includes lubricants (small remainder). | confirmed-correct; weight now read from xlsx in revised code; remainder documented |
| A-10 | Cox/LPM coefficients in raw units (−4.4 per €/l, 0.0055 per station) | Reviewer request: report per-10-c/l and per-km. | superseded; units restyled in rewrite |
| A-11 | 16–17 Oct treated silently | Documented in lineage; never interpolated. | resolved |
| A-12 | `build_distances.py` used nominal (undated) thresholds for the adopter set | Inconsistent with panel for diesel after 6 Oct. | FIXED in code (date-aware + strict) |
| A-13 | `paper_draft.md` (13 Oct draft) contradicts final paper (IQR "100% of cells", "+12.1 c/l", Cox PH "holds") | Stale document. | resolved; deprecation header added |
| A-14 | "inviting competitors to follow" (abstract) | Eni's 25 Sep release contains no invitation to rivals; rival matching is observed behaviour. | confirmed-error; reframe in rewrite |
| A-15 | 6-Oct ceiling 2.261 presented as "the mechanical translation of a tax change" (§2) | Correct and now strengthened: the release ties the cap to the excise relief ("correlato all'agevolazione fiscale … in vigore"). 28-Oct step 2.212 follows the same rule (D4). | confirmed-correct; extended |
| A-16 | Backtest prose "cuts it [RMSE] by a fifth for diesel … excluding transition days 3.10" | Transition-day exclusion is post-hoc; keep but flag as diagnostic, or report with/without symmetrically. | superseded; Phase 2 rebuilds backtests |
| A-17 | Event day: "day −1 = 27 September omitted" (Tab. 5 note) | Correct given ref = −1. | confirmed-correct |

## New facts established in this audit (for the rewrite)

1. **Strict rule impact is negligible** (0.02–0.03 pp pooled); the story is the
   *bunching one decimal below the ceiling*: 17.9% of post-cap petrol
   observations at exactly 1.999; diesel masses at 2.199 (6.4% of its segment)
   and 2.259 after 6 Oct (8.5%) — i.e. stations repriced to the ceiling minus
   the rounding unit, not to the announced 1.99/2.19.
2. **28 Oct tax-cut pass-through at the ceiling is incomplete and slow**:
   mean diesel gross unchanged on the day (2.2580 vs 2.2585 the day before),
   −1.9 c/l by 31 Oct (≈40% of the 4.88 c/l mechanical adjustment);
   below-ceiling share collapses 65.8→24.0% on 28 Oct, recovers to 50.2%.
   No station priced at 2.211 (zero obs) — the new ceiling never became a
   focal price within the window.
3. **2026 excise context**: −20 c/l spring cut (19 Mar) phased back May–Jul
   explains the low H1 price level; the cap sits at the END of a year of
   active excise management — important institutional framing.
4. Eni release facts: 25 Sep 16:05, Enilive network, 30 days initial,
   possible year-end extension; excise-linked framing.
