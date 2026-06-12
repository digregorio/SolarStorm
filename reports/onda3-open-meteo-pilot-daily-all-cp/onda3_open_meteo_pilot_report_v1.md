# Onda 3 Open-Meteo Pilot Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Open-Meteo augmented candidate is compared against local-only reference on identical covered rows.

## Decision

| decision_status | decision_rationale | augmented_minus_local_mae | production_status |
| --- | --- | --- | --- |
| PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION | Open-Meteo augmented candidate improved same-row MAE. | -0.2801135758300398 | EXPERIMENT_ONLY |

## Join Scope

| n_joined_rows | n_joined_dates | production_status |
| --- | --- | --- |
| 4384 | 1096 | EXPERIMENT_ONLY |

## Model Results

| test_year | candidate_id | n_train | n_test | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | local_only_reference | 1460 | 1464 | 1.1767644427092263 | 26.98087431693989 | EXPERIMENT_ONLY |
| 2024 | open_meteo_augmented | 1460 | 1464 | 0.9534499495398605 | 38.66120218579235 | EXPERIMENT_ONLY |
| 2025 | local_only_reference | 2924 | 1460 | 1.2054657917591576 | 25.410958904109588 | EXPERIMENT_ONLY |
| 2025 | open_meteo_augmented | 2924 | 1460 | 0.868553133268444 | 35.41095890410959 | EXPERIMENT_ONLY |
