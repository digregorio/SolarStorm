# Onda 4 Model Robustness Report

Generated: 2026-06-09

## Decision

| decision_status | blocked_gates | decision_rationale | production_status |
| --- | --- | --- | --- |
| READY_FOR_ONDA3_NEXT_MODEL_ITERATION |  | Onda 4 model robustness review completed against M1-M8 gates. | EXPERIMENT_ONLY |

## Gate Results

| gate_id | gate_name | gate_status | detail | production_status |
| --- | --- | --- | --- | --- |
| M1 | Input artifact integrity | PASS | missing_or_empty=0 | EXPERIMENT_ONLY |
| M2 | Causal manifest safety | PASS | included_blocked_target_or_proxy=0 | EXPERIMENT_ONLY |
| M3 | Challenger lift | PASS | null_mae=2.8120; challenger_mae=1.3487; lift=1.4632 | EXPERIMENT_ONLY |
| M4 | Temporal robustness | PASS | first_review_single_test_year_recorded | EXPERIMENT_ONLY |
| M5 | Slice robustness | PASS | low_support_slices=0 | EXPERIMENT_ONLY |
| M6 | Uncertainty and abstention | PASS | p50=1.0315; p90=2.9818; has_rule=True | EXPERIMENT_ONLY |
| M7 | Anti-nowcast/model timing | PASS | target_proxy_columns_blocked_by_manifest | EXPERIMENT_ONLY |
| M8 | Decision hygiene | PASS | onda3_decision=READY_FOR_ONDA4_MODEL_RERUN | EXPERIMENT_ONLY |

## Input Audit

| artifact | present | rows | production_status |
| --- | --- | --- | --- |
| baseline_results | True | 1 | EXPERIMENT_ONLY |
| challenger_results | True | 1 | EXPERIMENT_ONLY |
| decision | True | 1 | EXPERIMENT_ONLY |
| design_matrix_audit | True | 1 | EXPERIMENT_ONLY |
| feature_manifest | True | 26 | EXPERIMENT_ONLY |
| slice_diagnostics | True | 6 | EXPERIMENT_ONLY |
| uncertainty | True | 1 | EXPERIMENT_ONLY |

## Slice Review

| slice_column | slice_value | rows | target_mean | production_status |
| --- | --- | --- | --- | --- |
| cp | 20:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 21:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 22:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 23:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_non_southerly | 16298 | 17.57559209718984 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_southerly_flow | 5526 | 15.004162142598625 | EXPERIMENT_ONLY |

## Uncertainty Review

| model_name | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status |
| --- | --- | --- | --- | --- |
| ridge_challenger | 1.0314621789651444 | 2.981763035114538 | abstain when slice support or interval calibration fails | EXPERIMENT_ONLY |

## Scope

All outputs are EXPERIMENT_ONLY. This report does not approve production, deployment, or financial execution.
