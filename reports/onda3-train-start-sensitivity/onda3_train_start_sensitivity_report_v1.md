# Onda 3E Train-Start Sensitivity Report

Generated: 2026-06-09



Scope: pre-Open-Meteo local-data experiment. Open-Meteo forecast data is not integrated.

All outputs remain EXPERIMENT_ONLY.

## Decision

| decision_status | decision_rationale | continuous_minus_legacy_weighted_mae | continuous_minus_legacy_any_cp_exact_pct | production_status |
| --- | --- | --- | --- | --- |
| KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION | The train-start variants are too close or trade MAE against exact-bracket performance. | -0.002 | -0.091 | EXPERIMENT_ONLY |

## Variant Comparison

| variant_id | train_start | weighted_challenger_mae | any_cp_exact_pct | cp23_exact_pct | production_status | continuous_minus_legacy_weighted_mae | continuous_minus_legacy_any_cp_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_2009_start | 2009-04-23 | 1.173 | 45.164 | 29.927 | EXPERIMENT_ONLY | -0.002 | -0.091 |
| continuous_2012_start | 2012-01-01 | 1.170 | 45.073 | 29.836 | EXPERIMENT_ONLY | -0.002 | -0.091 |

## Train/Test Scope

| variant_id | train_start | test_year | train_period | test_period | n_train_rows | n_test_rows | n_train_days | n_test_days | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_2009_start | 2009-04-23 | 2023 | 2009-04-23 to 2022-12-31 | 2023-01-01 to 2023-12-31 | 16824 | 1460 | 4206 | 365 | EXPERIMENT_ONLY |
| legacy_2009_start | 2009-04-23 | 2024 | 2009-04-23 to 2023-12-31 | 2024-01-01 to 2024-12-31 | 18284 | 1464 | 4571 | 366 | EXPERIMENT_ONLY |
| legacy_2009_start | 2009-04-23 | 2025 | 2009-04-23 to 2024-12-31 | 2025-01-01 to 2025-12-31 | 19748 | 1460 | 4937 | 365 | EXPERIMENT_ONLY |
| continuous_2012_start | 2012-01-01 | 2023 | 2012-01-01 to 2022-12-31 | 2023-01-01 to 2023-12-31 | 16044 | 1460 | 4011 | 365 | EXPERIMENT_ONLY |
| continuous_2012_start | 2012-01-01 | 2024 | 2012-01-01 to 2023-12-31 | 2024-01-01 to 2024-12-31 | 17504 | 1464 | 4376 | 366 | EXPERIMENT_ONLY |
| continuous_2012_start | 2012-01-01 | 2025 | 2012-01-01 to 2024-12-31 | 2025-01-01 to 2025-12-31 | 18968 | 1460 | 4742 | 365 | EXPERIMENT_ONLY |

## Exact Bracket Overall

| iteration_id | iteration_label | n_days | n_cp_rows | mae | any_cp_exact_pct | cp23_exact_pct | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct | variant_id | train_start | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 1096 | 4384 | 1.170 | 45.073 | 29.836 | 25.912 | 27.646 | 30.474 | 29.836 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 1096 | 4384 | 1.173 | 45.164 | 29.927 | 26.095 | 27.099 | 30.566 | 29.927 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |

## Exact Bracket By Month

any_cp_exact_pct counts a day as correct if any checkpoint hit the exact integer bracket. cp23_exact_pct is the last-checkpoint-only rate.

| iteration_id | iteration_label | month | n_days | any_cp_exact_days | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | variant_id | train_start | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-02 | 28 | 11 | 39.286 | 28 | 9 | 32.143 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-03 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-04 | 30 | 15 | 50.000 | 30 | 11 | 36.667 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-05 | 31 | 18 | 58.065 | 31 | 11 | 35.484 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-07 | 31 | 12 | 38.710 | 31 | 6 | 19.355 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-08 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-09 | 30 | 18 | 60.000 | 30 | 10 | 33.333 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-10 | 31 | 11 | 35.484 | 31 | 4 | 12.903 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-11 | 30 | 13 | 43.333 | 30 | 9 | 30.000 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-12 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-01 | 31 | 9 | 29.032 | 31 | 6 | 19.355 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-02 | 29 | 9 | 31.034 | 29 | 6 | 20.690 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-03 | 31 | 9 | 29.032 | 31 | 8 | 25.806 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-04 | 30 | 16 | 53.333 | 30 | 7 | 23.333 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-05 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-06 | 30 | 16 | 53.333 | 30 | 12 | 40.000 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-07 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-08 | 31 | 15 | 48.387 | 31 | 7 | 22.581 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-09 | 30 | 13 | 43.333 | 30 | 4 | 13.333 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-10 | 31 | 14 | 45.161 | 31 | 9 | 29.032 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-11 | 30 | 15 | 50.000 | 30 | 11 | 36.667 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-12 | 31 | 11 | 35.484 | 31 | 9 | 29.032 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-01 | 31 | 15 | 48.387 | 31 | 12 | 38.710 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-02 | 28 | 10 | 35.714 | 28 | 6 | 21.429 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-03 | 31 | 12 | 38.710 | 31 | 11 | 35.484 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-04 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-05 | 31 | 18 | 58.065 | 31 | 9 | 29.032 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-06 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-07 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-08 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-09 | 30 | 14 | 46.667 | 30 | 9 | 30.000 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-10 | 31 | 18 | 58.065 | 31 | 14 | 45.161 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-11 | 30 | 17 | 56.667 | 30 | 11 | 36.667 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2025-12 | 31 | 10 | 32.258 | 31 | 7 | 22.581 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-02 | 28 | 10 | 35.714 | 28 | 9 | 32.143 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-03 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-04 | 30 | 15 | 50.000 | 30 | 9 | 30.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-05 | 31 | 18 | 58.065 | 31 | 10 | 32.258 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-06 | 30 | 18 | 60.000 | 30 | 11 | 36.667 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-07 | 31 | 12 | 38.710 | 31 | 7 | 22.581 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-08 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-09 | 30 | 19 | 63.333 | 30 | 12 | 40.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-10 | 31 | 12 | 38.710 | 31 | 5 | 16.129 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-11 | 30 | 13 | 43.333 | 30 | 9 | 30.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2023-12 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-01 | 31 | 8 | 25.806 | 31 | 5 | 16.129 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-02 | 29 | 9 | 31.034 | 29 | 7 | 24.138 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-03 | 31 | 9 | 29.032 | 31 | 8 | 25.806 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-04 | 30 | 16 | 53.333 | 30 | 6 | 20.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-05 | 31 | 14 | 45.161 | 31 | 10 | 32.258 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-06 | 30 | 16 | 53.333 | 30 | 13 | 43.333 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-07 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-08 | 31 | 15 | 48.387 | 31 | 7 | 22.581 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-09 | 30 | 12 | 40.000 | 30 | 5 | 16.667 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-10 | 31 | 13 | 41.935 | 31 | 9 | 29.032 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-11 | 30 | 15 | 50.000 | 30 | 10 | 33.333 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2024-12 | 31 | 12 | 38.710 | 31 | 9 | 29.032 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-01 | 31 | 15 | 48.387 | 31 | 11 | 35.484 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-02 | 28 | 10 | 35.714 | 28 | 6 | 21.429 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-03 | 31 | 12 | 38.710 | 31 | 12 | 38.710 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-04 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-05 | 31 | 19 | 61.290 | 31 | 10 | 32.258 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-06 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-07 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-08 | 31 | 16 | 51.613 | 31 | 11 | 35.484 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-09 | 30 | 14 | 46.667 | 30 | 9 | 30.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-10 | 31 | 18 | 58.065 | 31 | 14 | 45.161 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-11 | 30 | 17 | 56.667 | 30 | 12 | 40.000 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | 2025-12 | 31 | 11 | 35.484 | 31 | 6 | 19.355 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |

## Exact Bracket By Month And CP

| iteration_id | iteration_label | month | cp | n_cp_rows | exact_bracket_rows | exact_bracket_pct | mae | variant_id | train_start | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-01 | 20:00 | 31 | 4 | 12.903 | 1.608 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-01 | 21:00 | 31 | 8 | 25.806 | 1.470 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-01 | 22:00 | 31 | 10 | 32.258 | 1.337 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-01 | 23:00 | 31 | 11 | 35.484 | 1.280 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-02 | 20:00 | 28 | 6 | 21.429 | 1.280 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-02 | 21:00 | 28 | 6 | 21.429 | 1.113 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-02 | 22:00 | 28 | 8 | 28.571 | 0.934 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-02 | 23:00 | 28 | 9 | 32.143 | 0.951 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-03 | 20:00 | 31 | 8 | 25.806 | 1.217 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-03 | 21:00 | 31 | 8 | 25.806 | 1.158 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-03 | 22:00 | 31 | 9 | 29.032 | 1.181 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-03 | 23:00 | 31 | 8 | 25.806 | 1.218 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-04 | 20:00 | 30 | 8 | 26.667 | 1.051 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-04 | 21:00 | 30 | 4 | 13.333 | 1.092 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-04 | 22:00 | 30 | 11 | 36.667 | 0.866 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-04 | 23:00 | 30 | 11 | 36.667 | 0.876 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-05 | 20:00 | 31 | 9 | 29.032 | 1.090 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-05 | 21:00 | 31 | 11 | 35.484 | 1.058 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-05 | 22:00 | 31 | 10 | 32.258 | 1.064 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-05 | 23:00 | 31 | 11 | 35.484 | 1.068 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-06 | 20:00 | 30 | 15 | 50.000 | 0.904 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-06 | 21:00 | 30 | 12 | 40.000 | 0.925 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-06 | 22:00 | 30 | 12 | 40.000 | 0.928 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-06 | 23:00 | 30 | 11 | 36.667 | 1.004 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-07 | 20:00 | 31 | 6 | 19.355 | 1.405 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-07 | 21:00 | 31 | 4 | 12.903 | 1.499 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-07 | 22:00 | 31 | 6 | 19.355 | 1.191 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-07 | 23:00 | 31 | 6 | 19.355 | 1.151 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-08 | 20:00 | 31 | 11 | 35.484 | 1.205 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-08 | 21:00 | 31 | 8 | 25.806 | 1.209 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-08 | 22:00 | 31 | 10 | 32.258 | 1.048 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-08 | 23:00 | 31 | 10 | 32.258 | 1.006 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-09 | 20:00 | 30 | 10 | 33.333 | 0.915 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-09 | 21:00 | 30 | 12 | 40.000 | 0.851 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-09 | 22:00 | 30 | 11 | 36.667 | 0.901 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-09 | 23:00 | 30 | 10 | 33.333 | 0.920 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-10 | 20:00 | 31 | 4 | 12.903 | 1.552 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-10 | 21:00 | 31 | 6 | 19.355 | 1.217 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-10 | 22:00 | 31 | 4 | 12.903 | 1.219 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-10 | 23:00 | 31 | 4 | 12.903 | 1.239 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-11 | 20:00 | 30 | 7 | 23.333 | 1.201 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-11 | 21:00 | 30 | 7 | 23.333 | 0.972 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-11 | 22:00 | 30 | 9 | 30.000 | 0.893 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-11 | 23:00 | 30 | 9 | 30.000 | 0.924 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-12 | 20:00 | 31 | 6 | 19.355 | 1.404 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-12 | 21:00 | 31 | 9 | 29.032 | 1.258 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-12 | 22:00 | 31 | 9 | 29.032 | 1.283 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2023-12 | 23:00 | 31 | 9 | 29.032 | 1.311 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-01 | 20:00 | 31 | 5 | 16.129 | 2.064 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-01 | 21:00 | 31 | 6 | 19.355 | 1.698 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-01 | 22:00 | 31 | 5 | 16.129 | 1.704 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-01 | 23:00 | 31 | 6 | 19.355 | 1.721 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-02 | 20:00 | 29 | 7 | 24.138 | 1.512 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-02 | 21:00 | 29 | 4 | 13.793 | 1.464 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-02 | 22:00 | 29 | 5 | 17.241 | 1.398 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-02 | 23:00 | 29 | 6 | 20.690 | 1.372 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-03 | 20:00 | 31 | 6 | 19.355 | 1.396 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-03 | 21:00 | 31 | 6 | 19.355 | 1.383 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-03 | 22:00 | 31 | 8 | 25.806 | 1.234 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-03 | 23:00 | 31 | 8 | 25.806 | 1.204 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-04 | 20:00 | 30 | 10 | 33.333 | 0.995 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-04 | 21:00 | 30 | 12 | 40.000 | 1.016 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-04 | 22:00 | 30 | 8 | 26.667 | 1.084 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-04 | 23:00 | 30 | 7 | 23.333 | 1.145 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-05 | 20:00 | 31 | 8 | 25.806 | 1.147 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-05 | 21:00 | 31 | 6 | 19.355 | 1.064 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-05 | 22:00 | 31 | 10 | 32.258 | 0.889 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-05 | 23:00 | 31 | 10 | 32.258 | 0.889 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-06 | 20:00 | 30 | 8 | 26.667 | 1.244 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-06 | 21:00 | 30 | 8 | 26.667 | 1.231 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-06 | 22:00 | 30 | 12 | 40.000 | 0.915 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-06 | 23:00 | 30 | 12 | 40.000 | 0.907 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-07 | 20:00 | 31 | 9 | 29.032 | 1.104 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-07 | 21:00 | 31 | 12 | 38.710 | 1.071 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-07 | 22:00 | 31 | 11 | 35.484 | 0.911 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-07 | 23:00 | 31 | 11 | 35.484 | 0.879 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-08 | 20:00 | 31 | 10 | 32.258 | 1.076 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-08 | 21:00 | 31 | 9 | 29.032 | 1.075 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-08 | 22:00 | 31 | 7 | 22.581 | 1.187 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | 2024-08 | 23:00 | 31 | 7 | 22.581 | 1.187 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |

_Showing 80 of 288 rows. Full table is in CSV._

## Binary Macro Regime Performance

| iteration_id | iteration_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_rows | exact_bracket_pct | variant_id | train_start | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_non_southerly | 3225 | 833 | 1.170 | 897 | 27.814 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_southerly_flow | 1159 | 319 | 1.171 | 351 | 30.285 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_non_southerly | 3225 | 833 | 1.172 | 901 | 27.938 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_southerly_flow | 1159 | 319 | 1.173 | 345 | 29.767 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |

## Binary Macro Regime By CP

| iteration_id | iteration_label | binary_macro_regime_label | cp | n_cp_rows | mae | exact_bracket_rows | exact_bracket_pct | variant_id | train_start | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_non_southerly | 20:00 | 804 | 1.295 | 205 | 25.498 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_non_southerly | 21:00 | 806 | 1.181 | 220 | 27.295 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_non_southerly | 22:00 | 806 | 1.093 | 241 | 29.901 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_non_southerly | 23:00 | 809 | 1.113 | 231 | 28.554 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_southerly_flow | 20:00 | 292 | 1.222 | 79 | 27.055 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_southerly_flow | 21:00 | 290 | 1.225 | 83 | 28.621 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_southerly_flow | 22:00 | 290 | 1.145 | 93 | 32.069 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| continuous_2012_start | Onda 3E continuous 2012-start binary-macro interactions | macro_southerly_flow | 23:00 | 287 | 1.090 | 96 | 33.449 | continuous_2012_start | 2012-01-01 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_non_southerly | 20:00 | 804 | 1.297 | 207 | 25.746 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_non_southerly | 21:00 | 806 | 1.186 | 215 | 26.675 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_non_southerly | 22:00 | 806 | 1.094 | 245 | 30.397 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_non_southerly | 23:00 | 809 | 1.113 | 234 | 28.925 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_southerly_flow | 20:00 | 292 | 1.221 | 79 | 27.055 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_southerly_flow | 21:00 | 290 | 1.229 | 82 | 28.276 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_southerly_flow | 22:00 | 290 | 1.149 | 90 | 31.034 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |
| legacy_2009_start | Onda 3E legacy 2009-start binary-macro interactions | macro_southerly_flow | 23:00 | 287 | 1.094 | 94 | 32.753 | legacy_2009_start | 2009-04-23 | EXPERIMENT_ONLY |

## Model Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status | test_year | variant_id | train_start |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_challenger | 20:00 | 4206 | 365 | 1.241 | true | EXPERIMENT_ONLY | 2023 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 21:00 | 4206 | 365 | 1.160 | true | EXPERIMENT_ONLY | 2023 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 22:00 | 4206 | 365 | 1.076 | true | EXPERIMENT_ONLY | 2023 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 23:00 | 4206 | 365 | 1.084 | true | EXPERIMENT_ONLY | 2023 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 20:00 | 4571 | 366 | 1.298 | true | EXPERIMENT_ONLY | 2024 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 21:00 | 4571 | 366 | 1.194 | true | EXPERIMENT_ONLY | 2024 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 22:00 | 4571 | 366 | 1.127 | true | EXPERIMENT_ONLY | 2024 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 23:00 | 4571 | 366 | 1.123 | true | EXPERIMENT_ONLY | 2024 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 20:00 | 4937 | 365 | 1.290 | true | EXPERIMENT_ONLY | 2025 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 21:00 | 4937 | 365 | 1.238 | true | EXPERIMENT_ONLY | 2025 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 22:00 | 4937 | 365 | 1.123 | true | EXPERIMENT_ONLY | 2025 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 23:00 | 4937 | 365 | 1.118 | true | EXPERIMENT_ONLY | 2025 | legacy_2009_start | 2009-04-23 |
| ridge_challenger | 20:00 | 4011 | 365 | 1.238 | true | EXPERIMENT_ONLY | 2023 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 21:00 | 4011 | 365 | 1.154 | true | EXPERIMENT_ONLY | 2023 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 22:00 | 4011 | 365 | 1.074 | true | EXPERIMENT_ONLY | 2023 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 23:00 | 4011 | 365 | 1.082 | true | EXPERIMENT_ONLY | 2023 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 20:00 | 4376 | 366 | 1.298 | true | EXPERIMENT_ONLY | 2024 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 21:00 | 4376 | 366 | 1.190 | true | EXPERIMENT_ONLY | 2024 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 22:00 | 4376 | 366 | 1.127 | true | EXPERIMENT_ONLY | 2024 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 23:00 | 4376 | 366 | 1.123 | true | EXPERIMENT_ONLY | 2024 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 20:00 | 4742 | 365 | 1.290 | true | EXPERIMENT_ONLY | 2025 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 21:00 | 4742 | 365 | 1.235 | true | EXPERIMENT_ONLY | 2025 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 22:00 | 4742 | 365 | 1.120 | true | EXPERIMENT_ONLY | 2025 | continuous_2012_start | 2012-01-01 |
| ridge_challenger | 23:00 | 4742 | 365 | 1.116 | true | EXPERIMENT_ONLY | 2025 | continuous_2012_start | 2012-01-01 |
