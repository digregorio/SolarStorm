# Onda 3H Nested Validation Report

Generated: 2026-06-09



Scope: pre-Open-Meteo local-data nested validation. Open-Meteo forecast data is not integrated.

All outputs remain EXPERIMENT_ONLY.

## Decision

| decision_status | decision_rationale | n_outer_folds | selected_mean_test_mae | always_onda3d_mean_test_mae | always_onda3f_mean_test_mae | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS | Nested validation selected Onda 3F consistently; keep the nested harness as the model-selection gate before any Open-Meteo work. | 3 | 1.062 | 1.170 | 1.062 | EXPERIMENT_ONLY |

## Fold Scope

| stage | outer_test_year | evaluation_year | train_start | train_end | train_start_year | train_end_year | evaluation_start | evaluation_end | n_train_rows | n_evaluation_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 2023 | 2022 | 2012-01-01 | 2021-12-31 | 2012 | 2021 | 2022-01-01 | 2022-12-31 | 14584 | 1460 | EXPERIMENT_ONLY |
| test | 2023 | 2023 | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 16044 | 1460 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 16044 | 1460 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | 2012-01-01 | 2023-12-31 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 17504 | 1464 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | 2012-01-01 | 2023-12-31 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 17504 | 1464 | EXPERIMENT_ONLY |
| test | 2025 | 2025 | 2012-01-01 | 2024-12-31 | 2012 | 2024 | 2025-01-01 | 2025-12-31 | 18968 | 1460 | EXPERIMENT_ONLY |

## Validation Selection

| outer_test_year | validation_year | selected_candidate_id | selected_candidate_label | selected_validation_mae | selected_validation_any_cp_exact_pct | selected_validation_cp23_exact_pct | selected_test_mae | selected_test_any_cp_exact_pct | selected_test_cp23_exact_pct | validation_candidate_count | test_candidate_count | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 2022 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.107 | 40.000 | 27.945 | 1.040 | 44.932 | 31.781 | 2 | 2 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |
| 2024 | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.040 | 44.932 | 31.781 | 1.070 | 43.716 | 31.148 | 2 | 2 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |
| 2025 | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.070 | 43.716 | 31.148 | 1.077 | 43.836 | 30.411 | 2 | 2 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |

## Selected Test Summary

| outer_test_year | evaluation_year | candidate_id | candidate_label | mae | any_cp_exact_pct | cp23_exact_pct | n_days_with_cp23 | cp23_exact_days | n_days | n_cp_rows | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.040 | 44.932 | 31.781 | 365 | 116 | 365 | 1460 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |
| 2024 | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.070 | 43.716 | 31.148 | 366 | 114 | 366 | 1464 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |
| 2025 | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.077 | 43.836 | 30.411 | 365 | 111 | 365 | 1460 | validation_mae_then_cp23_exact_then_onda3d | EXPERIMENT_ONLY |

## Candidate Metric Summary

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | n_days | n_cp_rows | mae | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2023 | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 365 | 1460 | 1.137 | 45.753 | 365 | 109 | 29.863 | EXPERIMENT_ONLY | 25.753 | 26.027 | 29.863 | 29.863 |
| test | 2023 | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 365 | 1460 | 1.040 | 44.932 | 365 | 116 | 31.781 | EXPERIMENT_ONLY | 28.493 | 32.877 | 32.603 | 31.781 |
| validation | 2023 | 2022 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 365 | 1460 | 1.215 | 44.110 | 365 | 104 | 28.493 | EXPERIMENT_ONLY | 25.205 | 27.123 | 29.589 | 28.493 |
| validation | 2023 | 2022 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 365 | 1460 | 1.107 | 40.000 | 365 | 102 | 27.945 | EXPERIMENT_ONLY | 25.753 | 26.301 | 28.767 | 27.945 |
| test | 2024 | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 366 | 1464 | 1.184 | 42.896 | 366 | 100 | 27.322 | EXPERIMENT_ONLY | 25.956 | 27.322 | 27.596 | 27.322 |
| test | 2024 | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 366 | 1464 | 1.070 | 43.716 | 366 | 114 | 31.148 | EXPERIMENT_ONLY | 27.869 | 30.328 | 29.508 | 31.148 |
| validation | 2024 | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 365 | 1460 | 1.137 | 45.753 | 365 | 109 | 29.863 | EXPERIMENT_ONLY | 25.753 | 26.027 | 29.863 | 29.863 |
| validation | 2024 | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 365 | 1460 | 1.040 | 44.932 | 365 | 116 | 31.781 | EXPERIMENT_ONLY | 28.493 | 32.877 | 32.603 | 31.781 |
| test | 2025 | 2025 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 365 | 1460 | 1.190 | 46.575 | 365 | 118 | 32.329 | EXPERIMENT_ONLY | 26.027 | 29.589 | 33.973 | 32.329 |
| test | 2025 | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 365 | 1460 | 1.077 | 43.836 | 365 | 111 | 30.411 | EXPERIMENT_ONLY | 27.123 | 29.041 | 31.507 | 30.411 |
| validation | 2025 | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 366 | 1464 | 1.184 | 42.896 | 366 | 100 | 27.322 | EXPERIMENT_ONLY | 25.956 | 27.322 | 27.596 | 27.322 |
| validation | 2025 | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 366 | 1464 | 1.070 | 43.716 | 366 | 114 | 31.148 | EXPERIMENT_ONLY | 27.869 | 30.328 | 29.508 | 31.148 |

## Regime Performance

| stage | outer_test_year | candidate_id | candidate_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1073 | 276 | 1.143 | 26.934 | EXPERIMENT_ONLY |
| test | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 387 | 104 | 1.120 | 30.491 | EXPERIMENT_ONLY |
| test | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1073 | 276 | 1.034 | 31.128 | EXPERIMENT_ONLY |
| test | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 387 | 104 | 1.057 | 32.300 | EXPERIMENT_ONLY |
| validation | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1029 | 264 | 1.215 | 28.474 | EXPERIMENT_ONLY |
| validation | 2023 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 431 | 117 | 1.215 | 25.522 | EXPERIMENT_ONLY |
| validation | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1029 | 264 | 1.178 | 25.656 | EXPERIMENT_ONLY |
| validation | 2023 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 431 | 117 | 0.939 | 30.858 | EXPERIMENT_ONLY |
| test | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1132 | 292 | 1.176 | 26.413 | EXPERIMENT_ONLY |
| test | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 332 | 94 | 1.213 | 29.217 | EXPERIMENT_ONLY |
| test | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1132 | 292 | 1.064 | 29.064 | EXPERIMENT_ONLY |
| test | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 332 | 94 | 1.091 | 31.928 | EXPERIMENT_ONLY |
| validation | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1073 | 276 | 1.143 | 26.934 | EXPERIMENT_ONLY |
| validation | 2024 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 387 | 104 | 1.120 | 30.491 | EXPERIMENT_ONLY |
| validation | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1073 | 276 | 1.034 | 31.128 | EXPERIMENT_ONLY |
| validation | 2024 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 387 | 104 | 1.057 | 32.300 | EXPERIMENT_ONLY |
| test | 2025 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1020 | 265 | 1.192 | 30.294 | EXPERIMENT_ONLY |
| test | 2025 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 440 | 121 | 1.185 | 30.909 | EXPERIMENT_ONLY |
| test | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1020 | 265 | 1.108 | 27.941 | EXPERIMENT_ONLY |
| test | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 440 | 121 | 1.005 | 33.182 | EXPERIMENT_ONLY |
| validation | 2025 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 1132 | 292 | 1.176 | 26.413 | EXPERIMENT_ONLY |
| validation | 2025 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 332 | 94 | 1.213 | 29.217 | EXPERIMENT_ONLY |
| validation | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 1132 | 292 | 1.064 | 29.064 | EXPERIMENT_ONLY |
| validation | 2025 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 332 | 94 | 1.091 | 31.928 | EXPERIMENT_ONLY |

## Interpretation

- Validation uses train years ending at Y-2.
- Test uses the validation-selected design refit through Y-1.
- Onda 3H is a model-selection gate, not a production promotion.
