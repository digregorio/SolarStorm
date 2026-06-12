# Onda 3 Open-Meteo Pilot Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Open-Meteo augmented candidate is compared against local-only reference on identical covered rows.

## Decision

| decision_status | decision_rationale | augmented_minus_local_mae | production_status |
| --- | --- | --- | --- |
| PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION | Open-Meteo augmented candidate improved same-row MAE. | -0.23140872979353477 | EXPERIMENT_ONLY |

## Join Scope

| n_joined_rows | n_joined_dates | production_status |
| --- | --- | --- |
| 1096 | 1096 | EXPERIMENT_ONLY |

## Model Results

| test_year | candidate_id | n_train | n_test | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | local_only_reference | 365 | 366 | 1.1113864937705416 | 28.688524590163933 | EXPERIMENT_ONLY |
| 2024 | open_meteo_augmented | 365 | 366 | 0.9272635926771413 | 39.89071038251366 | EXPERIMENT_ONLY |
| 2025 | local_only_reference | 731 | 365 | 1.1135329936600247 | 27.123287671232877 | EXPERIMENT_ONLY |
| 2025 | open_meteo_augmented | 731 | 365 | 0.8348384351663551 | 36.71232876712329 | EXPERIMENT_ONLY |
