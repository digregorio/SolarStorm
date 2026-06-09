# Onda 2E Prerequisite EDA - 2026-06-07

Source atlas: `reports/onda2e/thesis_atlas_v1.md`

Theses parsed: 251
Blocked external-data theses: 6

## Artifact Summary

| Artifact | Rows | Columns |
|---|---:|---:|
| `power_map` | 228 | 5 |
| `regime_frequency` | 228 | 6 |
| `monthly_wind_rose` | 412 | 8 |
| `tmax_hour_distribution` | 57 | 8 |
| `remaining_warming_distribution` | 228 | 9 |
| `cooling_mechanism_taxonomy` | 408 | 10 |
| `tmax_anomaly_by_month` | 12 | 8 |

## Initial Findings

- Month x regime x CP cells audited: 228.
- Underpowered cells (`n < 30`): 113.
- Registry-detail gaps in the official atlas: 22.
- External-data blocked theses: 6.

### Regime Row Totals

| Regime | Rows |
|---|---:|
| southerly_disrupted | 17308 |
| standard_nw | 2466 |
| strong_nw_foehn | 1309 |
| calm_radiative | 625 |
| insufficient | 116 |

### Monthly Wind Rose Totals

| Wind sector | Observations |
|---|---:|
| N | 204807 |
| S | 87444 |
| NE | 51628 |
| SE | 20163 |
| NW | 13610 |
| SW | 12660 |
| E | 6738 |
| W | 3270 |
| unknown | 55 |

### Cooling Mechanism Taxonomy Totals

| Cooling mechanism | Rows |
|---|---:|
| no_material_cooling | 19513 |
| radiative_pre_dawn | 988 |
| southerly_frontal | 552 |
| ambiguous_cooling | 507 |
| post_dawn_advective | 158 |
| insufficient_obs | 106 |

### Registry Gaps

| Domain | Missing thesis details |
|---|---:|
| IX | 20 |
| TIMING | 2 |

## Testability Summary

| Domain | Testability | Theses |
|---|---|---:|
| CLOUD | available_eda | 15 |
| COOLING | priority_eda | 20 |
| CP | available_eda | 8 |
| DQ | available_eda | 8 |
| FOEHN | available_eda | 15 |
| GAP | blocked_external_data | 5 |
| GAP | gap_audit | 45 |
| HUM | available_eda | 12 |
| IX | registry_missing_detail | 20 |
| PRES | blocked_external_data | 1 |
| PRES | priority_eda | 11 |
| RAIN | priority_eda | 15 |
| REGIME | priority_eda | 20 |
| SPIKE | available_eda | 18 |
| TIMING | priority_eda | 16 |
| TIMING | registry_missing_detail | 2 |
| WIND | priority_eda | 20 |

## Method Guardrail

These artifacts are descriptive EDA prerequisites. They do not promote theses into features, change production regime labels, or relax Onda 4 gates.