# Onda 2E-Gate Decision Report - 2026-06-07

No thesis is promoted by prerequisite EDA alone.
Descriptive artifacts become actionable only after ADR-012 decision records resolve evidence, power, causality, and leakage.

## Summary

- Thesis decisions: 245
- Blocked thesis decisions: 0
- Baseline-register entries: 5
- Active quarantined decision rows: 2
- Regime design queue items: 9
- Feature candidate queue items: 0
- Rejected items: 22

## Decision Status Counts

| Status | Rows |
|---|---:|
| ADAPTED | 48 |
| PROMOTED_TO_REGIME_DESIGN | 4 |
| QUARANTINED_BASELINE | 2 |
| REJECTED | 22 |
| SUPPORTED | 174 |

## Required Registers

| Artifact | Rows |
|---|---:|
| `evidence_decision_register.csv` | 250 |
| `regime_design_queue.csv` | 9 |
| `feature_candidate_queue.csv` | 0 |
| `rejection_register.csv` | 22 |
| `quarantined_baseline_register.csv` | 5 |

## Baseline Comparator Register

Active quarantine is counted separately in the decision register. This table lists deprecated or provisional rules kept only as diagnostic comparators.

| Rule | Domain | Reason |
|---|---|---|
| `REGIME_CLASSIFIER_CURRENT` | REGIME | Retain only as a diagnostic comparator until Wellington climatology resolves stable physical classes. |
| `RULE_LATE_WARMING_FIXED_18` | TIMING | Fixed timing is useful only as a deprecated diagnostic reference, not production truth. |
| `RULE_COOLING_FIXED_MINUS_2_C_PER_H` | COOLING | The threshold mixed several physical cooling mechanisms and cannot justify regime design by itself. |
| `RULE_FOEHN_SCORE_FIXED_60` | FOEHN | Keep as an audit threshold only until the Onda 2E foehn theses resolve calibration. |
| `RULE_ONDA2R_PHYSICAL_REGIME_FAMILY` | REGIME | Treat as baseline ontology to investigate, not as authority to unlock model work. |

## Gate Consequence

Domain EDA has resolved the active local thesis backlog. Onda 4 remains blocked until the regime-design queue produces and validates a data-backed regime repair; no production feature, model input, or classifier is promoted here.