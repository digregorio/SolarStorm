# Onda C Regime Classifiability Report - 2026-06-08

> [!IMPORTANT]
> Onda C is non-production. This is a classifiability benchmark and not a production classifier.
> Onda 3 remains blocked unless Onda C returns `READY_FOR_ONDA3_DESIGN_REVIEW`.
> Onda C comes before Onda 3.

## Overall Decision Status

- **Verdict**: `BLOCK_ONDA_C_PROMOTION`
- **Next Allowed Action**: Onda C promotion is blocked. Investigate failures, leakage, or accidental production artifacts.

## Method Comparison Summary

| Method | Candidate Version | Macro Count | Dead Regimes | Coverage Share | Low Confidence Share | Mean Entropy | Mean Margin | Decision Update |
|---|---|---|---|---|---|---|---|---|
| `distance_softmax_v2` | `v2` | 3 | 0 | 1.0000 | 0.9317 | 1.3620 | 0.2820 | `KEEP_IN_REGIME_DESIGN_REVIEW` |
| `distance_softmax_v22` | `v2.2` | 3 | 0 | 1.0000 | 0.8226 | 1.2082 | 0.3303 | `BLOCK_ONDA_C_PROMOTION` |
| `train_only_gmm` | `v2.2` | 3 | 0 | 1.0000 | 0.1370 | 0.2484 | 0.7906 | `BLOCK_ONDA_C_PROMOTION` |
| `som_topological` | `v2.2` | 3 | 0 | 1.0000 | 0.0000 | 0.0000 | 0.8360 | `BLOCK_ONDA_C_PROMOTION` |
| `michelangeli_stability` | `v2.2` | 3 | 0 | 1.0000 | 0.0002 | 0.0000 | 0.8360 | `BLOCK_ONDA_C_PROMOTION` |

## Blocking Evidence

- `distance_softmax_v2` has protected regression or missing protected macro coverage.
- `distance_softmax_v2` has low confidence share 0.9317.
- `distance_softmax_v2` has stability score 0.5142, below the review threshold.
- `distance_softmax_v2` has weak classifiability score -0.0347.
- `distance_softmax_v22` has low confidence share 0.8226.
- `distance_softmax_v22` has stability score 0.6154, below the review threshold.
- `distance_softmax_v22` has weak classifiability score 0.0539.
- `train_only_gmm` has stability score 0.0799, below the review threshold.
- `train_only_gmm` has weak classifiability score 0.0933.
- `som_topological` has stability score 0.5235, below the review threshold.
- `som_topological` has weak classifiability score 0.0975.
- `michelangeli_stability` has stability score 0.5235, below the review threshold.
- `michelangeli_stability` has weak classifiability score 0.0975.

## Diagnostic Guardrails Status

| Diagnostic Item | Status | Detail | n_rows |
|---|---|---|---|
| non-production status guardrail | **PASS** | All inputs are NOT_PRODUCTION or EXPERIMENT_ONLY | 0 |
| no Onda 3 training artifact produced | **PASS** | No model files created | 0 |
| train/test leakage check | **PASS** | Train/test split is causal by date | 0 |
| causal-window check | **PASS** | All causal windows are valid < CP | 0 |
| duplicate method/date/CP assignment check | **PASS** | No duplicates found | 0 |
| protected macros present | **PASS** | Protected macros present in v2.2 | 3 |
| candidate comparison gate | **FAIL** | v2.2 is blocked before Onda C promotion by its comparison gate. | 7 |
| candidate comparison loaded | **PASS** | Comparison snapshot is loaded for v2.2 | 0 |
| candidate under review acknowledged | **PASS** | Onda C is evaluating v2.2 | 21824 |
| physical_feature_basis_loaded | **PASS** | Onda C used the approved physical meteorological feature basis. | 8 |
| obs_labels_features_join_valid | **PASS** | Classifiability features joined to regime assignments by (date_local, cp) without duplicate assignment keys. | 21824 |
| approved_physical_feature_count | **PASS** | 8 approved physical features survived preprocessing. | 8 |
| forbidden_numeric_fallback_not_used | **PASS** | Unrestricted numeric fallback is disabled for physical regime classifiability. | 0 |
| outcome_columns_excluded | **PASS** | 0 outcome columns were included. | 0 |
| quarantined_labels_excluded | **PASS** | 0 quarantined label columns were included. | 0 |