# Policy chronology — the 2026 voluntary price cap (Step 02)

All times CEST. Sources: Eni press release (verified 11 Nov 2026 via eni.com),
MIMIT open data, `data/tax.parquet` (MongoDB `fuels.tax`, 2005→), author
institutional knowledge (flagged as such).

## The cap episode

| Date | Event |
|---|---|
| **2026-09-25 (16:05)** | Eni press release: from **28 September** caps self-service petrol at **1.99 €/l** and diesel at **2.19 €/l** "per una durata iniziale di 30 giorni", "con possibilità di estensione fino alla fine dell'anno in funzione dell'andamento del mercato e degli approvvigionamenti". The release describes the measure for Eni's **Enilive** network and links it to the excise relief in force ("correlato all'agevolazione fiscale sulle accise in vigore"). |
| **2026-09-28** | **Implementation date** (the paper's event day, t=0). Enilive stations re-price in the 00:00–08:00 communication wave. |
| 2026-09-28 + 30d | Initial 30-day period ends 27/28 October. |
| **2026-10-27/28** | Extension: press coverage confirms the cap maintained beyond the initial 30 days; per author knowledge a hard commitment on the cap **level** ran through **31 October**; communications about commitments after 31 October are less clear. |
| 2026-10-31 | End of the paper's analysis window (fixed ex ante by the data cut). |

Notes for the paper:
- The release does **not** invite competitors to follow (v1 abstract claimed it did); rival
  matching is documented as observed behaviour, not an announced invitation.
- 25–27 Sep is used only for an anticipation check; the economic treatment date stays 28 Sep.
- "Two months" (v1 abstract) is not supported by the announcement; correct framing:
  initial 30-day commitment, maintained through (at least) 31 October.

## Excise calendar 2026 (EUR per 1,000 l; `fuels.tax`, VAT 22%)

| From | Petrol | Diesel | Δ diesel (c/l) | In paper window? |
|---|---|---|---|---|
| 2026-01-01 | 672.90 | 672.90 | — | estimation (extended) |
| **2026-03-19** | 472.90 | 472.90 | **−20.0** | estimation (spring cut) |
| 2026-05-02 | 622.90 | 472.90 | petrol +15 | estimation |
| 2026-05-23 | 622.90 | 572.90 | +10.0 | estimation |
| 2026-06-07 | 622.90 | 622.90 | +5.0 | estimation |
| 2026-07-04 | 672.90 | 672.90 | +5.0 (both) | estimation |
| 2026-07-28 | 672.90 | 532.90 | −14.0 | estimation (diesel discount) |
| 2026-09-18 | 672.90 | 572.90 | +4.0 | estimation (pre-cap) |
| 2026-09-26 | 672.90 | 622.90 | +5.0 | estimation (pre-cap) |
| **2026-10-06** | 672.90 | 672.90 | **+5.0** | **post-event #1** |
| **2026-10-28** | 672.90 | 632.90 | **−4.0** | **post-event #2** |
| (2026-11-08 / 11-10) | 672.90 | 672.90 / 632.90 | +4 / −4 | after window (not used) |

Rows 2026-04-08, 05-11, 07-30, 08-07, 08-25, 08-27, 09-07, 09-11 restate unchanged
values (re-legislation); they are redundant in the calendar join.
**No petrol change after 4 July** — in particular none in the outcome period.

## Operational thresholds (gross, Stradale self-service)

| Segment | Petrol | Diesel | Rule |
|---|---|---|---|
| from 2026-09-28 | 2.000 | 2.200 | compliant ⇔ prezzo **<** threshold (strict; D3) |
| from 2026-10-06 | 2.000 | 2.261 | 2.200 + 0.05 × 1.22 (mechanical VAT translation) |
| from 2026-10-28 | 2.000 | 2.212 | 2.261 − 0.04 × 1.22 = 2.2122 → 3-dp grid 2.212 (D4) |

With 3-decimal prices, strict `<` means the highest compliant prices are
1.999 / 2.199 / 2.260 / 2.211. Exact-boundary masses are negligible
(petrol 2.000: 171 obs = 0.02% of post-cap station-days; diesel 2.200: 14 obs;
2.261: 229 obs = 0.06%; 2.212: 7 obs) — see `threshold_boundary_counts.csv`.

## Institutional facts used in the paper

- MIMIT daily `prezzo_alle_8` files snapshot prices in force at 08:00 the
  preceding day; the `dtComu` field carries the communication timestamp used
  to reconstruct effective daily prices (Step 03).
- ISTAT NIC fuel observations use the 1st/11th/21st reference days
  (ISTAT FAQ, verified 11 Nov 2026).
- Eni/Enilive is the largest branded network (~4.9k of ~21k Stradale stations
  reporting prices in the panel); brand field "Agip Eni" in MIMIT data.
