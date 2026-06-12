# Onda 3G Audit Comparison Report

Generated: 2026-06-09



Scope: pre-Open-Meteo local-data audit comparison. Open-Meteo forecast data is not integrated.

All outputs remain EXPERIMENT_ONLY.

## Decision

| decision_status | decision_rationale | onda3f_minus_onda3d_mae | onda3f_minus_onda3d_any_cp_exact_pct | onda3f_minus_onda3d_cp23_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- |
| CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION | Onda 3F materially improves MAE but trades off at least one exact-bracket headline metric versus Onda 3D. | -0.111 | -0.730 | 1.551 | EXPERIMENT_ONLY |

## Model Summary

| model_rank_by_mae | iteration_id | iteration_label | n_days | n_cp_rows | mae | any_cp_exact_pct | cp23_exact_pct | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 1096 | 4384 | 1.173 | 45.164 | 29.927 | 26.095 | 27.099 | 30.566 | 29.927 | EXPERIMENT_ONLY |
| 2 | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 1096 | 4384 | 1.170 | 45.073 | 29.836 | 25.912 | 27.646 | 30.474 | 29.836 | EXPERIMENT_ONLY |
| 4 | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 1096 | 4384 | 1.173 | 45.164 | 29.927 | 26.095 | 27.099 | 30.566 | 29.927 | EXPERIMENT_ONLY |
| 1 | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1096 | 4384 | 1.062 | 44.434 | 31.478 | 28.650 | 31.569 | 31.934 | 31.478 | EXPERIMENT_ONLY |

## Pairwise Delta Versus Onda 3D

| comparison_id | reference_iteration_id | candidate_iteration_id | reference_mae | candidate_mae | mae_delta | any_cp_exact_pct_delta | cp23_exact_pct_delta | production_status | cp_2000_exact_pct_delta | cp_2100_exact_pct_delta | cp_2200_exact_pct_delta | cp_2300_exact_pct_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_e_legacy_minus_onda3_d | onda3_d_binary_macro_interactions | onda3_e_legacy_2009_start | 1.173 | 1.173 | 0.000 | 0.000 | 0.000 | EXPERIMENT_ONLY | 0.000 | 0.000 | 0.000 | 0.000 |
| onda3_e_continuous_minus_onda3_d | onda3_d_binary_macro_interactions | onda3_e_continuous_2012_start | 1.173 | 1.170 | -0.002 | -0.091 | -0.091 | EXPERIMENT_ONLY | -0.182 | 0.547 | -0.091 | -0.091 |
| onda3_f_minus_onda3_d | onda3_d_binary_macro_interactions | onda3_f_pooled_temporal_regime | 1.173 | 1.062 | -0.111 | -0.730 | 1.551 | EXPERIMENT_ONLY | 2.555 | 4.471 | 1.369 | 1.551 |

## By Year

| iteration_id | iteration_label | test_year | n_cp_rows | n_days | mae | exact_bracket_pct | any_cp_exact_pct | cp23_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023 | 1460 | 365 | 1.140 | 28.082 | 46.301 | 30.137 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024 | 1464 | 366 | 1.185 | 26.844 | 42.077 | 27.049 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025 | 1460 | 365 | 1.192 | 30.342 | 47.123 | 32.603 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023 | 1460 | 365 | 1.137 | 27.877 | 45.753 | 29.863 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024 | 1464 | 366 | 1.184 | 27.049 | 42.896 | 27.322 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025 | 1460 | 365 | 1.190 | 30.479 | 46.575 | 32.329 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023 | 1460 | 365 | 1.140 | 28.082 | 46.301 | 30.137 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2024 | 1464 | 366 | 1.185 | 26.844 | 42.077 | 27.049 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2025 | 1460 | 365 | 1.192 | 30.342 | 47.123 | 32.603 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023 | 1460 | 365 | 1.043 | 31.575 | 44.110 | 32.603 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024 | 1464 | 366 | 1.066 | 31.352 | 46.175 | 31.148 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025 | 1460 | 365 | 1.077 | 29.795 | 43.014 | 30.685 | EXPERIMENT_ONLY |

## By Month

| iteration_id | iteration_label | month | n_days | any_cp_exact_days | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 28 | 10 | 35.714 | 28 | 9 | 32.143 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 30 | 15 | 50.000 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 31 | 18 | 58.065 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 31 | 12 | 38.710 | 31 | 7 | 22.581 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 30 | 19 | 63.333 | 30 | 12 | 40.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 31 | 12 | 38.710 | 31 | 5 | 16.129 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 30 | 13 | 43.333 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 31 | 8 | 25.806 | 31 | 5 | 16.129 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 29 | 9 | 31.034 | 29 | 7 | 24.138 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 31 | 9 | 29.032 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 30 | 16 | 53.333 | 30 | 6 | 20.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 30 | 16 | 53.333 | 30 | 13 | 43.333 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 31 | 15 | 48.387 | 31 | 7 | 22.581 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-09 | 30 | 12 | 40.000 | 30 | 5 | 16.667 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-10 | 31 | 13 | 41.935 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-11 | 30 | 15 | 50.000 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-12 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-01 | 31 | 15 | 48.387 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-02 | 28 | 10 | 35.714 | 28 | 6 | 21.429 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-03 | 31 | 12 | 38.710 | 31 | 12 | 38.710 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-04 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-05 | 31 | 19 | 61.290 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-06 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-07 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-08 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-09 | 30 | 14 | 46.667 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-10 | 31 | 18 | 58.065 | 31 | 14 | 45.161 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-11 | 30 | 17 | 56.667 | 30 | 12 | 40.000 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-12 | 31 | 11 | 35.484 | 31 | 6 | 19.355 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-02 | 28 | 11 | 39.286 | 28 | 9 | 32.143 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-03 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-04 | 30 | 15 | 50.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-05 | 31 | 18 | 58.065 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-07 | 31 | 12 | 38.710 | 31 | 6 | 19.355 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-08 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-09 | 30 | 18 | 60.000 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-10 | 31 | 11 | 35.484 | 31 | 4 | 12.903 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-11 | 30 | 13 | 43.333 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2023-12 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-01 | 31 | 9 | 29.032 | 31 | 6 | 19.355 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-02 | 29 | 9 | 31.034 | 29 | 6 | 20.690 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-03 | 31 | 9 | 29.032 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-04 | 30 | 16 | 53.333 | 30 | 7 | 23.333 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-05 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-06 | 30 | 16 | 53.333 | 30 | 12 | 40.000 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-07 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-08 | 31 | 15 | 48.387 | 31 | 7 | 22.581 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-09 | 30 | 13 | 43.333 | 30 | 4 | 13.333 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-10 | 31 | 14 | 45.161 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-11 | 30 | 15 | 50.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2024-12 | 31 | 11 | 35.484 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-01 | 31 | 15 | 48.387 | 31 | 12 | 38.710 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-02 | 28 | 10 | 35.714 | 28 | 6 | 21.429 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-03 | 31 | 12 | 38.710 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-04 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-05 | 31 | 18 | 58.065 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-06 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-07 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-08 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-09 | 30 | 14 | 46.667 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-10 | 31 | 18 | 58.065 | 31 | 14 | 45.161 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-11 | 30 | 17 | 56.667 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 2025-12 | 31 | 10 | 32.258 | 31 | 7 | 22.581 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-02 | 28 | 10 | 35.714 | 28 | 9 | 32.143 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-03 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-04 | 30 | 15 | 50.000 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-05 | 31 | 18 | 58.065 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-07 | 31 | 12 | 38.710 | 31 | 7 | 22.581 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 2023-08 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |

_Showing 80 of 144 rows. Full table is in CSV._

## By Month And CP

| iteration_id | iteration_label | month | cp | n_cp_rows | exact_bracket_rows | exact_bracket_pct | mae | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 20:00 | 31 | 5 | 16.129 | 1.626 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 21:00 | 31 | 7 | 22.581 | 1.487 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 22:00 | 31 | 11 | 35.484 | 1.351 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 23:00 | 31 | 11 | 35.484 | 1.298 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 20:00 | 28 | 6 | 21.429 | 1.296 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 21:00 | 28 | 5 | 17.857 | 1.123 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 22:00 | 28 | 7 | 25.000 | 0.958 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 23:00 | 28 | 9 | 32.143 | 0.972 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 20:00 | 31 | 7 | 22.581 | 1.220 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 21:00 | 31 | 7 | 22.581 | 1.160 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 22:00 | 31 | 9 | 29.032 | 1.197 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 23:00 | 31 | 9 | 29.032 | 1.232 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 20:00 | 30 | 9 | 30.000 | 1.047 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 21:00 | 30 | 4 | 13.333 | 1.100 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 22:00 | 30 | 10 | 33.333 | 0.865 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 23:00 | 30 | 9 | 30.000 | 0.871 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 20:00 | 31 | 9 | 29.032 | 1.082 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 21:00 | 31 | 11 | 35.484 | 1.062 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 22:00 | 31 | 10 | 32.258 | 1.060 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 23:00 | 31 | 10 | 32.258 | 1.063 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 20:00 | 30 | 15 | 50.000 | 0.885 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 21:00 | 30 | 12 | 40.000 | 0.912 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 22:00 | 30 | 13 | 43.333 | 0.908 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 23:00 | 30 | 11 | 36.667 | 0.999 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 20:00 | 31 | 6 | 19.355 | 1.391 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 21:00 | 31 | 3 | 9.677 | 1.505 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 22:00 | 31 | 6 | 19.355 | 1.188 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 23:00 | 31 | 7 | 22.581 | 1.152 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 20:00 | 31 | 11 | 35.484 | 1.208 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 21:00 | 31 | 9 | 29.032 | 1.216 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 22:00 | 31 | 10 | 32.258 | 1.043 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 23:00 | 31 | 10 | 32.258 | 1.002 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 20:00 | 30 | 11 | 36.667 | 0.913 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 21:00 | 30 | 12 | 40.000 | 0.862 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 22:00 | 30 | 12 | 40.000 | 0.895 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 23:00 | 30 | 12 | 40.000 | 0.911 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 20:00 | 31 | 3 | 9.677 | 1.558 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 21:00 | 31 | 6 | 19.355 | 1.213 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 22:00 | 31 | 7 | 22.581 | 1.211 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 23:00 | 31 | 5 | 16.129 | 1.230 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 20:00 | 30 | 7 | 23.333 | 1.213 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 21:00 | 30 | 8 | 26.667 | 0.970 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 22:00 | 30 | 9 | 30.000 | 0.887 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 23:00 | 30 | 9 | 30.000 | 0.916 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 20:00 | 31 | 6 | 19.355 | 1.426 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 21:00 | 31 | 8 | 25.806 | 1.283 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 22:00 | 31 | 9 | 29.032 | 1.307 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 23:00 | 31 | 8 | 25.806 | 1.334 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 20:00 | 31 | 5 | 16.129 | 2.090 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 21:00 | 31 | 6 | 19.355 | 1.723 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 22:00 | 31 | 5 | 16.129 | 1.728 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 23:00 | 31 | 5 | 16.129 | 1.744 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 20:00 | 29 | 7 | 24.138 | 1.520 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 21:00 | 29 | 4 | 13.793 | 1.471 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 22:00 | 29 | 6 | 20.690 | 1.405 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 23:00 | 29 | 7 | 24.138 | 1.378 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 20:00 | 31 | 6 | 19.355 | 1.405 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 21:00 | 31 | 6 | 19.355 | 1.394 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 22:00 | 31 | 8 | 25.806 | 1.244 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 23:00 | 31 | 8 | 25.806 | 1.211 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 20:00 | 30 | 10 | 33.333 | 0.993 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 21:00 | 30 | 11 | 36.667 | 1.022 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 22:00 | 30 | 8 | 26.667 | 1.074 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 23:00 | 30 | 6 | 20.000 | 1.138 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 20:00 | 31 | 8 | 25.806 | 1.136 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 21:00 | 31 | 6 | 19.355 | 1.061 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 22:00 | 31 | 10 | 32.258 | 0.884 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 23:00 | 31 | 10 | 32.258 | 0.884 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 20:00 | 30 | 8 | 26.667 | 1.217 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 21:00 | 30 | 8 | 26.667 | 1.214 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 22:00 | 30 | 13 | 43.333 | 0.898 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 23:00 | 30 | 13 | 43.333 | 0.891 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 20:00 | 31 | 10 | 32.258 | 1.092 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 21:00 | 31 | 12 | 38.710 | 1.061 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 22:00 | 31 | 10 | 32.258 | 0.910 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 23:00 | 31 | 10 | 32.258 | 0.877 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 20:00 | 31 | 10 | 32.258 | 1.068 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 21:00 | 31 | 9 | 29.032 | 1.076 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 22:00 | 31 | 7 | 22.581 | 1.171 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 23:00 | 31 | 7 | 22.581 | 1.172 | EXPERIMENT_ONLY |

_Showing 80 of 576 rows. Full table is in CSV._

## Binary Macro Regime Performance

| iteration_id | iteration_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_rows | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 3225 | 833 | 1.172 | 901 | 27.938 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 1159 | 319 | 1.173 | 345 | 29.767 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | macro_non_southerly | 3225 | 833 | 1.170 | 897 | 27.814 | EXPERIMENT_ONLY |
| onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | macro_southerly_flow | 1159 | 319 | 1.171 | 351 | 30.285 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | macro_non_southerly | 3225 | 833 | 1.172 | 901 | 27.938 | EXPERIMENT_ONLY |
| onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | macro_southerly_flow | 1159 | 319 | 1.173 | 345 | 29.767 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 3225 | 833 | 1.065 | 984 | 30.512 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 1159 | 319 | 1.054 | 371 | 32.010 | EXPERIMENT_ONLY |

## Binary Macro Regime Winners

| binary_macro_regime_label | winner_iteration_id | winner_iteration_label | winner_mae | winner_exact_bracket_pct | n_cp_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| macro_non_southerly | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.065 | 30.512 | 3225 | EXPERIMENT_ONLY |
| macro_southerly_flow | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1.054 | 32.010 | 1159 | EXPERIMENT_ONLY |

## Local Feature Audit Slices

| slice_id | slice_label | iteration_id | iteration_label | n_cp_rows | n_unique_dates | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calm_radiative_regime_label | regime_label == calm_radiative | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 54 | 16 | 1.661 | 24.074 | EXPERIMENT_ONLY |
| calm_radiative_regime_label | regime_label == calm_radiative | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 54 | 16 | 1.656 | 25.926 | EXPERIMENT_ONLY |
| calm_radiative_regime_label | regime_label == calm_radiative | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 54 | 16 | 1.661 | 24.074 | EXPERIMENT_ONLY |
| calm_radiative_regime_label | regime_label == calm_radiative | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 54 | 16 | 1.113 | 40.741 | EXPERIMENT_ONLY |
| top_quartile_foehn_score | top 25pct rows by foehn_score | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 1096 | 305 | 1.025 | 32.938 | EXPERIMENT_ONLY |
| top_quartile_foehn_score | top 25pct rows by foehn_score | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 1096 | 305 | 1.026 | 32.573 | EXPERIMENT_ONLY |
| top_quartile_foehn_score | top 25pct rows by foehn_score | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 1096 | 305 | 1.025 | 32.938 | EXPERIMENT_ONLY |
| top_quartile_foehn_score | top 25pct rows by foehn_score | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1096 | 305 | 0.926 | 36.131 | EXPERIMENT_ONLY |
| top_quartile_foehn_score_macro_non_southerly | top 25pct rows by foehn_score inside macro_non_southerly | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 1067 | 299 | 0.998 | 33.365 | EXPERIMENT_ONLY |
| top_quartile_foehn_score_macro_non_southerly | top 25pct rows by foehn_score inside macro_non_southerly | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 1067 | 299 | 1.000 | 32.802 | EXPERIMENT_ONLY |
| top_quartile_foehn_score_macro_non_southerly | top 25pct rows by foehn_score inside macro_non_southerly | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 1067 | 299 | 0.998 | 33.365 | EXPERIMENT_ONLY |
| top_quartile_foehn_score_macro_non_southerly | top 25pct rows by foehn_score inside macro_non_southerly | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1067 | 299 | 0.911 | 36.176 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression | top 25pct rows by cloud_cover_suppression | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 1002 | 260 | 1.174 | 27.445 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression | top 25pct rows by cloud_cover_suppression | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 1002 | 260 | 1.173 | 27.046 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression | top 25pct rows by cloud_cover_suppression | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 1002 | 260 | 1.174 | 27.445 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression | top 25pct rows by cloud_cover_suppression | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1002 | 260 | 1.109 | 28.244 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression_macro_non_southerly | top 25pct rows by cloud_cover_suppression inside macro_non_southerly | onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 645 | 177 | 1.193 | 26.357 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression_macro_non_southerly | top 25pct rows by cloud_cover_suppression inside macro_non_southerly | onda3_e_continuous_2012_start | Onda 3E continuous 2012-start | 645 | 177 | 1.195 | 25.426 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression_macro_non_southerly | top 25pct rows by cloud_cover_suppression inside macro_non_southerly | onda3_e_legacy_2009_start | Onda 3E legacy 2009-start | 645 | 177 | 1.193 | 26.357 | EXPERIMENT_ONLY |
| top_quartile_cloud_cover_suppression_macro_non_southerly | top 25pct rows by cloud_cover_suppression inside macro_non_southerly | onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 645 | 177 | 1.130 | 27.597 | EXPERIMENT_ONLY |

## Interpretation

- Onda 3G is an audit comparison only; it trains no model.
- Exact brackets use the same half-up integer rule as prior Onda 3 reviews.
- Nested validation remains the next design gate before any Open-Meteo/NWP work.
