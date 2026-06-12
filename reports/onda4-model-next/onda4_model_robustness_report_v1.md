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
| M3 | Challenger lift | PASS | null_mae=2.8120; challenger_mae=1.2708; lift=1.5411; challenger_failures=0 | EXPERIMENT_ONLY |
| M4 | Temporal robustness | PASS | first_review_single_test_year_recorded | EXPERIMENT_ONLY |
| M5 | Slice robustness | PASS | low_support_slices=0 | EXPERIMENT_ONLY |
| M6 | Uncertainty and abstention | PASS | p50=1.0805; p90=3.1088; has_rule=True | EXPERIMENT_ONLY |
| M7 | Anti-nowcast/model timing | PASS | target_proxy_columns_blocked_by_manifest | EXPERIMENT_ONLY |
| M8 | Decision hygiene | PASS | onda3_decision=READY_FOR_ONDA4_MODEL_RERUN | EXPERIMENT_ONLY |

## Input Audit

| artifact | present | rows | production_status |
| --- | --- | --- | --- |
| baseline_results | True | 4 | EXPERIMENT_ONLY |
| challenger_results | True | 4 | EXPERIMENT_ONLY |
| decision | True | 1 | EXPERIMENT_ONLY |
| design_matrix_audit | True | 1 | EXPERIMENT_ONLY |
| feature_manifest | True | 26 | EXPERIMENT_ONLY |
| slice_diagnostics | True | 6 | EXPERIMENT_ONLY |
| uncertainty | True | 4 | EXPERIMENT_ONLY |

## Slice Review

| slice_column | slice_value | rows | mae | production_status |
| --- | --- | --- | --- | --- |
| cp | 20:00 | 519 | 1.3760822291051822 | EXPERIMENT_ONLY |
| cp | 21:00 | 519 | 1.3119629668574013 | EXPERIMENT_ONLY |
| cp | 22:00 | 519 | 1.19807910746778 | EXPERIMENT_ONLY |
| cp | 23:00 | 519 | 1.1972739153096004 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_non_southerly | 1458 | 1.2501869908525016 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_southerly_flow | 618 | 1.3195971567363989 | EXPERIMENT_ONLY |

## Uncertainty Review

| model_name | cp | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status |
| --- | --- | --- | --- | --- | --- |
| ridge_challenger | 20:00 | 1.080473382258912 | 3.1087621394342 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 21:00 | 1.0218326486417624 | 2.7299561452756658 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 22:00 | 0.9039723772665376 | 2.6685467500499027 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 23:00 | 0.9122617536859075 | 2.6727240199248605 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |

## Scope

All outputs are EXPERIMENT_ONLY. This report does not approve production, deployment, or financial execution.
