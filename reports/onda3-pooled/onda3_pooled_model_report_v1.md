# Onda 3F Pooled Temporal/Regime Model Report

Generated: 2026-06-09



Scope: pre-Open-Meteo local-data experiment. Open-Meteo forecast data is not integrated.

All outputs remain EXPERIMENT_ONLY.

## Decision

| decision_status | decision_rationale | production_status |
| --- | --- | --- |
| READY_FOR_ONDA3_AUDIT_COMPARISON | Onda 3F pooled temporal/regime model iteration completed. | EXPERIMENT_ONLY |

## Temporal Diagnostics

| diagnostic | status | test_years | n_challenger_rows | n_valid_folds | production_status |
| --- | --- | --- | --- | --- | --- |
| all_pooled_challengers_beat_null | PASS | 2023,2024,2025 | 3 | 3 | EXPERIMENT_ONLY |

## Model Results

| test_year | model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | train_mean_null | ALL | 16824 | 1460 | 2.901 | false | EXPERIMENT_ONLY |
| 2023 | ridge_challenger | ALL | 16824 | 1460 | 1.043 | true | EXPERIMENT_ONLY |
| 2024 | train_mean_null | ALL | 18284 | 1464 | 3.140 | false | EXPERIMENT_ONLY |
| 2024 | ridge_challenger | ALL | 18284 | 1464 | 1.066 | true | EXPERIMENT_ONLY |
| 2025 | train_mean_null | ALL | 19748 | 1460 | 2.815 | false | EXPERIMENT_ONLY |
| 2025 | ridge_challenger | ALL | 19748 | 1460 | 1.077 | true | EXPERIMENT_ONLY |

## Exact Bracket Overall

| iteration_id | iteration_label | n_days | n_cp_rows | mae | any_cp_exact_pct | cp23_exact_pct | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 1096 | 4384 | 1.062 | 44.434 | 31.478 | 28.650 | 31.569 | 31.934 | 31.478 | EXPERIMENT_ONLY |

## Exact Bracket By Month

any_cp_exact_pct counts a day as correct if any checkpoint hit the exact integer bracket. cp23_exact_pct is the last-checkpoint-only rate.

| iteration_id | iteration_label | month | n_days | any_cp_exact_days | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-01 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-02 | 28 | 10 | 35.714 | 28 | 7 | 25.000 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-03 | 31 | 15 | 48.387 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-04 | 30 | 17 | 56.667 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-05 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-06 | 30 | 18 | 60.000 | 30 | 15 | 50.000 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-07 | 31 | 12 | 38.710 | 31 | 6 | 19.355 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-08 | 31 | 13 | 41.935 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-09 | 30 | 11 | 36.667 | 30 | 7 | 23.333 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-10 | 31 | 14 | 45.161 | 31 | 12 | 38.710 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-11 | 30 | 14 | 46.667 | 30 | 14 | 46.667 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-12 | 31 | 9 | 29.032 | 31 | 6 | 19.355 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-01 | 31 | 8 | 25.806 | 31 | 4 | 12.903 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-02 | 29 | 11 | 37.931 | 29 | 7 | 24.138 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-03 | 31 | 13 | 41.935 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-04 | 30 | 18 | 60.000 | 30 | 7 | 23.333 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-05 | 31 | 14 | 45.161 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-06 | 30 | 13 | 43.333 | 30 | 8 | 26.667 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-07 | 31 | 17 | 54.839 | 31 | 14 | 45.161 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-08 | 31 | 15 | 48.387 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-09 | 30 | 15 | 50.000 | 30 | 13 | 43.333 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-10 | 31 | 17 | 54.839 | 31 | 13 | 41.935 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-11 | 30 | 15 | 50.000 | 30 | 11 | 36.667 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-12 | 31 | 13 | 41.935 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-01 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-02 | 28 | 11 | 39.286 | 28 | 8 | 28.571 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-03 | 31 | 12 | 38.710 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-04 | 30 | 15 | 50.000 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-05 | 31 | 19 | 61.290 | 31 | 12 | 38.710 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-06 | 30 | 10 | 33.333 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-07 | 31 | 15 | 48.387 | 31 | 9 | 29.032 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-08 | 31 | 15 | 48.387 | 31 | 11 | 35.484 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-09 | 30 | 11 | 36.667 | 30 | 9 | 30.000 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-10 | 31 | 15 | 48.387 | 31 | 10 | 32.258 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-11 | 30 | 14 | 46.667 | 30 | 10 | 33.333 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2025-12 | 31 | 8 | 25.806 | 31 | 8 | 25.806 | EXPERIMENT_ONLY |

## Exact Bracket By Month And CP

| iteration_id | iteration_label | month | cp | n_cp_rows | exact_bracket_rows | exact_bracket_pct | mae | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-01 | 20:00 | 31 | 5 | 16.129 | 1.325 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-01 | 21:00 | 31 | 10 | 32.258 | 1.180 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-01 | 22:00 | 31 | 11 | 35.484 | 1.154 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-01 | 23:00 | 31 | 11 | 35.484 | 1.118 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-02 | 20:00 | 28 | 7 | 25.000 | 1.089 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-02 | 21:00 | 28 | 6 | 21.429 | 0.967 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-02 | 22:00 | 28 | 7 | 25.000 | 0.936 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-02 | 23:00 | 28 | 7 | 25.000 | 0.936 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-03 | 20:00 | 31 | 11 | 35.484 | 0.994 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-03 | 21:00 | 31 | 13 | 41.935 | 0.911 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-03 | 22:00 | 31 | 14 | 45.161 | 0.955 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-03 | 23:00 | 31 | 11 | 35.484 | 1.008 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-04 | 20:00 | 30 | 14 | 46.667 | 0.809 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-04 | 21:00 | 30 | 12 | 40.000 | 0.816 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-04 | 22:00 | 30 | 12 | 40.000 | 0.781 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-04 | 23:00 | 30 | 11 | 36.667 | 0.794 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-05 | 20:00 | 31 | 13 | 41.935 | 0.960 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-05 | 21:00 | 31 | 13 | 41.935 | 0.958 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-05 | 22:00 | 31 | 10 | 32.258 | 1.056 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-05 | 23:00 | 31 | 10 | 32.258 | 1.071 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-06 | 20:00 | 30 | 11 | 36.667 | 0.874 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-06 | 21:00 | 30 | 12 | 40.000 | 0.921 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-06 | 22:00 | 30 | 13 | 43.333 | 0.958 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-06 | 23:00 | 30 | 15 | 50.000 | 0.901 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-07 | 20:00 | 31 | 7 | 22.581 | 1.313 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-07 | 21:00 | 31 | 7 | 22.581 | 1.314 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-07 | 22:00 | 31 | 8 | 25.806 | 1.053 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-07 | 23:00 | 31 | 6 | 19.355 | 1.060 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-08 | 20:00 | 31 | 8 | 25.806 | 1.056 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-08 | 21:00 | 31 | 8 | 25.806 | 1.051 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-08 | 22:00 | 31 | 9 | 29.032 | 1.057 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-08 | 23:00 | 31 | 9 | 29.032 | 1.014 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-09 | 20:00 | 30 | 6 | 20.000 | 1.162 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-09 | 21:00 | 30 | 5 | 16.667 | 1.128 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-09 | 22:00 | 30 | 8 | 26.667 | 0.827 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-09 | 23:00 | 30 | 7 | 23.333 | 0.847 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-10 | 20:00 | 31 | 4 | 12.903 | 1.348 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-10 | 21:00 | 31 | 14 | 45.161 | 1.037 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-10 | 22:00 | 31 | 12 | 38.710 | 1.110 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-10 | 23:00 | 31 | 12 | 38.710 | 1.114 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-11 | 20:00 | 30 | 8 | 26.667 | 1.061 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-11 | 21:00 | 30 | 13 | 43.333 | 0.798 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-11 | 22:00 | 30 | 13 | 43.333 | 0.808 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-11 | 23:00 | 30 | 14 | 46.667 | 0.833 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-12 | 20:00 | 31 | 7 | 22.581 | 1.458 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-12 | 21:00 | 31 | 5 | 16.129 | 1.319 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-12 | 22:00 | 31 | 6 | 19.355 | 1.341 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2023-12 | 23:00 | 31 | 6 | 19.355 | 1.377 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-01 | 20:00 | 31 | 4 | 12.903 | 2.185 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-01 | 21:00 | 31 | 4 | 12.903 | 1.945 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-01 | 22:00 | 31 | 4 | 12.903 | 1.924 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-01 | 23:00 | 31 | 4 | 12.903 | 1.988 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-02 | 20:00 | 29 | 6 | 20.690 | 1.288 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-02 | 21:00 | 29 | 6 | 20.690 | 1.211 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-02 | 22:00 | 29 | 7 | 24.138 | 1.154 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-02 | 23:00 | 29 | 7 | 24.138 | 1.159 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-03 | 20:00 | 31 | 10 | 32.258 | 1.127 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-03 | 21:00 | 31 | 10 | 32.258 | 1.076 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-03 | 22:00 | 31 | 9 | 29.032 | 1.043 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-03 | 23:00 | 31 | 8 | 25.806 | 1.002 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-04 | 20:00 | 30 | 13 | 43.333 | 0.907 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-04 | 21:00 | 30 | 14 | 46.667 | 0.910 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-04 | 22:00 | 30 | 7 | 23.333 | 1.066 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-04 | 23:00 | 30 | 7 | 23.333 | 1.083 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-05 | 20:00 | 31 | 8 | 25.806 | 1.050 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-05 | 21:00 | 31 | 12 | 38.710 | 0.889 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-05 | 22:00 | 31 | 9 | 29.032 | 0.940 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-05 | 23:00 | 31 | 9 | 29.032 | 0.936 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-06 | 20:00 | 30 | 10 | 33.333 | 0.998 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-06 | 21:00 | 30 | 9 | 30.000 | 1.023 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-06 | 22:00 | 30 | 8 | 26.667 | 0.914 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-06 | 23:00 | 30 | 8 | 26.667 | 0.895 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-07 | 20:00 | 31 | 10 | 32.258 | 0.838 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-07 | 21:00 | 31 | 10 | 32.258 | 0.799 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-07 | 22:00 | 31 | 13 | 41.935 | 0.724 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-07 | 23:00 | 31 | 14 | 45.161 | 0.684 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-08 | 20:00 | 31 | 11 | 35.484 | 0.835 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-08 | 21:00 | 31 | 12 | 38.710 | 0.799 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-08 | 22:00 | 31 | 8 | 25.806 | 0.922 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | 2024-08 | 23:00 | 31 | 9 | 29.032 | 0.884 | EXPERIMENT_ONLY |

_Showing 80 of 144 rows. Full table is in CSV._

## Binary Macro Regime Performance

| iteration_id | iteration_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_rows | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_non_southerly | 3225 | 833 | 1.065 | 984 | 30.512 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | macro_southerly_flow | 1159 | 319 | 1.054 | 371 | 32.010 | EXPERIMENT_ONLY |

## Slice Diagnostics

| iteration_id | iteration_label | slice_column | slice_value | rows | mae | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | cp | 20:00 | 1096 | 1.137 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | cp | 21:00 | 1096 | 1.054 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | cp | 22:00 | 1096 | 1.028 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | cp | 23:00 | 1096 | 1.028 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | binary_macro_regime_label | macro_non_southerly | 3225 | 1.065 | EXPERIMENT_ONLY |
| onda3_f_pooled_temporal_regime | Onda 3F pooled temporal/regime | binary_macro_regime_label | macro_southerly_flow | 1159 | 1.054 | EXPERIMENT_ONLY |

## Feature Audit

| feature | feature_role | source_feature | production_status | macro_value |
| --- | --- | --- | --- | --- |
| tmin_delta_tmax | pooled_numeric_input | tmin_delta_tmax | EXPERIMENT_ONLY |  |
| tmax_dminus1 | pooled_numeric_input | tmax_dminus1 | EXPERIMENT_ONLY |  |
| regime_score_argmax | pooled_categorical_input | regime_score_argmax | EXPERIMENT_ONLY |  |
| regime_label | pooled_categorical_input | regime_label | EXPERIMENT_ONLY |  |
| dewpoint_collapse_rate_3h | pooled_numeric_input | dewpoint_collapse_rate_3h | EXPERIMENT_ONLY |  |
| cloud_cover_suppression_x_macro_southerly_flow | continuous_x_binary_macro | cloud_cover_suppression | EXPERIMENT_ONLY | macro_southerly_flow |
| precip_disruption | pooled_numeric_input | precip_disruption | EXPERIMENT_ONLY |  |
| pressure_trend_3h | pooled_numeric_input | pressure_trend_3h | EXPERIMENT_ONLY |  |
| doy_cos | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| month_sin | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| cloud_cover_suppression_x_macro_non_southerly | continuous_x_binary_macro | cloud_cover_suppression | EXPERIMENT_ONLY | macro_non_southerly |
| foehn_score_x_macro_non_southerly | continuous_x_binary_macro | foehn_score | EXPERIMENT_ONLY | macro_non_southerly |
| month_cos | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| cp_sin | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| binary_macro_regime_label | pooled_categorical_input | binary_macro_regime_label | EXPERIMENT_ONLY |  |
| day_sequence_pattern | pooled_categorical_input | day_sequence_pattern | EXPERIMENT_ONLY |  |
| nw_sector_not_foehn | pooled_numeric_input | nw_sector_not_foehn | EXPERIMENT_ONLY |  |
| foehn_score | pooled_numeric_input | foehn_score | EXPERIMENT_ONLY |  |
| warming_rate_06_09 | pooled_numeric_input | warming_rate_06_09 | EXPERIMENT_ONLY |  |
| cloud_base_transparency | pooled_numeric_input | cloud_base_transparency | EXPERIMENT_ONLY |  |
| cloud_cover_suppression | pooled_numeric_input | cloud_cover_suppression | EXPERIMENT_ONLY |  |
| cp_cos | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| wind_dir_change_s_to_n | pooled_numeric_input | wind_dir_change_s_to_n | EXPERIMENT_ONLY |  |
| dewpoint_depression | pooled_numeric_input | dewpoint_depression | EXPERIMENT_ONLY |  |
| doy_sin | pooled_temporal_cyclic | cp_or_date_local | EXPERIMENT_ONLY |  |
| nocturnal_plateau_flag | pooled_numeric_input | nocturnal_plateau_flag | EXPERIMENT_ONLY |  |
| slope_3h | pooled_numeric_input | slope_3h | EXPERIMENT_ONLY |  |
| foehn_score_x_macro_southerly_flow | continuous_x_binary_macro | foehn_score | EXPERIMENT_ONLY | macro_southerly_flow |
| prefrontal_warming_window | pooled_numeric_input | prefrontal_warming_window | EXPERIMENT_ONLY |  |

## Uncertainty and Abstention

| test_year | model_name | cp | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | ridge_challenger | ALL | 0.861 | 2.191 | abstain when pooled CP/regime slice support is weak | EXPERIMENT_ONLY |
| 2024 | ridge_challenger | ALL | 0.892 | 2.256 | abstain when pooled CP/regime slice support is weak | EXPERIMENT_ONLY |
| 2025 | ridge_challenger | ALL | 0.845 | 2.247 | abstain when pooled CP/regime slice support is weak | EXPERIMENT_ONLY |
