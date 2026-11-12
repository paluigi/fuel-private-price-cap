# Research design memo (Step 06) — for Gate 1 sign-off

## The one question

> How much did Eni's voluntary price cap — matched within weeks by most of
> the Italian fuel-retail network — moderate pump prices during the
> September–October 2026 oil-price surge, and what did it contribute to
> October measured consumer-price inflation?

Everything else in the paper exists to make that question answerable and its
answer credible: the station panel validates observed prices; adoption
evidence explains *how* the aggregate price path changed; institutional
detail (excise calendar, ceiling mechanics) keeps the counterfactual honest.

## Three estimands (kept distinct in the paper)

1. **Observed price response** — the actual national petrol/diesel price path
   (effective-day, Stradale, self-service) before/after 28 September, net of
   statutory taxes. Purely descriptive, no model.
2. **Conditional no-cap price path** — what pre-cap oil-to-net-pump-price
   pass-through implies for 28 Sep–31 Oct, given the *actual* Brent path and
   the *actual* excise calendar. Model-based, conditional on the maintained
   assumption that pre-cap pass-through would have continued absent the cap.
   Not experimental identification; a transparent policy counterfactual.
3. **Approximate inflation-accounting effect** — the difference between the
   observed and no-cap paths evaluated at the 1/11/21 reference days,
   aggregated with documented approximation assumptions (≈50/50 fuel split,
   equal station weights in a regularity-filtered sample, ECOICOP 07.2.2
   weight 4.5219%). An *estimated contribution to headline NIC inflation
   under stated assumptions*, not a replication of ISTAT's proprietary index.

## Supporting (micro) evidence, demoted to mechanism

Adoption timing, brand contrasts, distances, bunching and dispersion appear
as *how the aggregate movement happened*: who repriced, when, where; the
28-Oct natural pass-through check (excise cut at the ceiling) as validation
that the ceiling binds behaviourally.

## Maintained assumptions (stated plainly in the paper)

- Pre-cap oil pass-through would have persisted absent the cap (tested via
  backtests, specification grid, fit-window and announcement-window variants;
  uncertainty propagated with re-estimation + block bootstrap).
- No general-equilibrium feedback: the cap did not move Brent or the EUR/USD
  rate (plausible: Italy is a price-taker).
- Counterfactual taxes = actual taxes (the excise calendar is policy, not
  firm behaviour).
- Aggregation assumptions for NIC (above) — sensitivities 45/55, 55/45,
  regularity-filtered vs universe.

## Abstract-number candidates (final values fixed after Step 07–09)

- October mean gap vs no-cap path, petrol and diesel, c/l (was 16.3/24.3).
- Estimated October NIC contribution, pp (was −0.40), with range.
- Adoption: ever-below share by 31 Oct (≈83–84%); day-4 median; brand coverage.
- One mechanism number: e.g. the 17.9% petrol mass at exactly 1.999 €/l, or
  the 28-Oct incomplete pass-through (−1.9 c/l of −4.9 by 31 Oct).

## Caveat list (to appear, proportioned, in intro + conclusion)

- Conditional (not identified) counterfactual; sensitivity shown.
- Window ends 31 Oct; post-window commitment unclear (author).
- Micro regressions are conditional associations (PH rejected; time-varying
  effects reported as such).
- Net-of-tax price ≠ retail margin; no volume/welfare claims.
- 16–17 Oct extract gap (2 of 34 post-cap days), never interpolated.

## Paper architecture target (Step 12 will finalize)

8 sections: Intro / Institutional setting / Data & measurement / Observed
response / Counterfactual / Inflation / Propagation mechanism / Conclusion.
4–5 main figures, 3–4 main tables; survival/LPM detail, lag grids, maps,
boundary counts, data dictionary in the appendix.
