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
| M3 | Challenger lift | PASS | null_mae=2.9522; challenger_mae=1.2026; lift=1.7496; challenger_failures=0 | EXPERIMENT_ONLY |
| M4 | Temporal robustness | PASS | rolling_temporal_diagnostics; test_years=2023,2024,2025 | EXPERIMENT_ONLY |
| M5 | Slice robustness | PASS | low_support_slices=0 | EXPERIMENT_ONLY |
| M6 | Uncertainty and abstention | PASS | p50=1.1292; p90=2.8582; has_rule=True | EXPERIMENT_ONLY |
| M7 | Anti-nowcast/model timing | PASS | target_proxy_columns_blocked_by_manifest | EXPERIMENT_ONLY |
| M8 | Decision hygiene | PASS | onda3_decision=READY_FOR_ONDA4_MODEL_RERUN | EXPERIMENT_ONLY |

## Input Audit

| artifact | present | rows | production_status |
| --- | --- | --- | --- |
| baseline_results | True | 12 | EXPERIMENT_ONLY |
| challenger_results | True | 12 | EXPERIMENT_ONLY |
| decision | True | 1 | EXPERIMENT_ONLY |
| design_matrix_audit | True | 1 | EXPERIMENT_ONLY |
| feature_manifest | True | 26 | EXPERIMENT_ONLY |
| slice_diagnostics | True | 18 | EXPERIMENT_ONLY |
| uncertainty | True | 12 | EXPERIMENT_ONLY |

## Slice Review

| slice_column | slice_value | rows | mae | production_status | test_year |
| --- | --- | --- | --- | --- | --- |
| cp | 20:00 | 365 | 1.3284799607654607 | EXPERIMENT_ONLY | 2023 |
| cp | 21:00 | 365 | 1.2115345202493062 | EXPERIMENT_ONLY | 2023 |
| cp | 22:00 | 365 | 1.125319484449512 | EXPERIMENT_ONLY | 2023 |
| cp | 23:00 | 365 | 1.1206958953579043 | EXPERIMENT_ONLY | 2023 |
| binary_macro_regime_label | macro_non_southerly | 1073 | 1.1921368613658314 | EXPERIMENT_ONLY | 2023 |
| binary_macro_regime_label | macro_southerly_flow | 387 | 1.2086254443270277 | EXPERIMENT_ONLY | 2023 |
| cp | 20:00 | 366 | 1.3368947066521863 | EXPERIMENT_ONLY | 2024 |
| cp | 21:00 | 366 | 1.20568745437114 | EXPERIMENT_ONLY | 2024 |
| cp | 22:00 | 366 | 1.1361141378350192 | EXPERIMENT_ONLY | 2024 |
| cp | 23:00 | 366 | 1.1394583343799842 | EXPERIMENT_ONLY | 2024 |
| binary_macro_regime_label | macro_non_southerly | 1132 | 1.1803708059747904 | EXPERIMENT_ONLY | 2024 |
| binary_macro_regime_label | macro_southerly_flow | 332 | 1.2869422994029076 | EXPERIMENT_ONLY | 2024 |
| cp | 20:00 | 365 | 1.308204786317765 | EXPERIMENT_ONLY | 2025 |
| cp | 21:00 | 365 | 1.2580350789080306 | EXPERIMENT_ONLY | 2025 |
| cp | 22:00 | 365 | 1.128880081259754 | EXPERIMENT_ONLY | 2025 |
| cp | 23:00 | 365 | 1.131564035795828 | EXPERIMENT_ONLY | 2025 |
| binary_macro_regime_label | macro_non_southerly | 1020 | 1.21452546382221 | EXPERIMENT_ONLY | 2025 |
| binary_macro_regime_label | macro_southerly_flow | 440 | 1.188462910077384 | EXPERIMENT_ONLY | 2025 |

## Uncertainty Review

| model_name | cp | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status | test_year |
| --- | --- | --- | --- | --- | --- | --- |
| ridge_challenger | 20:00 | 1.1291844988369846 | 2.858215818923812 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 21:00 | 1.018076828326917 | 2.444494155577822 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 22:00 | 1.014340574512488 | 2.2057543613587995 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 23:00 | 1.0105022883037762 | 2.1900259066959173 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 20:00 | 1.1087160744006814 | 2.6406769786890756 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 21:00 | 1.021931640197205 | 2.317888429446329 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 22:00 | 0.9946415694236741 | 2.3513607574155007 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 23:00 | 0.9870147637713842 | 2.3648353525157733 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 20:00 | 1.0448326620189015 | 2.859526124394116 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 21:00 | 0.9804263775583113 | 2.646886473817554 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 22:00 | 0.8651023712550057 | 2.3664911905966792 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 23:00 | 0.8510065419274699 | 2.376207881632381 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY | 2025 |

## Scope

All outputs are EXPERIMENT_ONLY. This report does not approve production, deployment, or financial execution.
