# Onda 2E Timing Domain EDA - 2026-06-07

This report resolves WCT-TIMING-001 as an evaluation target timing prior.
`tmax_hour` is a full-day outcome and must never be used as direct CP evidence.
Any late-Tmax prior derived from this table must be computed train-only.

## Artifacts

| Artifact | Rows |
|---|---:|
| `domain_timing_norms_by_month_regime.csv` | 57 |
| `domain_timing_fixed_18_sensitivity.csv` | 228 |
| `domain_timing_bucket_priors.csv` | 574 |

## Power

- Underpowered month x regime cells (`n < 30`): 28/57.

## Decision Implication

- `WCT-TIMING-001`: SUPPORTED as prerequisite evidence.
- `RULE_LATE_WARMING_FIXED_18`: ADAPTED to month/regime-relative q90 timing norms.
- No feature candidate is promoted by this report.