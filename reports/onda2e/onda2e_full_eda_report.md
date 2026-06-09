# Onda 2E Full EDA Sprint Report - 2026-06-07

No production feature, model, or regime classifier is promoted by this sprint.
Every active local thesis receives an individual review row backed by an ADR-012 decision.

## Thesis Review Coverage

- Thesis rows reviewed: 245
- Unique thesis IDs: 245

| Review status | Rows |
|---|---:|
| ADAPTED_DOMAIN_EVIDENCE | 45 |
| READY_FOR_REGIME_DESIGN_REVIEW | 4 |
| REJECTED_BY_DOMAIN_EVIDENCE | 22 |
| SUPPORTED_DESCRIPTIVE_EVIDENCE | 174 |

## Regime Architecture EDA

- K-selection rows: 80
- Year-stability rows: 240
- Physical-interpretation rows: 320
- Regime-design candidate rows: 96
- Blocked next-experiment rows: 0
- Clustering inputs use pre-CP observations only (`valid < CP`).
- Tmax anomaly and remaining warming are external audits only.

| Stratum | Best k by BIC | n rows | eta2 Tmax anomaly | underpowered? |
|---|---:|---:|---:|---|
| month=1 | 6 | 1623 | 0.270 | False |
| month=10 | 6 | 1595 | 0.338 | False |
| month=11 | 6 | 1580 | 0.313 | False |
| month=12 | 6 | 1705 | 0.217 | False |
| month=2 | 6 | 1514 | 0.365 | False |
| month=3 | 6 | 1727 | 0.289 | False |
| month=4 | 6 | 1608 | 0.360 | False |
| month=5 | 6 | 1695 | 0.358 | False |
| month=6 | 6 | 1558 | 0.269 | False |
| month=7 | 6 | 1535 | 0.438 | False |
| month=8 | 6 | 1576 | 0.398 | False |
| month=9 | 6 | 1544 | 0.388 | False |
| season=DJF | 6 | 4842 | 0.279 | False |
| season=JJA | 6 | 4669 | 0.372 | False |
| season=MAM | 6 | 5030 | 0.347 | False |
| season=SON | 6 | 4719 | 0.351 | False |

## Leakage Audit

| Audit item | Status | Detail |
|---|---|---|
| clustering_inputs | PASS | All included clustering inputs are aggregated from observations with valid < CP. |
| outcome_exclusion | PASS | tmax_int, tmax_hour, remaining_warming, and tmax_anomaly are excluded from clustering and used only for external audit. |
| baseline_regime_exclusion | PASS | Current regime_label and regime_flags are excluded from clustering to avoid learning the quarantined ontology. |
| power | PASS | Cluster matrix contains 21824 date/CP rows before null filtering. |

## Next Gate Action

Use the regime-design queue to build and validate a data-backed regime repair. Onda 4 remains blocked until that repair is designed, interpreted, and rerun.