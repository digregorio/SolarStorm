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
| M3 | Challenger lift | PASS | null_mae=2.9522; challenger_mae=1.1726; lift=1.7796; challenger_failures=0 | EXPERIMENT_ONLY |
| M4 | Temporal robustness | PASS | rolling_temporal_diagnostics; test_years=2023,2024,2025 | EXPERIMENT_ONLY |
| M5 | Slice robustness | PASS | low_support_slices=0 | EXPERIMENT_ONLY |
| M6 | Uncertainty and abstention | PASS | p50=1.0198; p90=2.6165; has_rule=True | EXPERIMENT_ONLY |
| M7 | Anti-nowcast/model timing | PASS | target_proxy_columns_blocked_by_manifest | EXPERIMENT_ONLY |
| M8 | Decision hygiene | PASS | onda3_decision=READY_FOR_ONDA4_MODEL_RERUN | EXPERIMENT_ONLY |

## Input Audit

| artifact | present | rows | production_status |
| --- | --- | --- | --- |
| baseline_results | True | 12 | EXPERIMENT_ONLY |
| challenger_results | True | 12 | EXPERIMENT_ONLY |
| decision | True | 1 | EXPERIMENT_ONLY |
| design_matrix_audit | True | 1 | EXPERIMENT_ONLY |
| feature_manifest | True | 30 | EXPERIMENT_ONLY |
| slice_diagnostics | True | 18 | EXPERIMENT_ONLY |
| uncertainty | True | 12 | EXPERIMENT_ONLY |

## Slice Review

| slice_column | slice_value | rows | mae | production_status | test_year |
| --- | --- | --- | --- | --- | --- |
| cp | 20:00 | 365 | 1.240803655263843 | EXPERIMENT_ONLY | 2023 |
| cp | 21:00 | 365 | 1.160047899655755 | EXPERIMENT_ONLY | 2023 |
| cp | 22:00 | 365 | 1.0756289562734338 | EXPERIMENT_ONLY | 2023 |
| cp | 23:00 | 365 | 1.0842245506158874 | EXPERIMENT_ONLY | 2023 |
| binary_macro_regime_label | macro_non_southerly | 1073 | 1.1465583185261174 | EXPERIMENT_ONLY | 2023 |
| binary_macro_regime_label | macro_southerly_flow | 387 | 1.1224813224334131 | EXPERIMENT_ONLY | 2023 |
| cp | 20:00 | 366 | 1.2982372441222527 | EXPERIMENT_ONLY | 2024 |
| cp | 21:00 | 366 | 1.1935159165818656 | EXPERIMENT_ONLY | 2024 |
| cp | 22:00 | 366 | 1.1272397054576047 | EXPERIMENT_ONLY | 2024 |
| cp | 23:00 | 366 | 1.1225216046022026 | EXPERIMENT_ONLY | 2024 |
| binary_macro_regime_label | macro_non_southerly | 1132 | 1.1768265011162518 | EXPERIMENT_ONLY | 2024 |
| binary_macro_regime_label | macro_southerly_flow | 332 | 1.2145382440843404 | EXPERIMENT_ONLY | 2024 |
| cp | 20:00 | 365 | 1.2903412248060544 | EXPERIMENT_ONLY | 2025 |
| cp | 21:00 | 365 | 1.2381508057435093 | EXPERIMENT_ONLY | 2025 |
| cp | 22:00 | 365 | 1.1228737810053282 | EXPERIMENT_ONLY | 2025 |
| cp | 23:00 | 365 | 1.1176427389790031 | EXPERIMENT_ONLY | 2025 |
| binary_macro_regime_label | macro_non_southerly | 1020 | 1.194455081661377 | EXPERIMENT_ONLY | 2025 |
| binary_macro_regime_label | macro_southerly_flow | 440 | 1.1871453128415161 | EXPERIMENT_ONLY | 2025 |

## Uncertainty Review

| model_name | cp | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status | test_year |
| --- | --- | --- | --- | --- | --- | --- |
| ridge_challenger | 20:00 | 1.0197955888048575 | 2.616484006216139 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 21:00 | 0.9422588212715368 | 2.4624039076709336 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 22:00 | 0.9517349138738211 | 2.098599677066738 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 23:00 | 0.95997306645382 | 2.1107945222754836 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 20:00 | 1.1616943853483264 | 2.5774650630853913 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 21:00 | 1.0422322173033214 | 2.352103766089974 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 22:00 | 0.9682918306156072 | 2.2291489760723584 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 23:00 | 0.9458977017692414 | 2.2560661192151414 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 20:00 | 0.9781822961939675 | 2.8004205675733913 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 21:00 | 1.0156861784099576 | 2.5048021116885626 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 22:00 | 0.9158584320651322 | 2.3969561045088654 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 23:00 | 0.8983072471063274 | 2.3828993861633205 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |

## Scope

All outputs are EXPERIMENT_ONLY. This report does not approve production, deployment, or financial execution.
