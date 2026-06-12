# Onda 3 Open-Meteo Calibrated Nested Validation Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Calibrated Open-Meteo candidates are compared against local-only Onda 3F and raw GFS Previous Runs on identical covered rows.

## Decision

| decision_status | decision_rationale | n_outer_folds | selected_mean_test_mae | always_local_mean_test_mae | always_open_meteo_augmented_mean_test_mae | always_gfs_previous_runs_mean_test_mae | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW | Calibrated Open-Meteo improved or was selected, but coverage/fold support is not sufficient for a final model decision. | 1 | 0.8258065144596652 | 1.0662765512517574 | 0.7609956986376547 | 1.426499546010817 | EXPERIMENT_ONLY |

## Candidate Scope

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | train_start | train_end | train_start_year | train_end_year | evaluation_start | evaluation_end | n_train_rows | n_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 2024 | 2023 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_mean_raw | om family mean raw | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_median_raw | om family median raw | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 |  | 2012 |  | 2023-01-01 | 2023-12-31 | 0 | 1456 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_mean_raw | om family mean raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_median_raw | om family median raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_mean_raw | om family mean raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_median_raw | om family median raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 1456 | 1388 | EXPERIMENT_ONLY |

## Selection

| outer_test_year | validation_year | selected_candidate_id | selected_candidate_label | selected_validation_mae | selected_validation_any_cp_exact_pct | selected_validation_cp23_exact_pct | selected_test_mae | selected_test_any_cp_exact_pct | selected_test_cp23_exact_pct | validation_candidate_count | test_candidate_count | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 0.7166820365033622 | 42.363112391930834 | 42.363112391930834 | 0.8258065144596652 | 38.63013698630137 | 38.63013698630137 | 10 | 10 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |

## Selected Test Summary

| outer_test_year | evaluation_year | candidate_id | candidate_label | mae | any_cp_exact_pct | cp23_exact_pct | n_days_with_cp23 | cp23_exact_days | n_days | n_cp_rows | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | 0.8258065144596652 | 38.63013698630137 | 38.63013698630137 | 365 | 141 | 365 | 1460 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |

## Candidate Metrics

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | n_days | n_cp_rows | mae | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | 2024 | local_only_onda3f | Local-only Onda 3F | 347 | 1388 | 1.0611235852728234 | 42.93948126801153 | 347 | 96 | 27.6657060518732 | EXPERIMENT_ONLY | 29.106628242074926 | 30.835734870317005 | 28.24207492795389 | 27.6657060518732 |
| test | 2024 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 347 | 1388 | 1.264647752129061 | 16.138328530259365 | 347 | 56 | 16.138328530259365 | EXPERIMENT_ONLY | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 |
| test | 2024 | 2024 | om_family_mean_raw | om family mean raw | 347 | 1388 | 1.3189048991354466 | 15.85014409221902 | 347 | 55 | 15.85014409221902 | EXPERIMENT_ONLY | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 |
| test | 2024 | 2024 | om_family_median_raw | om family median raw | 347 | 1388 | 1.3485590778097982 | 16.714697406340058 | 347 | 58 | 16.714697406340058 | EXPERIMENT_ONLY | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 |
| test | 2024 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 347 | 1388 | 0.7576784493916929 | 40.345821325648416 | 347 | 140 | 40.345821325648416 | EXPERIMENT_ONLY | 40.345821325648416 | 40.345821325648416 | 40.345821325648416 | 40.345821325648416 |
| test | 2024 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 347 | 1388 | 0.7166820365033622 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| test | 2024 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 347 | 1388 | 0.7354554772358184 | 41.4985590778098 | 347 | 139 | 40.05763688760807 | EXPERIMENT_ONLY | 39.19308357348703 | 39.19308357348703 | 39.481268011527376 | 40.05763688760807 |
| test | 2024 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 347 | 1388 | 0.7396154001453107 | 42.93948126801153 | 347 | 149 | 42.93948126801153 | EXPERIMENT_ONLY | 42.93948126801153 | 42.93948126801153 | 42.93948126801153 | 42.93948126801153 |
| test | 2024 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 347 | 1388 | 1.4302593659942364 | 13.8328530259366 | 347 | 48 | 13.8328530259366 | EXPERIMENT_ONLY | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 |
| test | 2024 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 347 | 1388 | 0.7589523278690488 | 51.008645533141205 | 347 | 151 | 43.51585014409222 | EXPERIMENT_ONLY | 40.05763688760807 | 42.363112391930834 | 42.07492795389049 | 43.51585014409222 |
| test | 2025 | 2025 | local_only_onda3f | Local-only Onda 3F | 365 | 1460 | 1.0714295172306914 | 45.47945205479452 | 365 | 113 | 30.958904109589042 | EXPERIMENT_ONLY | 27.671232876712327 | 31.506849315068493 | 32.87671232876712 | 30.958904109589042 |
| test | 2025 | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | 365 | 1460 | 1.2107920403666472 | 19.726027397260275 | 365 | 72 | 19.726027397260275 | EXPERIMENT_ONLY | 19.726027397260275 | 19.726027397260275 | 19.726027397260275 | 19.726027397260275 |
| test | 2025 | 2025 | om_family_mean_raw | om family mean raw | 365 | 1460 | 1.292876712328767 | 17.80821917808219 | 365 | 65 | 17.80821917808219 | EXPERIMENT_ONLY | 17.80821917808219 | 17.80821917808219 | 17.80821917808219 | 17.80821917808219 |
| test | 2025 | 2025 | om_family_median_raw | om family median raw | 365 | 1460 | 1.33 | 18.356164383561644 | 365 | 67 | 18.356164383561644 | EXPERIMENT_ONLY | 18.356164383561644 | 18.356164383561644 | 18.356164383561644 | 18.356164383561644 |
| test | 2025 | 2025 | om_family_month_bias_corrected | om family month bias corrected | 365 | 1460 | 0.8177262522176716 | 38.63013698630137 | 365 | 141 | 38.63013698630137 | EXPERIMENT_ONLY | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 |
| test | 2025 | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | 365 | 1460 | 0.8258065144596652 | 38.63013698630137 | 365 | 141 | 38.63013698630137 | EXPERIMENT_ONLY | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 |
| test | 2025 | 2025 | om_family_regime_bias_corrected | om family regime bias corrected | 365 | 1460 | 0.8573018487151092 | 34.794520547945204 | 365 | 122 | 33.42465753424658 | EXPERIMENT_ONLY | 33.42465753424658 | 33.15068493150685 | 32.87671232876712 | 33.42465753424658 |
| test | 2025 | 2025 | om_family_season_bias_corrected | om family season bias corrected | 365 | 1460 | 0.7830872917037301 | 42.19178082191781 | 365 | 154 | 42.19178082191781 | EXPERIMENT_ONLY | 42.19178082191781 | 42.19178082191781 | 42.19178082191781 | 42.19178082191781 |
| test | 2025 | 2025 | om_gfs_previous_runs_raw | om gfs previous runs raw | 365 | 1460 | 1.4227397260273975 | 15.342465753424658 | 365 | 56 | 15.342465753424658 | EXPERIMENT_ONLY | 15.342465753424658 | 15.342465753424658 | 15.342465753424658 | 15.342465753424658 |
| test | 2025 | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 365 | 1460 | 0.7630390694062605 | 53.15068493150685 | 365 | 156 | 42.73972602739726 | EXPERIMENT_ONLY | 40.0 | 41.64383561643836 | 41.64383561643836 | 42.73972602739726 |
| validation | 2025 | 2024 | local_only_onda3f | Local-only Onda 3F | 347 | 1388 | 1.0611235852728234 | 42.93948126801153 | 347 | 96 | 27.6657060518732 | EXPERIMENT_ONLY | 29.106628242074926 | 30.835734870317005 | 28.24207492795389 | 27.6657060518732 |
| validation | 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 347 | 1388 | 1.264647752129061 | 16.138328530259365 | 347 | 56 | 16.138328530259365 | EXPERIMENT_ONLY | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 |
| validation | 2025 | 2024 | om_family_mean_raw | om family mean raw | 347 | 1388 | 1.3189048991354466 | 15.85014409221902 | 347 | 55 | 15.85014409221902 | EXPERIMENT_ONLY | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 |
| validation | 2025 | 2024 | om_family_median_raw | om family median raw | 347 | 1388 | 1.3485590778097982 | 16.714697406340058 | 347 | 58 | 16.714697406340058 | EXPERIMENT_ONLY | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 |
| validation | 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 347 | 1388 | 0.7576784493916929 | 40.345821325648416 | 347 | 140 | 40.345821325648416 | EXPERIMENT_ONLY | 40.345821325648416 | 40.345821325648416 | 40.345821325648416 | 40.345821325648416 |
| validation | 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 347 | 1388 | 0.7166820365033622 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| validation | 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 347 | 1388 | 0.7354554772358184 | 41.4985590778098 | 347 | 139 | 40.05763688760807 | EXPERIMENT_ONLY | 39.19308357348703 | 39.19308357348703 | 39.481268011527376 | 40.05763688760807 |
| validation | 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 347 | 1388 | 0.7396154001453107 | 42.93948126801153 | 347 | 149 | 42.93948126801153 | EXPERIMENT_ONLY | 42.93948126801153 | 42.93948126801153 | 42.93948126801153 | 42.93948126801153 |
| validation | 2025 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 347 | 1388 | 1.4302593659942364 | 13.8328530259366 | 347 | 48 | 13.8328530259366 | EXPERIMENT_ONLY | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 |
| validation | 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 347 | 1388 | 0.7589523278690488 | 51.008645533141205 | 347 | 151 | 43.51585014409222 | EXPERIMENT_ONLY | 40.05763688760807 | 42.363112391930834 | 42.07492795389049 | 43.51585014409222 |

## Regime Performance

| stage | outer_test_year | candidate_id | candidate_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1073 | 277 | 1.073900847129206 | 28.984156570363467 | EXPERIMENT_ONLY |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 315 | 89 | 1.0175997694890186 | 28.888888888888886 | EXPERIMENT_ONLY |
| test | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1073 | 277 | 1.3941732670557616 | 12.022367194780987 | EXPERIMENT_ONLY |
| test | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 315 | 89 | 0.8234386171565224 | 30.158730158730158 | EXPERIMENT_ONLY |
| test | 2024 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1073 | 277 | 1.456924510717614 | 11.276794035414724 | EXPERIMENT_ONLY |
| test | 2024 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 315 | 89 | 0.8487619047619048 | 31.428571428571427 | EXPERIMENT_ONLY |
| test | 2024 | om_family_median_raw | om family median raw | macro_non_southerly | 1073 | 277 | 1.4797763280521903 | 12.022367194780987 | EXPERIMENT_ONLY |
| test | 2024 | om_family_median_raw | om family median raw | macro_southerly_flow | 315 | 89 | 0.9015873015873016 | 32.698412698412696 | EXPERIMENT_ONLY |
| test | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1073 | 277 | 0.784241761366735 | 36.905871388630004 | EXPERIMENT_ONLY |
| test | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 315 | 89 | 0.6671945327275027 | 52.06349206349207 | EXPERIMENT_ONLY |
| test | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_non_southerly | 1073 | 277 | 0.7148953091022056 | 41.47250698974837 | EXPERIMENT_ONLY |
| test | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_southerly_flow | 315 | 89 | 0.7227682539682541 | 45.3968253968254 | EXPERIMENT_ONLY |
| test | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_non_southerly | 1073 | 277 | 0.7021921737216364 | 41.845293569431504 | EXPERIMENT_ONLY |
| test | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_southerly_flow | 315 | 89 | 0.8487619047619048 | 31.428571428571427 | EXPERIMENT_ONLY |
| test | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_non_southerly | 1073 | 277 | 0.7448229479555134 | 41.75209692451072 | EXPERIMENT_ONLY |
| test | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_southerly_flow | 315 | 89 | 0.7218766737950018 | 46.98412698412698 | EXPERIMENT_ONLY |
| test | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_non_southerly | 1073 | 277 | 1.5843429636533084 | 7.921714818266542 | EXPERIMENT_ONLY |
| test | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_southerly_flow | 315 | 89 | 0.9053968253968253 | 33.96825396825397 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1073 | 277 | 0.7977865351283903 | 38.11742777260019 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 315 | 89 | 0.6266694567919904 | 55.23809523809524 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1020 | 265 | 1.0916253573549455 | 30.686274509803923 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 440 | 121 | 1.024611887851738 | 30.909090909090907 | EXPERIMENT_ONLY |
| test | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1020 | 265 | 1.358597299557055 | 15.588235294117647 | EXPERIMENT_ONLY |
| test | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 440 | 121 | 0.868152575879793 | 29.318181818181817 | EXPERIMENT_ONLY |
| test | 2025 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1020 | 265 | 1.4668039215686273 | 14.215686274509803 | EXPERIMENT_ONLY |
| test | 2025 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 440 | 121 | 0.8896818181818181 | 26.136363636363637 | EXPERIMENT_ONLY |
| test | 2025 | om_family_median_raw | om family median raw | macro_non_southerly | 1020 | 265 | 1.5170588235294118 | 12.84313725490196 | EXPERIMENT_ONLY |
| test | 2025 | om_family_median_raw | om family median raw | macro_southerly_flow | 440 | 121 | 0.8963636363636364 | 31.136363636363633 | EXPERIMENT_ONLY |
| test | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1020 | 265 | 0.8288526261839391 | 34.80392156862745 | EXPERIMENT_ONLY |
| test | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 440 | 121 | 0.7919332943867784 | 47.5 | EXPERIMENT_ONLY |
| test | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | macro_non_southerly | 1020 | 265 | 0.8603027450980392 | 35.588235294117645 | EXPERIMENT_ONLY |
| test | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | macro_southerly_flow | 440 | 121 | 0.7458379797979797 | 45.68181818181819 | EXPERIMENT_ONLY |
| test | 2025 | om_family_regime_bias_corrected | om family regime bias corrected | macro_non_southerly | 1020 | 265 | 0.8425929972044152 | 36.27450980392157 | EXPERIMENT_ONLY |
| test | 2025 | om_family_regime_bias_corrected | om family regime bias corrected | macro_southerly_flow | 440 | 121 | 0.8913996408535362 | 26.136363636363637 | EXPERIMENT_ONLY |
| test | 2025 | om_family_season_bias_corrected | om family season bias corrected | macro_non_southerly | 1020 | 265 | 0.7716312378486748 | 39.509803921568626 | EXPERIMENT_ONLY |
| test | 2025 | om_family_season_bias_corrected | om family season bias corrected | macro_southerly_flow | 440 | 121 | 0.8096445074586308 | 48.40909090909091 | EXPERIMENT_ONLY |
| test | 2025 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_non_southerly | 1020 | 265 | 1.5557843137254903 | 11.07843137254902 | EXPERIMENT_ONLY |
| test | 2025 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_southerly_flow | 440 | 121 | 1.1143181818181818 | 25.227272727272727 | EXPERIMENT_ONLY |
| test | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1020 | 265 | 0.7538232557298766 | 42.05882352941177 | EXPERIMENT_ONLY |
| test | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 440 | 121 | 0.784403001110605 | 40.22727272727273 | EXPERIMENT_ONLY |
| validation | 2025 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1073 | 277 | 1.073900847129206 | 28.984156570363467 | EXPERIMENT_ONLY |
| validation | 2025 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 315 | 89 | 1.0175997694890186 | 28.888888888888886 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1073 | 277 | 1.3941732670557616 | 12.022367194780987 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 315 | 89 | 0.8234386171565224 | 30.158730158730158 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1073 | 277 | 1.456924510717614 | 11.276794035414724 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 315 | 89 | 0.8487619047619048 | 31.428571428571427 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_median_raw | om family median raw | macro_non_southerly | 1073 | 277 | 1.4797763280521903 | 12.022367194780987 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_median_raw | om family median raw | macro_southerly_flow | 315 | 89 | 0.9015873015873016 | 32.698412698412696 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1073 | 277 | 0.784241761366735 | 36.905871388630004 | EXPERIMENT_ONLY |
| validation | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 315 | 89 | 0.6671945327275027 | 52.06349206349207 | EXPERIMENT_ONLY |

## Defensive Selection Guardrail

| outer_test_year | validation_year | candidate_id | candidate_label | baseline_candidate_id | binary_macro_regime_label | candidate_non_southerly_mae | augmented_non_southerly_mae | non_southerly_mae_delta | candidate_non_southerly_exact_pct | augmented_non_southerly_exact_pct | non_southerly_exact_delta_pp | blocked_by_non_southerly_mae | blocked_by_non_southerly_exact | eligible_by_non_southerly_guard | selected_fallback_candidate_id | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | open_meteo_augmented_onda3f | macro_non_southerly | 1.3941732670557614 | 0.7977865351283904 | 0.596386731927371 | 12.022367194780987 | 38.11742777260019 | -26.0950605778192 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_mean_raw | om family mean raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.4569245107176143 | 0.7977865351283904 | 0.6591379755892239 | 11.276794035414724 | 38.11742777260019 | -26.840633737185463 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_median_raw | om family median raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.4797763280521903 | 0.7977865351283904 | 0.6819897929237999 | 12.022367194780987 | 38.11742777260019 | -26.0950605778192 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.784241761366735 | 0.7977865351283904 | -0.013544773761655415 | 36.905871388630004 | 38.11742777260019 | -1.2115563839701835 | False | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7148953091022056 | 0.7977865351283904 | -0.08289122602618482 | 41.47250698974837 | 38.11742777260019 | 3.3550792171481802 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7021921737216363 | 0.7977865351283904 | -0.09559436140675404 | 41.845293569431504 | 38.11742777260019 | 3.727865796831317 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7448229479555134 | 0.7977865351283904 | -0.05296358717287697 | 41.75209692451072 | 38.11742777260019 | 3.634669151910529 | False | False | True |  | EXPERIMENT_ONLY |
