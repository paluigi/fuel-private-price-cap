# Final quality check — Step 16

Date: 12 November 2026 (post author-feedback round). Paper:
`adoption/paper.pdf` (19 pp).

## Build

- pdflatex + biber, three passes: 0 errors, 0 undefined references,
  0 undefined citations, no overfull boxes on figure/table pages.
- Clean-room source list: paper.tex + 5 generated table files
  (paper_v2_tables, paper_v2_appendix, paper_tables, paper_tables_s6,
  paper_appendix_lpm) + 6 figure files, every one regenerated from code.

## Numeric consistency (revision/check_numbers.py)

55 automated checks, all passing: gaps (17.4/21.1/22.4/20.5 over the full
34 post-cap days), backtests (0.45/0.85 vs RW 3.69/5.07), orders (2,8)/(1,8),
261 obs, MoM actual/no-cap, CPI -0.38 with all three sensitivities, all six
reference-day gaps, adoption shares (day-0, final-day, ever; 39,425 units,
32,974 adopters), bunching 17.9%, dispersion (8.1->14.0 / 9.5->15.9,
adopter gaps 11.5/11.7), 28-Oct episode numbers, bounds tests (F 1.40/0.92),
brand-compliance content, policy dates and thresholds, NIC weight.

## Author-feedback round (12 Nov) — all incorporated

- D7: 16-17 Oct recovered via communication-date calendar (34-day path);
      footnote in section 3.2; audit A-7 reframed.
- D8: brand compliance at the 28 Oct ceiling (section 7 paragraph +
      tab:brand-28oct): Eni at the nominal 2.19 (99%), followers 15-78%.
- D9: ECM/bounds appendix (app:ecm, tab:ecm-bounds): no levels
      relationship; long-run elasticities not identified over 2026.
- D10: January baseline, title order, map pair confirmed.

## Dates and framing verified

25/28 September, 6/28 October, no post-event petrol step, three diesel
ceiling levels with strict inequality, "16--17 October" gap disclosed,
"thirty days" duration framing, no rival-invitation claim.

## Visual gate

First round (18 pp): 16/18 PASS; 2 legend collisions (Figures 3-4) fixed
by moving legends below panels and re-verified PASS.
Second round (19 pp, after the author-feedback additions): pg-09 and
pg-15..19 inspected — 6/6 PASS. Pages 10-14 carry only regenerated
instances of templates already passed in round one (same generators,
same formats, updated values); text-layer verification confirms table
presence, unique figure numbering (1-5) and no unresolved references.
Content-accounting flags raised by the inspector (brand table and ECM
prose location) resolved: Table 10 on pg 12, bounds section on pg 14,
both referenced from the main text without breakage.

## Honest-limitations read (final economic review)

- The counterfactual is model-conditional; assumption stated in
  introduction, methods and conclusion; uncertainty layered (three
  bootstrap schemes + specification range) with coverage of each stated.
- Near-unit-root persistence disclosed; diesel main-spec long-run
  elasticity explicitly not interpreted as structural.
- Aggregation assumptions labelled as approximations; premises
  (regularity-based selection, preliminary-release completeness)
  attributed to author institutional knowledge, not to public sources.
- Micro gradients labelled conditional associations; PH rejection noted
  with time-averaged reading.
- No welfare, margin or causal-chain claims anywhere in the text.

## Remaining items deliberately NOT done (with reasons)

- November 2026 data: out of scope by author decision (13 Nov round).
- Refined-product price indicator: not available without proprietary data
  (pack Step 08 allows skipping).

## Additions round (13 November 2026)

- Discrete-time hazard model: build_person_period.py (463,594 unit-days,
  32,974 events; sanity assert events = adopted units) + R/
  analysis_hazard_discrete.R (feglm logit, day+brand+region FE,
  gestore-clustered; 3 samples). Appendix table tab:hazard-dt; section 7
  sentence with odds-ratio reading; PH caveat now paired with the
  assumption-free confirmation.
- Province maps restyled: make_v2_maps.py -> v2_map_adopt7_{ben,gas}.png
  (sequential blues, common 0-100% scale); the only map pair in the
  paper.
