# Onda 3C Rolling Temporal Model Iteration Report

Generated: 2026-06-09

## Decision

| decision_status | decision_rationale | production_status |
| --- | --- | --- |
| READY_FOR_ONDA4_MODEL_RERUN | Onda 3C rolling temporal model iteration completed. | EXPERIMENT_ONLY |

## Temporal Diagnostics

| diagnostic | status | test_years | n_challenger_rows | production_status |
| --- | --- | --- | --- | --- |
| all_challengers_beat_null | PASS | 2023,2024,2025 | 12 | EXPERIMENT_ONLY |

## Model Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status | test_year |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train_mean_null | 20:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 20:00 | 4206 | 365 | 1.3284799607654612 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 21:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 21:00 | 4206 | 365 | 1.2115345202493055 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 22:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 22:00 | 4206 | 365 | 1.1253194844495127 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 23:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 23:00 | 4206 | 365 | 1.1206958953579038 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 20:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 20:00 | 4571 | 366 | 1.3368947066521863 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 21:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 21:00 | 4571 | 366 | 1.20568745437114 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 22:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 22:00 | 4571 | 366 | 1.1361141378350188 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 23:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 23:00 | 4571 | 366 | 1.1394583343799836 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 20:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 20:00 | 4937 | 365 | 1.3082047863177653 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 21:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 21:00 | 4937 | 365 | 1.2580350789080303 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 22:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 22:00 | 4937 | 365 | 1.1288800812597533 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 23:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 23:00 | 4937 | 365 | 1.1315640357958285 | True | EXPERIMENT_ONLY | 2025 |

## Uncertainty and Abstention

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

All outputs are EXPERIMENT_ONLY.
