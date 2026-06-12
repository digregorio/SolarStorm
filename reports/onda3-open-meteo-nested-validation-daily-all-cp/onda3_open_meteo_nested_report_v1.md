# Onda 3 Open-Meteo Nested Validation Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Open-Meteo augmented Onda 3F is compared against local-only Onda 3F on identical covered rows using nested validation folds: train through Y-2, validation on Y-1, test on Y.

## Decision

| decision_status | decision_rationale | n_outer_folds | selected_mean_test_mae | always_local_mean_test_mae | always_open_meteo_mean_test_mae | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION | Nested validation selected the Open-Meteo augmented candidate in every valid outer fold. | 1 | 0.8508168910799024 | 1.0915916419200538 | 0.8852083119788041 | EXPERIMENT_ONLY |

## Fold Scope

| stage | outer_test_year | evaluation_year | train_start | train_end | train_start_year | train_end_year | evaluation_start | evaluation_end | n_train_rows | n_evaluation_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 2024 | 2023 | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1460 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | 2012-01-01 | 2023-12-31 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1460 | 1464 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | 2012-01-01 | 2023-12-31 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1460 | 1464 | EXPERIMENT_ONLY |
| test | 2025 | 2025 | 2012-01-01 | 2024-12-31 | 2012 | 2024 | 2025-01-01 | 2025-12-31 | 2924 | 1460 | EXPERIMENT_ONLY |

## Validation Selection

| outer_test_year | validation_year | selected_candidate_id | selected_candidate_label | selected_validation_mae | selected_validation_any_cp_exact_pct | selected_validation_cp23_exact_pct | selected_test_mae | selected_test_any_cp_exact_pct | selected_test_cp23_exact_pct | validation_candidate_count | test_candidate_count | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 0.9195997328777058 | 50.27322404371585 | 41.80327868852459 | 0.8508168910799024 | 51.78082191780822 | 36.16438356164384 | 2 | 2 | validation_mae_then_cp23_exact_then_local | EXPERIMENT_ONLY |

## Selected Test Summary

| outer_test_year | evaluation_year | candidate_id | candidate_label | mae | any_cp_exact_pct | cp23_exact_pct | n_days_with_cp23 | cp23_exact_days | n_days | n_cp_rows | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 0.8508168910799024 | 51.78082191780822 | 36.16438356164384 | 365 | 132 | 365 | 1460 | validation_mae_then_cp23_exact_then_local | EXPERIMENT_ONLY |

## Candidate Metric Summary

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | n_days | n_cp_rows | mae | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | 2024 | local_only_onda3f | Local-only Onda 3F | 366 | 1464 | 1.1022931939517722 | 42.349726775956285 | 366 | 100 | 27.322404371584703 | EXPERIMENT_ONLY | 29.23497267759563 | 30.327868852459016 | 26.775956284153008 | 27.322404371584703 |
| test | 2024 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 366 | 1464 | 0.9195997328777058 | 50.27322404371585 | 366 | 153 | 41.80327868852459 | EXPERIMENT_ONLY | 39.61748633879781 | 41.2568306010929 | 41.80327868852459 | 41.80327868852459 |
| test | 2025 | 2025 | local_only_onda3f | Local-only Onda 3F | 365 | 1460 | 1.0808900898883356 | 46.02739726027397 | 365 | 115 | 31.506849315068493 | EXPERIMENT_ONLY | 26.84931506849315 | 31.780821917808222 | 31.506849315068493 | 31.506849315068493 |
| test | 2025 | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 365 | 1460 | 0.8508168910799024 | 51.78082191780822 | 365 | 132 | 36.16438356164384 | EXPERIMENT_ONLY | 35.342465753424655 | 37.80821917808219 | 36.16438356164384 | 36.16438356164384 |
| validation | 2025 | 2024 | local_only_onda3f | Local-only Onda 3F | 366 | 1464 | 1.1022931939517722 | 42.349726775956285 | 366 | 100 | 27.322404371584703 | EXPERIMENT_ONLY | 29.23497267759563 | 30.327868852459016 | 26.775956284153008 | 27.322404371584703 |
| validation | 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 366 | 1464 | 0.9195997328777058 | 50.27322404371585 | 366 | 153 | 41.80327868852459 | EXPERIMENT_ONLY | 39.61748633879781 | 41.2568306010929 | 41.80327868852459 | 41.80327868852459 |

## Regime Performance

| stage | outer_test_year | candidate_id | candidate_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1132 | 292 | 1.092564672156246 | 28.71024734982332 | EXPERIMENT_ONLY |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 332 | 94 | 1.1354639369413364 | 27.40963855421687 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1132 | 292 | 0.9501365983776733 | 37.36749116607774 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 332 | 94 | 0.8154800589440817 | 53.915662650602414 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1020 | 265 | 1.0940183294622725 | 31.274509803921568 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 440 | 121 | 1.0504564436032995 | 28.40909090909091 | EXPERIMENT_ONLY |
| test | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1020 | 265 | 0.8453800938336542 | 36.56862745098039 | EXPERIMENT_ONLY |
| test | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 440 | 121 | 0.8634203756052957 | 35.90909090909091 | EXPERIMENT_ONLY |
| validation | 2025 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1132 | 292 | 1.092564672156246 | 28.71024734982332 | EXPERIMENT_ONLY |
| validation | 2025 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 332 | 94 | 1.1354639369413364 | 27.40963855421687 | EXPERIMENT_ONLY |
| validation | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1132 | 292 | 0.9501365983776733 | 37.36749116607774 | EXPERIMENT_ONLY |
| validation | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 332 | 94 | 0.8154800589440817 | 53.915662650602414 | EXPERIMENT_ONLY |
