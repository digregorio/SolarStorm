# Onda 3D Binary-Macro Interaction Model Report

Generated: 2026-06-09

## Decision

| decision_status | decision_rationale | mean_mae_delta_vs_no_interaction | production_status |
| --- | --- | --- | --- |
| READY_FOR_ONDA4_MODEL_RERUN | Onda 3D binary-macro interaction experiment completed. | -0.029970032769595867 | EXPERIMENT_ONLY |

## Interaction Feature Audit

| feature | source_feature | macro_value | interaction_type | production_status |
| --- | --- | --- | --- | --- |
| foehn_score_x_macro_non_southerly | foehn_score | macro_non_southerly | continuous_x_binary_macro | EXPERIMENT_ONLY |
| foehn_score_x_macro_southerly_flow | foehn_score | macro_southerly_flow | continuous_x_binary_macro | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_non_southerly | cloud_cover_suppression | macro_non_southerly | continuous_x_binary_macro | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_southerly_flow | cloud_cover_suppression | macro_southerly_flow | continuous_x_binary_macro | EXPERIMENT_ONLY |

## Challenger Comparison

| cp | test_year | interaction_mae | no_interaction_mae | mae_delta | beats_no_interaction | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 20:00 | 2023 | 1.2408036552638424 | 1.3284799607654612 | -0.08767630550161876 | True | EXPERIMENT_ONLY |
| 21:00 | 2023 | 1.160047899655754 | 1.2115345202493055 | -0.05148662059355158 | True | EXPERIMENT_ONLY |
| 22:00 | 2023 | 1.0756289562734336 | 1.1253194844495127 | -0.04969052817607911 | True | EXPERIMENT_ONLY |
| 23:00 | 2023 | 1.0842245506158878 | 1.1206958953579038 | -0.036471344742015965 | True | EXPERIMENT_ONLY |
| 20:00 | 2024 | 1.2982372441222527 | 1.3368947066521863 | -0.03865746252993363 | True | EXPERIMENT_ONLY |
| 21:00 | 2024 | 1.1935159165818656 | 1.20568745437114 | -0.012171537789274378 | True | EXPERIMENT_ONLY |
| 22:00 | 2024 | 1.1272397054576053 | 1.1361141378350188 | -0.008874432377413477 | True | EXPERIMENT_ONLY |
| 23:00 | 2024 | 1.1225216046022026 | 1.1394583343799836 | -0.016936729777780934 | True | EXPERIMENT_ONLY |
| 20:00 | 2025 | 1.2903412248060548 | 1.3082047863177653 | -0.017863561511710424 | True | EXPERIMENT_ONLY |
| 21:00 | 2025 | 1.2381508057435093 | 1.2580350789080303 | -0.019884273164521016 | True | EXPERIMENT_ONLY |
| 22:00 | 2025 | 1.1228737810053278 | 1.1288800812597533 | -0.006006300254425501 | True | EXPERIMENT_ONLY |
| 23:00 | 2025 | 1.117642738979003 | 1.1315640357958285 | -0.013921296816825635 | True | EXPERIMENT_ONLY |

## Model Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status | test_year |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train_mean_null | 20:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 20:00 | 4206 | 365 | 1.2408036552638424 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 21:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 21:00 | 4206 | 365 | 1.160047899655754 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 22:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 22:00 | 4206 | 365 | 1.0756289562734336 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 23:00 | 4206 | 365 | 2.901045473198757 | False | EXPERIMENT_ONLY | 2023 |
| ridge_challenger | 23:00 | 4206 | 365 | 1.0842245506158878 | True | EXPERIMENT_ONLY | 2023 |
| train_mean_null | 20:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 20:00 | 4571 | 366 | 1.2982372441222527 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 21:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 21:00 | 4571 | 366 | 1.1935159165818656 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 22:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 22:00 | 4571 | 366 | 1.1272397054576053 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 23:00 | 4571 | 366 | 3.1402611856883444 | False | EXPERIMENT_ONLY | 2024 |
| ridge_challenger | 23:00 | 4571 | 366 | 1.1225216046022026 | True | EXPERIMENT_ONLY | 2024 |
| train_mean_null | 20:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 20:00 | 4937 | 365 | 1.2903412248060548 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 21:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 21:00 | 4937 | 365 | 1.2381508057435093 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 22:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 22:00 | 4937 | 365 | 1.1228737810053278 | True | EXPERIMENT_ONLY | 2025 |
| train_mean_null | 23:00 | 4937 | 365 | 2.8152901906487493 | False | EXPERIMENT_ONLY | 2025 |
| ridge_challenger | 23:00 | 4937 | 365 | 1.117642738979003 | True | EXPERIMENT_ONLY | 2025 |

## Scope

All outputs are EXPERIMENT_ONLY.
