# Onda 2E Wind Domain EDA - 2026-06-07

No production classifier change is made by this report.
No feature candidate is promoted by wind-domain EDA.

## Artifacts

| Artifact | Rows |
|---|---:|
| `wind_sector_effects_by_month_cp.csv` | 412 |
| `wind_direction_reliability_by_day_cp.csv` | 21824 |
| `wind_power_leakage_audit.csv` | 3 |
| `wind_regime_repair_candidates.csv` | 1 |

## Power

- Underpowered wind-sector cells (`n_obs < 30`): 28/412.

## Decision Implication

- `WCT-WIND-006`: SUPPORTED as descriptive wind-sector evidence.
- `WCT-WIND-019`: eligible only for regime-design review when southerly counts are present.