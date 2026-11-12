# Author memo — submission readiness

**Manuscript:** *Counterfactual Prices, Inflation, and Adoption: A
Voluntary Price Cap in the Italian Retail Fuel Market* (18 pp incl.
appendix, `adoption/paper.pdf`, branch `revision/v2-rewrite`).

## What changed, in one paragraph

The paper is rebuilt around the macro question. The estimation window now
uses your January archives (261 pre-cap observations, max lag 21), the
compliance rule is strict with the corrected 28 October diesel ceiling
(2.212), and every number, figure and table is regenerated. Headline:
gaps 17.4 / 21.1 c/l (petrol/diesel), NIC contribution -0.38 pp
(specification range -0.38 to -0.45; aggregation sensitivities negligible).
The AR-only embarrassment is gone on the longer window; backtests improved
~4x; uncertainty now includes re-estimation and block bootstraps plus a
scenario range. The micro evidence is compressed into one mechanism
section with readable units. All eight reviewer-flagged contradictions are
resolved (claim ledger, 17+ items).

## Author decisions incorporated (12 November 2026)

1. **January window confirmed** as baseline (July shown as sensitivity).
2. **28 October brand analysis added** (§7 + tab:brand-28oct): Eni ends
   October at 2.190 €/l, 99% compliant — it was already at the announced
   nominal level, so the corrected 2.212 ceiling required nothing of it.
   The incomplete pass-through is entirely a follower gradient: Q8 cut
   3.8 c/l (78% compliant by 31 Oct), Api-Ip 2.7 (60%), Esso/Tamoil
   2.4–3.4 (22–32%), white pumps 1.8 (15%). This sharpens the earlier
   "firms no longer treating the ceiling as binding" reading: the
   *leader* treated the commitment level as binding to the end; the
   followers did not.
3. **ECM/bounds appendix added** (app:ecm + tab:ecm-bounds): PSS bounds
   tests decisively fail to reject no-level-relationship (F 1.40/0.92
   against a 4.92 lower bound; ECT insignificant). Levels long-run
   elasticities are not identified over 2026 — the formal backing for
   range-reporting and forecast validation.
4. Title reorder and single map pair confirmed as delivered.

## Handling of the missing 16–17 October downloads (author correction)

Effective prices are assigned by communication date, so the two missing
downloads lose no days: the panel calendar now spans all calendar days
and every average covers the full 34-day window. Disclosed as a §3.2
footnote; only same-gap double repricing could be lost, which is
immaterial. Headlines after the 34-day rerun: gaps 17.45/21.13 c/l,
endpoint gaps 22.4/20.5, NIC −0.378 pp (sensitivities −0.374/−0.381/
−0.411).

## Additions completed in this round (13 November)

- **Discrete-time hazard model** (\cref{tab:hazard-dt} in the appendix,
  one sentence in section 7): logit hazard with day fixed effects on
  463,594 unit-days reproduces every Cox gradient without the PH
  assumption (odds ratios 0.41/0.21 per 10 c/l of pre-gap; baseline
  spikes at the 1 Oct repricing wave and the 6 Oct excise step).
- **Province maps**: one restyled pair in the appendix (adoption within
  seven days, common 0-100% scale, sequential colour-blind-safe blues).

## Out of scope (author decision)

- November 2026 data: outside the fixed analysis window; dropped from
  the extension list.

## Reproduction

One chain, one seed (20260928), all inputs local except the two FRED CSVs
(cached) and one MongoDB read (`fuels.tax`). See
`revision/reproduction_instructions.md`; the numeric gate
(`revision/check_numbers.py`, 53 checks) exits 0 on the shipped PDF.

## Suggested submission target

*Energy Economics* fits the revised design (conditional forecasting
counterfactual + measurement contribution + mechanism section). The paper
no longer invites the general-interest identification critique the
original's framing attracted.
