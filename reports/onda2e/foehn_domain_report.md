# Onda 2E FOEHN Domain EDA - 2026-06-07

No production classifier change is made by this report.
`RULE_FOEHN_SCORE_FIXED_60` is adapted as an audit comparator, not production truth.

## Artifacts

| Artifact | Rows |
|---|---:|
| `domain_foehn_score_bins_by_month_cp.csv` | 272 |
| `foehn_false_positive_audit.csv` | 48 |
| `foehn_power_leakage_audit.csv` | 3 |
| `foehn_regime_repair_candidates.csv` | 1 |

## Power

- Underpowered FOEHN score-bin cells (`n < 30`): 55/272.

## Decision Implication

- `WCT-FOEHN-001`: PROMOTED_TO_REGIME_DESIGN for calibration review.
- `RULE_FOEHN_SCORE_FIXED_60`: ADAPTED, not retained as production truth.
- No feature candidate is promoted by this report.