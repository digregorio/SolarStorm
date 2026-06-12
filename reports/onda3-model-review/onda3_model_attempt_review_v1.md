# Onda 3 Model Attempt Review
Generated: 2026-06-09

Scope: pre-Open-Meteo review. Open-Meteo forecast data is not integrated in these artifacts.
All outputs remain EXPERIMENT_ONLY.
Current best MAE surface: Onda 3D binary-macro interactions with weighted challenger MAE 1.173.
Current daily exact-bracket surface: any CP exact 45.164% and 23:00 exact 29.927%.
Validation status: no distinct validation split is persisted; current artifacts use fixed holdout or rolling-year test folds.

## Train Validation Test Scope

| iteration_id | iteration_label | split_type | train_period | validation_period | test_period | row_unit | n_train_reported | n_test_reported | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_a_baseline_first | Onda 3A baseline-first aggregate ridge | fixed_holdout | 2009-04-23 to 2024-12-31 | none; no separate validation split persisted | 2025-01-01 to 2026-06-03 | all_cp_rows | 19748 | 2076 | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | fixed_holdout | 2009-04-23 to 2024-12-31 | none; no separate validation split persisted | 2025-01-01 to 2026-06-03 | per_cp_model_rows | 4937 | 519 | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | rolling_year_2023 | 2009-04-23 to 2022-12-31 | none; no separate validation split persisted | 2023-01-01 to 2023-12-31 | per_cp_model_rows | 4206 | 365 | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | rolling_year_2024 | 2009-04-23 to 2023-12-31 | none; no separate validation split persisted | 2024-01-01 to 2024-12-31 | per_cp_model_rows | 4571 | 366 | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | rolling_year_2025 | 2009-04-23 to 2024-12-31 | none; no separate validation split persisted | 2025-01-01 to 2025-12-31 | per_cp_model_rows | 4937 | 365 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | rolling_year_2023 | 2009-04-23 to 2022-12-31 | none; no separate validation split persisted | 2023-01-01 to 2023-12-31 | per_cp_model_rows | 4206 | 365 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | rolling_year_2024 | 2009-04-23 to 2023-12-31 | none; no separate validation split persisted | 2024-01-01 to 2024-12-31 | per_cp_model_rows | 4571 | 366 | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | rolling_year_2025 | 2009-04-23 to 2024-12-31 | none; no separate validation split persisted | 2025-01-01 to 2025-12-31 | per_cp_model_rows | 4937 | 365 | EXPERIMENT_ONLY |

## Model Iteration Summary

| iteration_id | iteration_label | n_result_rows | n_challenger_rows | weighted_null_mae | weighted_challenger_mae | weighted_mae_lift | all_challenger_rows_beat_null | has_line_level_predictions | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_a_baseline_first | Onda 3A baseline-first aggregate ridge | 2 | 1 | 2.812 | 1.349 | 1.463 | true | false | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 8 | 4 | 2.812 | 1.271 | 1.541 | true | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 24 | 12 | 2.952 | 1.203 | 1.750 | true | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 24 | 12 | 2.952 | 1.173 | 1.780 | true | true | EXPERIMENT_ONLY |

## Individual Challenger Result Rows

| iteration_id | iteration_label | test_year | cp | model_name | n_train | n_test | mae | beats_train_mean_null | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_a_baseline_first | Onda 3A baseline-first aggregate ridge |  | ALL | ridge_challenger | 19748 | 2076 | 1.349 | true | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ |  | 20:00 | ridge_challenger | 4937 | 519 | 1.376 | true | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ |  | 21:00 | ridge_challenger | 4937 | 519 | 1.312 | true | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ |  | 22:00 | ridge_challenger | 4937 | 519 | 1.198 | true | EXPERIMENT_ONLY |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ |  | 23:00 | ridge_challenger | 4937 | 519 | 1.197 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023 | 20:00 | ridge_challenger | 4206 | 365 | 1.328 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023 | 21:00 | ridge_challenger | 4206 | 365 | 1.212 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023 | 22:00 | ridge_challenger | 4206 | 365 | 1.125 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023 | 23:00 | ridge_challenger | 4206 | 365 | 1.121 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024 | 20:00 | ridge_challenger | 4571 | 366 | 1.337 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024 | 21:00 | ridge_challenger | 4571 | 366 | 1.206 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024 | 22:00 | ridge_challenger | 4571 | 366 | 1.136 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024 | 23:00 | ridge_challenger | 4571 | 366 | 1.139 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025 | 20:00 | ridge_challenger | 4937 | 365 | 1.308 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025 | 21:00 | ridge_challenger | 4937 | 365 | 1.258 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025 | 22:00 | ridge_challenger | 4937 | 365 | 1.129 | true | EXPERIMENT_ONLY |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025 | 23:00 | ridge_challenger | 4937 | 365 | 1.132 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023 | 20:00 | ridge_challenger | 4206 | 365 | 1.241 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023 | 21:00 | ridge_challenger | 4206 | 365 | 1.160 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023 | 22:00 | ridge_challenger | 4206 | 365 | 1.076 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023 | 23:00 | ridge_challenger | 4206 | 365 | 1.084 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024 | 20:00 | ridge_challenger | 4571 | 366 | 1.298 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024 | 21:00 | ridge_challenger | 4571 | 366 | 1.194 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024 | 22:00 | ridge_challenger | 4571 | 366 | 1.127 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024 | 23:00 | ridge_challenger | 4571 | 366 | 1.123 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025 | 20:00 | ridge_challenger | 4937 | 365 | 1.290 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025 | 21:00 | ridge_challenger | 4937 | 365 | 1.238 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025 | 22:00 | ridge_challenger | 4937 | 365 | 1.123 | true | EXPERIMENT_ONLY |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025 | 23:00 | ridge_challenger | 4937 | 365 | 1.118 | true | EXPERIMENT_ONLY |

## Exact Bracket Overall

| iteration_id | iteration_label | n_days | n_cp_rows | mae | any_cp_exact_pct | cp23_exact_pct | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 519 | 2076 | 1.271 | 43.931 | 29.287 | 25.626 | 26.782 | 31.792 | 29.287 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 1096 | 4384 | 1.203 | 44.891 | 29.653 | 24.726 | 27.828 | 30.748 | 29.653 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 1096 | 4384 | 1.173 | 45.164 | 29.927 | 26.095 | 27.099 | 30.566 | 29.927 |

## Exact Bracket By Month Day

any_cp_exact_pct counts a day as correct if any checkpoint hit the exact integer bracket. cp23_exact_pct is the last-checkpoint-only rate.

| iteration_id | iteration_label | month | n_days | any_cp_exact_days | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-01 | 31 | 15 | 48.387 | 31 | 11 | 35.484 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-02 | 28 | 12 | 42.857 | 28 | 9 | 32.143 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-03 | 31 | 14 | 45.161 | 31 | 12 | 38.710 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-04 | 30 | 16 | 53.333 | 30 | 12 | 40.000 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-05 | 31 | 16 | 51.613 | 31 | 9 | 29.032 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-06 | 30 | 12 | 40.000 | 30 | 6 | 20.000 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-07 | 31 | 13 | 41.935 | 31 | 9 | 29.032 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-08 | 31 | 18 | 58.065 | 31 | 13 | 41.935 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-09 | 30 | 13 | 43.333 | 30 | 8 | 26.667 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-10 | 31 | 14 | 45.161 | 31 | 7 | 22.581 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-11 | 30 | 13 | 43.333 | 30 | 8 | 26.667 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-12 | 31 | 13 | 41.935 | 31 | 9 | 29.032 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-01 | 31 | 10 | 32.258 | 31 | 9 | 29.032 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-02 | 28 | 11 | 39.286 | 28 | 7 | 25.000 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-03 | 31 | 7 | 22.581 | 31 | 5 | 16.129 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-04 | 30 | 14 | 46.667 | 30 | 9 | 30.000 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-05 | 31 | 15 | 48.387 | 31 | 8 | 25.806 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-06 | 3 | 2 | 66.667 | 3 | 1 | 33.333 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-01 | 31 | 14 | 45.161 | 31 | 12 | 38.710 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-02 | 28 | 11 | 39.286 | 28 | 11 | 39.286 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-03 | 31 | 9 | 29.032 | 31 | 7 | 22.581 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-04 | 30 | 15 | 50.000 | 30 | 10 | 33.333 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-05 | 31 | 17 | 54.839 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-06 | 30 | 16 | 53.333 | 30 | 10 | 33.333 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-07 | 31 | 11 | 35.484 | 31 | 7 | 22.581 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-08 | 31 | 14 | 45.161 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-09 | 30 | 19 | 63.333 | 30 | 11 | 36.667 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-10 | 31 | 9 | 29.032 | 31 | 7 | 22.581 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-11 | 30 | 15 | 50.000 | 30 | 9 | 30.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-12 | 31 | 12 | 38.710 | 31 | 8 | 25.806 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-01 | 31 | 11 | 35.484 | 31 | 7 | 22.581 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-02 | 29 | 8 | 27.586 | 29 | 5 | 17.241 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-03 | 31 | 7 | 22.581 | 31 | 6 | 19.355 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-04 | 30 | 16 | 53.333 | 30 | 9 | 30.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-05 | 31 | 16 | 51.613 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-06 | 30 | 18 | 60.000 | 30 | 12 | 40.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-07 | 31 | 18 | 58.065 | 31 | 12 | 38.710 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-08 | 31 | 12 | 38.710 | 31 | 5 | 16.129 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-09 | 30 | 13 | 43.333 | 30 | 6 | 20.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-10 | 31 | 14 | 45.161 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-11 | 30 | 16 | 53.333 | 30 | 12 | 40.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2024-12 | 31 | 12 | 38.710 | 31 | 10 | 32.258 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-01 | 31 | 15 | 48.387 | 31 | 11 | 35.484 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-02 | 28 | 12 | 42.857 | 28 | 9 | 32.143 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-03 | 31 | 14 | 45.161 | 31 | 12 | 38.710 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-04 | 30 | 16 | 53.333 | 30 | 12 | 40.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-05 | 31 | 16 | 51.613 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-06 | 30 | 12 | 40.000 | 30 | 6 | 20.000 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-07 | 31 | 13 | 41.935 | 31 | 9 | 29.032 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-08 | 31 | 18 | 58.065 | 31 | 13 | 41.935 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-09 | 30 | 13 | 43.333 | 30 | 8 | 26.667 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-10 | 31 | 14 | 45.161 | 31 | 7 | 22.581 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-11 | 30 | 13 | 43.333 | 30 | 8 | 26.667 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2025-12 | 31 | 13 | 41.935 | 31 | 9 | 29.032 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-02 | 28 | 10 | 35.714 | 28 | 9 | 32.143 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-03 | 31 | 12 | 38.710 | 31 | 9 | 29.032 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-04 | 30 | 15 | 50.000 | 30 | 9 | 30.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-05 | 31 | 18 | 58.065 | 31 | 10 | 32.258 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-07 | 31 | 12 | 38.710 | 31 | 7 | 22.581 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-08 | 31 | 15 | 48.387 | 31 | 10 | 32.258 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-09 | 30 | 19 | 63.333 | 30 | 12 | 40.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-10 | 31 | 12 | 38.710 | 31 | 5 | 16.129 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-11 | 30 | 13 | 43.333 | 30 | 9 | 30.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2023-12 | 31 | 12 | 38.710 | 31 | 8 | 25.806 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-01 | 31 | 8 | 25.806 | 31 | 5 | 16.129 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-02 | 29 | 9 | 31.034 | 29 | 7 | 24.138 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-03 | 31 | 9 | 29.032 | 31 | 8 | 25.806 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-04 | 30 | 16 | 53.333 | 30 | 6 | 20.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-05 | 31 | 14 | 45.161 | 31 | 10 | 32.258 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-06 | 30 | 16 | 53.333 | 30 | 13 | 43.333 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-07 | 31 | 15 | 48.387 | 31 | 10 | 32.258 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-08 | 31 | 15 | 48.387 | 31 | 7 | 22.581 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-09 | 30 | 12 | 40.000 | 30 | 5 | 16.667 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-10 | 31 | 13 | 41.935 | 31 | 9 | 29.032 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-11 | 30 | 15 | 50.000 | 30 | 10 | 33.333 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2024-12 | 31 | 12 | 38.710 | 31 | 9 | 29.032 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-01 | 31 | 15 | 48.387 | 31 | 11 | 35.484 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-02 | 28 | 10 | 35.714 | 28 | 6 | 21.429 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-03 | 31 | 12 | 38.710 | 31 | 12 | 38.710 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-04 | 30 | 14 | 46.667 | 30 | 10 | 33.333 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-05 | 31 | 19 | 61.290 | 31 | 10 | 32.258 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-06 | 30 | 14 | 46.667 | 30 | 10 | 33.333 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-07 | 31 | 12 | 38.710 | 31 | 8 | 25.806 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-08 | 31 | 16 | 51.613 | 31 | 11 | 35.484 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-09 | 30 | 14 | 46.667 | 30 | 9 | 30.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-10 | 31 | 18 | 58.065 | 31 | 14 | 45.161 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-11 | 30 | 17 | 56.667 | 30 | 12 | 40.000 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | 2025-12 | 31 | 11 | 35.484 | 31 | 6 | 19.355 |

## Exact Bracket By Month And CP

| iteration_id | iteration_label | month | cp | n_cp_rows | exact_bracket_rows | exact_bracket_pct | mae |
| --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-01 | 20:00 | 31 | 8 | 25.806 | 1.688 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-01 | 21:00 | 31 | 11 | 35.484 | 1.527 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-01 | 22:00 | 31 | 12 | 38.710 | 1.464 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-01 | 23:00 | 31 | 11 | 35.484 | 1.471 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-02 | 20:00 | 28 | 6 | 21.429 | 1.605 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-02 | 21:00 | 28 | 6 | 21.429 | 1.279 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-02 | 22:00 | 28 | 9 | 32.143 | 1.224 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-02 | 23:00 | 28 | 9 | 32.143 | 1.227 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-03 | 20:00 | 31 | 5 | 16.129 | 1.537 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-03 | 21:00 | 31 | 8 | 25.806 | 1.363 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-03 | 22:00 | 31 | 12 | 38.710 | 1.238 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-03 | 23:00 | 31 | 12 | 38.710 | 1.206 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-04 | 20:00 | 30 | 7 | 23.333 | 1.154 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-04 | 21:00 | 30 | 6 | 20.000 | 1.174 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-04 | 22:00 | 30 | 13 | 43.333 | 0.992 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-04 | 23:00 | 30 | 12 | 40.000 | 1.025 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-05 | 20:00 | 31 | 9 | 29.032 | 0.925 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-05 | 21:00 | 31 | 9 | 29.032 | 1.001 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-05 | 22:00 | 31 | 11 | 35.484 | 0.911 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-05 | 23:00 | 31 | 9 | 29.032 | 0.934 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-06 | 20:00 | 30 | 9 | 30.000 | 1.457 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-06 | 21:00 | 30 | 6 | 20.000 | 1.517 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-06 | 22:00 | 30 | 6 | 20.000 | 1.495 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-06 | 23:00 | 30 | 6 | 20.000 | 1.473 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-07 | 20:00 | 31 | 7 | 22.581 | 1.178 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-07 | 21:00 | 31 | 9 | 29.032 | 1.253 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-07 | 22:00 | 31 | 9 | 29.032 | 1.028 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-07 | 23:00 | 31 | 9 | 29.032 | 0.996 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-08 | 20:00 | 31 | 12 | 38.710 | 1.126 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-08 | 21:00 | 31 | 10 | 32.258 | 1.151 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-08 | 22:00 | 31 | 14 | 45.161 | 1.002 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-08 | 23:00 | 31 | 13 | 41.935 | 0.996 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-09 | 20:00 | 30 | 8 | 26.667 | 1.538 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-09 | 21:00 | 30 | 9 | 30.000 | 1.605 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-09 | 22:00 | 30 | 9 | 30.000 | 1.169 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-09 | 23:00 | 30 | 8 | 26.667 | 1.162 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-10 | 20:00 | 31 | 9 | 29.032 | 1.013 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-10 | 21:00 | 31 | 8 | 25.806 | 1.015 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-10 | 22:00 | 31 | 11 | 35.484 | 0.892 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-10 | 23:00 | 31 | 7 | 22.581 | 0.937 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-11 | 20:00 | 30 | 9 | 30.000 | 1.109 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-11 | 21:00 | 30 | 11 | 36.667 | 0.998 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-11 | 22:00 | 30 | 9 | 30.000 | 1.113 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-11 | 23:00 | 30 | 8 | 26.667 | 1.127 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-12 | 20:00 | 31 | 7 | 22.581 | 1.398 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-12 | 21:00 | 31 | 8 | 25.806 | 1.225 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-12 | 22:00 | 31 | 11 | 35.484 | 1.036 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2025-12 | 23:00 | 31 | 9 | 29.032 | 1.042 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-01 | 20:00 | 31 | 4 | 12.903 | 1.892 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-01 | 21:00 | 31 | 6 | 19.355 | 1.535 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-01 | 22:00 | 31 | 9 | 29.032 | 1.424 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-01 | 23:00 | 31 | 9 | 29.032 | 1.403 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-02 | 20:00 | 28 | 7 | 25.000 | 1.811 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-02 | 21:00 | 28 | 6 | 21.429 | 1.655 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-02 | 22:00 | 28 | 7 | 25.000 | 1.546 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-02 | 23:00 | 28 | 7 | 25.000 | 1.577 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-03 | 20:00 | 31 | 6 | 19.355 | 1.669 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-03 | 21:00 | 31 | 4 | 12.903 | 1.585 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-03 | 22:00 | 31 | 5 | 16.129 | 1.585 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-03 | 23:00 | 31 | 5 | 16.129 | 1.585 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-04 | 20:00 | 30 | 10 | 33.333 | 1.185 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-04 | 21:00 | 30 | 11 | 36.667 | 1.288 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-04 | 22:00 | 30 | 9 | 30.000 | 1.218 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-04 | 23:00 | 30 | 9 | 30.000 | 1.155 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-05 | 20:00 | 31 | 9 | 29.032 | 1.151 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-05 | 21:00 | 31 | 10 | 32.258 | 1.147 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-05 | 22:00 | 31 | 9 | 29.032 | 1.061 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-05 | 23:00 | 31 | 8 | 25.806 | 1.068 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-06 | 20:00 | 3 | 1 | 33.333 | 1.441 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-06 | 21:00 | 3 | 1 | 33.333 | 1.484 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-06 | 22:00 | 3 | 0 | 0.000 | 1.264 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | 2026-06 | 23:00 | 3 | 1 | 33.333 | 1.268 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-01 | 20:00 | 31 | 3 | 9.677 | 1.587 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-01 | 21:00 | 31 | 10 | 32.258 | 1.403 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-01 | 22:00 | 31 | 11 | 35.484 | 1.254 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-01 | 23:00 | 31 | 12 | 38.710 | 1.187 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-02 | 20:00 | 28 | 4 | 14.286 | 1.399 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-02 | 21:00 | 28 | 6 | 21.429 | 1.200 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-02 | 22:00 | 28 | 10 | 35.714 | 1.006 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | 2023-02 | 23:00 | 28 | 11 | 39.286 | 1.003 |

_Showing 80 of 360 rows. Full table is in CSV._

## Regime Performance

| iteration_id | iteration_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_rows | exact_bracket_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_non_southerly | 1458 | 377 | 1.250 | 409 | 28.052 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_southerly_flow | 618 | 168 | 1.320 | 180 | 29.126 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_non_southerly | 3225 | 833 | 1.195 | 882 | 27.349 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_southerly_flow | 1159 | 319 | 1.223 | 356 | 30.716 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 3225 | 833 | 1.172 | 901 | 27.938 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 1159 | 319 | 1.173 | 345 | 29.767 |

## Regime CP Performance

| iteration_id | iteration_label | binary_macro_regime_label | cp | n_cp_rows | mae | exact_bracket_rows | exact_bracket_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_non_southerly | 20:00 | 363 | 1.375 | 88 | 24.242 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_non_southerly | 21:00 | 364 | 1.283 | 99 | 27.198 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_non_southerly | 22:00 | 365 | 1.160 | 117 | 32.055 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_non_southerly | 23:00 | 366 | 1.184 | 105 | 28.689 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_southerly_flow | 20:00 | 156 | 1.379 | 45 | 28.846 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_southerly_flow | 21:00 | 155 | 1.381 | 40 | 25.806 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_southerly_flow | 22:00 | 154 | 1.289 | 48 | 31.169 |
| onda3_b_cp_specific_holdout | Onda 3B CP-specific holdout 2025+ | macro_southerly_flow | 23:00 | 153 | 1.228 | 47 | 30.719 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_non_southerly | 20:00 | 804 | 1.336 | 185 | 23.010 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_non_southerly | 21:00 | 806 | 1.209 | 221 | 27.419 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_non_southerly | 22:00 | 806 | 1.111 | 243 | 30.149 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_non_southerly | 23:00 | 809 | 1.126 | 233 | 28.801 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_southerly_flow | 20:00 | 292 | 1.293 | 86 | 29.452 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_southerly_flow | 21:00 | 290 | 1.271 | 84 | 28.966 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_southerly_flow | 22:00 | 290 | 1.184 | 94 | 32.414 |
| onda3_c_rolling_temporal | Onda 3C rolling temporal no-interaction | macro_southerly_flow | 23:00 | 287 | 1.144 | 92 | 32.056 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 20:00 | 804 | 1.297 | 207 | 25.746 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 21:00 | 806 | 1.186 | 215 | 26.675 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 22:00 | 806 | 1.094 | 245 | 30.397 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_non_southerly | 23:00 | 809 | 1.113 | 234 | 28.925 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 20:00 | 292 | 1.221 | 79 | 27.055 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 21:00 | 290 | 1.229 | 82 | 28.276 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 22:00 | 290 | 1.149 | 90 | 31.034 |
| onda3_d_binary_macro_interactions | Onda 3D binary-macro interactions | macro_southerly_flow | 23:00 | 287 | 1.094 | 94 | 32.753 |

## Onda 3D vs Onda 3C Regime Delta

| comparison | binary_macro_regime_label | onda3_c_mae | onda3_d_mae | mae_delta | onda3_c_exact_bracket_pct | onda3_d_exact_bracket_pct | exact_bracket_pct_delta | n_cp_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_d_minus_onda3_c | macro_non_southerly | 1.195 | 1.172 | -0.023 | 27.349 | 27.938 | 0.589 | 3225 | EXPERIMENT_ONLY |
| onda3_d_minus_onda3_c | macro_southerly_flow | 1.223 | 1.173 | -0.050 | 30.716 | 29.767 | -0.949 | 1159 | EXPERIMENT_ONLY |

## Binary Macro Interaction Structure

Onda 3D keeps the binary macro regime as the structural switch and adds continuous-x-macro interactions for foehn_score and cloud_cover_suppression.

| feature | source_feature | macro_value | interaction_type | production_status |
| --- | --- | --- | --- | --- |
| foehn_score_x_macro_non_southerly | foehn_score | macro_non_southerly | continuous_x_binary_macro | EXPERIMENT_ONLY |
| foehn_score_x_macro_southerly_flow | foehn_score | macro_southerly_flow | continuous_x_binary_macro | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_non_southerly | cloud_cover_suppression | macro_non_southerly | continuous_x_binary_macro | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_southerly_flow | cloud_cover_suppression | macro_southerly_flow | continuous_x_binary_macro | EXPERIMENT_ONLY |

## Onda 4M Gate Review

| review_id | review_label | source_iteration_id | n_gates | n_pass | blocked_gates | m3_detail | m4_detail | decision_status | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda4_review_onda3_a | Onda 4M review on Onda 3A | onda3_a_baseline_first | 8 | 8 |  | null_mae=2.8120; challenger_mae=1.3487; lift=1.4632 | first_review_single_test_year_recorded | READY_FOR_ONDA3_NEXT_MODEL_ITERATION | EXPERIMENT_ONLY |
| onda4_review_onda3_b | Onda 4M review on Onda 3B | onda3_b_cp_specific_holdout | 8 | 8 |  | null_mae=2.8120; challenger_mae=1.2708; lift=1.5411; challenger_failures=0 | first_review_single_test_year_recorded | READY_FOR_ONDA3_NEXT_MODEL_ITERATION | EXPERIMENT_ONLY |
| onda4_review_onda3_c | Onda 4M review on Onda 3C | onda3_c_rolling_temporal | 8 | 8 |  | null_mae=2.9522; challenger_mae=1.2026; lift=1.7496; challenger_failures=0 | rolling_temporal_diagnostics; test_years=2023,2024,2025 | READY_FOR_ONDA3_NEXT_MODEL_ITERATION | EXPERIMENT_ONLY |
| onda4_review_onda3_d | Onda 4M review on Onda 3D | onda3_d_binary_macro_interactions | 8 | 8 |  | null_mae=2.9522; challenger_mae=1.1726; lift=1.7796; challenger_failures=0 | rolling_temporal_diagnostics; test_years=2023,2024,2025 | READY_FOR_ONDA3_NEXT_MODEL_ITERATION | EXPERIMENT_ONLY |

## Interpretation

- The current baseline exists: Onda 3A train_mean_null vs ridge_challenger on the fixed 2025+ holdout.
- Onda 3A did not persist line-level predictions, so exact bracket rates cannot be reconstructed from its artifacts alone.
- Onda 3D improved MAE versus Onda 3C in both binary macro regimes; exact bracket improvement is smaller than MAE improvement.
- Southerly-flow rows often show slightly higher exact bracket rates, but the evidence is not strong enough to claim a dedicated regime-specialist model.
- The current path supports two macro regimes as a structural switch plus continuous foehn/cloud features inside the model, not as a complete meteorological taxonomy.
