# Changes from the original (8 Nov 2026) draft — Step 16

Original: tag `paper-v1-2026-11-08` (31 pp, 12 sections, 23 figures incl.
14 maps, 8 tables). Revised: `adoption/paper.tex` on `revision/v2-rewrite`
(18 pp, 8 sections, 5 main figures + 1 map pair, 13 tables incl. appendix).

## Analysis changes

| Area | v1 | v2 |
|---|---|---|
| Price data | Jul-Nov cache only | + MIMIT H1 archives: full Jan-Oct (12.4M rows) |
| Estimation window | 1 Jul-27 Sep (82 obs) | 2 Jan-27 Sep (261 obs) |
| Lag grid | p<=10, q in [7,10] | p<=21, q in [7,21] (author D6) |
| Selected models | (4,7) / (1,7) | (2,8) / (1,8) |
| Compliance rule | <= ceiling (inclusive) | < ceiling (strict; D3) |
| Diesel ceiling after 28 Oct | fixed 2.261 (undocumented) | 2.212 mechanical step (D4) |
| Placebo backtest | 14-27 Sep only, RMSE 1.93/4.01 | + 5 expanding origins, 14/28d; placebo 0.45/0.85 |
| Uncertainty | iid residual bootstrap | + moving-block + re-estimation bootstraps; scenario range |
| Inflation sensitivities | none | 45/55, 55/45, regularity sample; AR-only benchmark |
| Long-run elasticity | point estimates 0.43/0.50 | range across floors; near-unit-root caveat (main diesel LR not reportable) |
| Event study | leads dropped by a factor-levels bug | leads displayed (audit A-04) |
| Micro units | per EUR/l, per station | per 10 c/l, per 10 stations, per 1,000 residents |

## Headline numbers

| Quantity | v1 | v2 |
|---|---|---|
| October mean gap petrol | 16.3 c/l | 17.4 c/l (range 15-19) |
| October mean gap diesel | 24.3 c/l | 21.1 c/l (range 21-24) |
| NIC contribution | -0.40 pp | -0.38 pp (range -0.38..-0.45; AR bench -0.30) |
| Ever below cap | 84.5% | 84.4% petrol / 82.8% diesel |
| Final-day diesel share | 73.0% (fixed 2.261) | 50.2% (corrected 2.212 ceiling) |

## Corrections of v1 errors (audit A-series)

- "Two months" duration claim -> initial 30 days, level commitment through
  31 Oct (D5, press-release verified).
- "Inviting competitors to follow" -> removed (not in the release).
- Dispersion "doubled" -> quantified (p90-p10 +70%; SD detail by fuel/baseline).
- "34 post-cap days" -> 32 available days (16-17 Oct extracts missing).
- Snapshot bias "up to 4 c/l" -> 4.2-4.9 c/l on the roadside sample.
- AR-only diesel forecast superiority suppressed -> reported honestly
  (and it disappears on the extended window).
- Appendix Table 5 leads -> now displayed.
- NIC weight verified from ISTAT xlsx (was hardcoded; value confirmed).

## New results in v2

- Spring 2026 excise cut (-20 c/l, 19 Mar) and phased reinstatement as
  institutional context and estimation-window content.
- Bunching one decimal below the ceiling (17.9% of petrol obs at 1.999;
  diesel .19 endings 2.0->11.2%); post-6-Oct mass at 2.259.
- Group decomposition of the mean decline (Eni 27% of diesel move at ~19%
  share; white pumps 4%).
- 6-Oct compliance jump decomposition: 43 of 48 pp re-communicated on the day.
- 28-Oct natural experiment: ~40% pass-through of the excise cut in 3 days;
  zero mass at the new bunching point 2.211.
- ISTAT-like regularity-filtered sample (57.5% of units) as composition check.

## Paper architecture

12 sections -> 8 (Intro / Institutions / Data / Observed response /
Counterfactual / Inflation / Propagation / Conclusion); standalone
literature and discussion sections integrated; variable names moved to a
data-dictionary appendix; abstract rewritten last (approx. 200 words);
caption redundancy removed; bibliography cleaned (decorative metadata
fields stripped; 37 cited entries verified rendering).
