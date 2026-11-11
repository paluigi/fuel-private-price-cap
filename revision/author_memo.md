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

## Decisions you may want to revisit

1. **January vs July fit window as baseline.** January is the baseline
   (your D6); July moves the diesel gap from -21.1 to -24.3 c/l and would
   push the NIC estimate toward -0.40. Both are shown (Table 7); the
   choice is documented but is the single largest sensitivity.
2. **The 50.2% final-day diesel share.** Under the corrected 2.212
   ceiling, half the diesel network ends October *above* the mechanical
   ceiling. This is now a feature of the paper (incomplete pass-through at
   a fading ceiling) but it is the number most likely to draw referee
   questions; the alternative reading (firms no longer treating the
   ceiling as binding once the commitment's end approaches) is in the
   text.
3. **Near-unit-root disclosure.** We state that the diesel main spec's
   long-run elasticity is not interpretable and report the range across
   floors. A referee may ask for an ECM/bounds-test treatment; that is a
   feasible extension but was not required by the review.
4. **Title.** Reordered to put the macro objects first; easy to revert.

## Suggested referee-response-ready extras (not in the paper)

- Discrete-time hazard model (PH rejection is disclosed).
- November data pull to document post-commitment behaviour (outside the
  fixed window by design).
- Province-level maps: kept to one appendix pair; the full catalogue can
  be reintroduced if requested.

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
