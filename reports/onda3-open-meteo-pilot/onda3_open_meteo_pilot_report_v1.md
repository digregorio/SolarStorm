# Onda 3 Open-Meteo Pilot Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Open-Meteo augmented candidate is compared against local-only reference on identical covered rows.

## Decision

| decision_status | decision_rationale | augmented_minus_local_mae | production_status |
| --- | --- | --- | --- |
| PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION | Open-Meteo augmented candidate improved same-row MAE. | -0.13349137097794306 | EXPERIMENT_ONLY |

## Join Scope

| n_joined_rows | n_joined_dates | production_status |
| --- | --- | --- |
| 72 | 72 | EXPERIMENT_ONLY |

## Model Results

| test_year | candidate_id | n_train | n_test | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | local_only_reference | 24 | 24 | 1.3836484514601561 | 29.166666666666668 | EXPERIMENT_ONLY |
| 2024 | open_meteo_augmented | 24 | 24 | 1.3825887880494936 | 33.33333333333333 | EXPERIMENT_ONLY |
| 2025 | local_only_reference | 48 | 24 | 1.383732126345748 | 29.166666666666668 | EXPERIMENT_ONLY |
| 2025 | open_meteo_augmented | 48 | 24 | 1.1178090478005245 | 25.0 | EXPERIMENT_ONLY |
