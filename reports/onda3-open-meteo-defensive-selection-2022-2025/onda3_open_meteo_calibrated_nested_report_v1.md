# Onda 3 Open-Meteo Calibrated Nested Validation Report

Generated: 2026-06-11

production_status: EXPERIMENT_ONLY

Calibrated Open-Meteo candidates are compared against local-only Onda 3F and raw GFS Previous Runs on identical covered rows.

## Decision

| decision_status | decision_rationale | n_outer_folds | selected_mean_test_mae | always_local_mean_test_mae | always_open_meteo_augmented_mean_test_mae | always_gfs_previous_runs_mean_test_mae | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PROMOTE_CALIBRATED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION | Calibrated Open-Meteo was selected in enough outer folds. | 2 | 0.7823964601524304 | 1.0573963635616603 | 0.8243513522952353 | 1.426499546010817 | EXPERIMENT_ONLY |

## Candidate Scope

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | train_start | train_end | train_start_year | train_end_year | evaluation_start | evaluation_end | n_train_rows | n_rows | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 2024 | 2023 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_mean_raw | om family mean raw | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_median_raw | om family median raw | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| validation | 2024 | 2023 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 | 2022-12-31 | 2012 | 2022 | 2023-01-01 | 2023-12-31 | 1460 | 1456 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_mean_raw | om family mean raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_median_raw | om family median raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| test | 2024 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | local_only_onda3f | Local-only Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_mean_raw | om family mean raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_median_raw | om family median raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |
| validation | 2025 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 2012-01-01 | 2023-12-30 | 2012 | 2023 | 2024-01-01 | 2024-12-31 | 2916 | 1388 | EXPERIMENT_ONLY |

## Selection

| outer_test_year | validation_year | selected_candidate_id | selected_candidate_label | selected_validation_mae | selected_validation_any_cp_exact_pct | selected_validation_cp23_exact_pct | selected_test_mae | selected_test_any_cp_exact_pct | selected_test_cp23_exact_pct | validation_candidate_count | test_candidate_count | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | 2023 | om_family_season_bias_corrected | om family season bias corrected | 0.8407124877245218 | 38.18681318681318 | 38.18681318681318 | 0.7389864058451955 | 42.65129682997118 | 42.65129682997118 | 10 | 10 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 0.7166820365033622 | 42.363112391930834 | 42.363112391930834 | 0.8258065144596652 | 38.63013698630137 | 38.63013698630137 | 10 | 10 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |

## Selected Test Summary

| outer_test_year | evaluation_year | candidate_id | candidate_label | mae | any_cp_exact_pct | cp23_exact_pct | n_days_with_cp23 | cp23_exact_days | n_days | n_cp_rows | selection_rule | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 0.7389864058451955 | 42.65129682997118 | 42.65129682997118 | 347 | 148 | 347 | 1388 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |
| 2025 | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | 0.8258065144596652 | 38.63013698630137 | 38.63013698630137 | 365 | 141 | 365 | 1460 | validation_mae_then_non_southerly_guard_then_cp23 | EXPERIMENT_ONLY |

## Candidate Metrics

| stage | outer_test_year | evaluation_year | candidate_id | candidate_label | n_days | n_cp_rows | mae | any_cp_exact_pct | n_days_with_cp23 | cp23_exact_days | cp23_exact_pct | production_status | cp_2000_exact_pct | cp_2100_exact_pct | cp_2200_exact_pct | cp_2300_exact_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | 2024 | local_only_onda3f | Local-only Onda 3F | 347 | 1388 | 1.0577107916122577 | 43.51585014409222 | 347 | 94 | 27.089337175792505 | EXPERIMENT_ONLY | 29.106628242074926 | 30.547550432276655 | 27.6657060518732 | 27.089337175792505 |
| test | 2024 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 347 | 1388 | 1.264647752129061 | 16.138328530259365 | 347 | 56 | 16.138328530259365 | EXPERIMENT_ONLY | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 |
| test | 2024 | 2024 | om_family_mean_raw | om family mean raw | 347 | 1388 | 1.3189048991354466 | 15.85014409221902 | 347 | 55 | 15.85014409221902 | EXPERIMENT_ONLY | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 |
| test | 2024 | 2024 | om_family_median_raw | om family median raw | 347 | 1388 | 1.3485590778097982 | 16.714697406340058 | 347 | 58 | 16.714697406340058 | EXPERIMENT_ONLY | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 |
| test | 2024 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 347 | 1388 | 0.7506991616421218 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| test | 2024 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 347 | 1388 | 0.7166820365033622 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| test | 2024 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 347 | 1388 | 0.7354554772358184 | 41.4985590778098 | 347 | 139 | 40.05763688760807 | EXPERIMENT_ONLY | 39.19308357348703 | 39.19308357348703 | 39.481268011527376 | 40.05763688760807 |
| test | 2024 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 347 | 1388 | 0.7389864058451955 | 42.65129682997118 | 347 | 148 | 42.65129682997118 | EXPERIMENT_ONLY | 42.65129682997118 | 42.65129682997118 | 42.65129682997118 | 42.65129682997118 |
| test | 2024 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 347 | 1388 | 1.4302593659942364 | 13.8328530259366 | 347 | 48 | 13.8328530259366 | EXPERIMENT_ONLY | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 |
| test | 2024 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 347 | 1388 | 0.8419277395321766 | 56.48414985590778 | 347 | 135 | 38.90489913544668 | EXPERIMENT_ONLY | 34.293948126801155 | 36.023054755043226 | 39.19308357348703 | 38.90489913544668 |
| validation | 2024 | 2023 | local_only_onda3f | Local-only Onda 3F | 364 | 1456 | 1.0576790939996112 | 47.527472527472526 | 364 | 121 | 33.24175824175824 | EXPERIMENT_ONLY | 28.846153846153843 | 32.967032967032964 | 33.24175824175824 | 33.24175824175824 |
| validation | 2024 | 2023 | om_family_inverse_mae_weighted | om family inverse mae weighted | 364 | 1456 | 1.4195240456354083 | 15.659340659340659 | 364 | 57 | 15.659340659340659 | EXPERIMENT_ONLY | 15.659340659340659 | 15.659340659340659 | 15.659340659340659 | 15.659340659340659 |
| validation | 2024 | 2023 | om_family_mean_raw | om family mean raw | 364 | 1456 | 1.4358516483516486 | 15.934065934065933 | 364 | 58 | 15.934065934065933 | EXPERIMENT_ONLY | 15.934065934065933 | 15.934065934065933 | 15.934065934065933 | 15.934065934065933 |
| validation | 2024 | 2023 | om_family_median_raw | om family median raw | 364 | 1456 | 1.4358516483516486 | 15.934065934065933 | 364 | 58 | 15.934065934065933 | EXPERIMENT_ONLY | 15.934065934065933 | 15.934065934065933 | 15.934065934065933 | 15.934065934065933 |
| validation | 2024 | 2023 | om_family_month_bias_corrected | om family month bias corrected | 364 | 1456 | 0.8833797378296946 | 33.791208791208796 | 364 | 123 | 33.791208791208796 | EXPERIMENT_ONLY | 33.791208791208796 | 33.791208791208796 | 33.791208791208796 | 33.791208791208796 |
| validation | 2024 | 2023 | om_family_recent_bias_corrected | om family recent bias corrected | 364 | 1456 | 0.8579505494505494 | 35.43956043956044 | 364 | 129 | 35.43956043956044 | EXPERIMENT_ONLY | 35.43956043956044 | 35.43956043956044 | 35.43956043956044 | 35.43956043956044 |
| validation | 2024 | 2023 | om_family_regime_bias_corrected | om family regime bias corrected | 364 | 1456 | 0.9688960493372167 | 30.21978021978022 | 364 | 103 | 28.296703296703296 | EXPERIMENT_ONLY | 29.120879120879124 | 28.846153846153843 | 28.021978021978022 | 28.296703296703296 |
| validation | 2024 | 2023 | om_family_season_bias_corrected | om family season bias corrected | 364 | 1456 | 0.8407124877245218 | 38.18681318681318 | 364 | 139 | 38.18681318681318 | EXPERIMENT_ONLY | 38.18681318681318 | 38.18681318681318 | 38.18681318681318 | 38.18681318681318 |
| validation | 2024 | 2023 | om_gfs_previous_runs_raw | om gfs previous runs raw | 364 | 1456 | 1.4096153846153847 | 16.483516483516482 | 364 | 60 | 16.483516483516482 | EXPERIMENT_ONLY | 16.483516483516482 | 16.483516483516482 | 16.483516483516482 | 16.483516483516482 |
| validation | 2024 | 2023 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 364 | 1456 | 0.9137936866946796 | 55.494505494505496 | 364 | 129 | 35.43956043956044 | EXPERIMENT_ONLY | 34.065934065934066 | 35.989010989010985 | 32.967032967032964 | 35.43956043956044 |
| test | 2025 | 2025 | local_only_onda3f | Local-only Onda 3F | 365 | 1460 | 1.057081935511063 | 45.47945205479452 | 365 | 117 | 32.054794520547944 | EXPERIMENT_ONLY | 27.397260273972602 | 30.958904109589042 | 33.97260273972603 | 32.054794520547944 |
| test | 2025 | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | 365 | 1460 | 1.2107920403666472 | 19.726027397260275 | 365 | 72 | 19.726027397260275 | EXPERIMENT_ONLY | 19.726027397260275 | 19.726027397260275 | 19.726027397260275 | 19.726027397260275 |
| test | 2025 | 2025 | om_family_mean_raw | om family mean raw | 365 | 1460 | 1.292876712328767 | 17.80821917808219 | 365 | 65 | 17.80821917808219 | EXPERIMENT_ONLY | 17.80821917808219 | 17.80821917808219 | 17.80821917808219 | 17.80821917808219 |
| test | 2025 | 2025 | om_family_median_raw | om family median raw | 365 | 1460 | 1.33 | 18.356164383561644 | 365 | 67 | 18.356164383561644 | EXPERIMENT_ONLY | 18.356164383561644 | 18.356164383561644 | 18.356164383561644 | 18.356164383561644 |
| test | 2025 | 2025 | om_family_month_bias_corrected | om family month bias corrected | 365 | 1460 | 0.8177262522176716 | 38.63013698630137 | 365 | 141 | 38.63013698630137 | EXPERIMENT_ONLY | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 |
| test | 2025 | 2025 | om_family_recent_bias_corrected | om family recent bias corrected | 365 | 1460 | 0.8258065144596652 | 38.63013698630137 | 365 | 141 | 38.63013698630137 | EXPERIMENT_ONLY | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 | 38.63013698630137 |
| test | 2025 | 2025 | om_family_regime_bias_corrected | om family regime bias corrected | 365 | 1460 | 0.8573018487151092 | 34.794520547945204 | 365 | 122 | 33.42465753424658 | EXPERIMENT_ONLY | 33.42465753424658 | 33.15068493150685 | 32.87671232876712 | 33.42465753424658 |
| test | 2025 | 2025 | om_family_season_bias_corrected | om family season bias corrected | 365 | 1460 | 0.7830872917037301 | 42.19178082191781 | 365 | 154 | 42.19178082191781 | EXPERIMENT_ONLY | 42.19178082191781 | 42.19178082191781 | 42.19178082191781 | 42.19178082191781 |
| test | 2025 | 2025 | om_gfs_previous_runs_raw | om gfs previous runs raw | 365 | 1460 | 1.4227397260273975 | 15.342465753424658 | 365 | 56 | 15.342465753424658 | EXPERIMENT_ONLY | 15.342465753424658 | 15.342465753424658 | 15.342465753424658 | 15.342465753424658 |
| test | 2025 | 2025 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 365 | 1460 | 0.806774965058294 | 61.917808219178085 | 365 | 154 | 42.19178082191781 | EXPERIMENT_ONLY | 40.54794520547945 | 43.013698630136986 | 39.726027397260275 | 42.19178082191781 |
| validation | 2025 | 2024 | local_only_onda3f | Local-only Onda 3F | 347 | 1388 | 1.0577107916122577 | 43.51585014409222 | 347 | 94 | 27.089337175792505 | EXPERIMENT_ONLY | 29.106628242074926 | 30.547550432276655 | 27.6657060518732 | 27.089337175792505 |
| validation | 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | 347 | 1388 | 1.264647752129061 | 16.138328530259365 | 347 | 56 | 16.138328530259365 | EXPERIMENT_ONLY | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 | 16.138328530259365 |
| validation | 2025 | 2024 | om_family_mean_raw | om family mean raw | 347 | 1388 | 1.3189048991354466 | 15.85014409221902 | 347 | 55 | 15.85014409221902 | EXPERIMENT_ONLY | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 | 15.85014409221902 |
| validation | 2025 | 2024 | om_family_median_raw | om family median raw | 347 | 1388 | 1.3485590778097982 | 16.714697406340058 | 347 | 58 | 16.714697406340058 | EXPERIMENT_ONLY | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 | 16.714697406340058 |
| validation | 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | 347 | 1388 | 0.7506991616421218 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| validation | 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | 347 | 1388 | 0.7166820365033622 | 42.363112391930834 | 347 | 147 | 42.363112391930834 | EXPERIMENT_ONLY | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 | 42.363112391930834 |
| validation | 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | 347 | 1388 | 0.7354554772358184 | 41.4985590778098 | 347 | 139 | 40.05763688760807 | EXPERIMENT_ONLY | 39.19308357348703 | 39.19308357348703 | 39.481268011527376 | 40.05763688760807 |
| validation | 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | 347 | 1388 | 0.7389864058451955 | 42.65129682997118 | 347 | 148 | 42.65129682997118 | EXPERIMENT_ONLY | 42.65129682997118 | 42.65129682997118 | 42.65129682997118 | 42.65129682997118 |
| validation | 2025 | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | 347 | 1388 | 1.4302593659942364 | 13.8328530259366 | 347 | 48 | 13.8328530259366 | EXPERIMENT_ONLY | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 | 13.8328530259366 |
| validation | 2025 | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | 347 | 1388 | 0.8419277395321766 | 56.48414985590778 | 347 | 135 | 38.90489913544668 | EXPERIMENT_ONLY | 34.293948126801155 | 36.023054755043226 | 39.19308357348703 | 38.90489913544668 |

## Regime Performance

| stage | outer_test_year | candidate_id | candidate_label | binary_macro_regime_label | n_cp_rows | n_unique_dates | mae | exact_bracket_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1073 | 277 | 1.072716117661352 | 28.611369990680334 | EXPERIMENT_ONLY |
| test | 2024 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 315 | 89 | 1.0065974111339147 | 28.57142857142857 | EXPERIMENT_ONLY |
| test | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1073 | 277 | 1.3941732670557616 | 12.022367194780987 | EXPERIMENT_ONLY |
| test | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 315 | 89 | 0.8234386171565224 | 30.158730158730158 | EXPERIMENT_ONLY |
| test | 2024 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1073 | 277 | 1.456924510717614 | 11.276794035414724 | EXPERIMENT_ONLY |
| test | 2024 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 315 | 89 | 0.8487619047619048 | 31.428571428571427 | EXPERIMENT_ONLY |
| test | 2024 | om_family_median_raw | om family median raw | macro_non_southerly | 1073 | 277 | 1.4797763280521903 | 12.022367194780987 | EXPERIMENT_ONLY |
| test | 2024 | om_family_median_raw | om family median raw | macro_southerly_flow | 315 | 89 | 0.9015873015873016 | 32.698412698412696 | EXPERIMENT_ONLY |
| test | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1073 | 277 | 0.7675159776613358 | 39.235787511649576 | EXPERIMENT_ONLY |
| test | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 315 | 89 | 0.6934152137417519 | 53.01587301587302 | EXPERIMENT_ONLY |
| test | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_non_southerly | 1073 | 277 | 0.7148953091022056 | 41.47250698974837 | EXPERIMENT_ONLY |
| test | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_southerly_flow | 315 | 89 | 0.7227682539682541 | 45.3968253968254 | EXPERIMENT_ONLY |
| test | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_non_southerly | 1073 | 277 | 0.7021921737216364 | 41.845293569431504 | EXPERIMENT_ONLY |
| test | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_southerly_flow | 315 | 89 | 0.8487619047619048 | 31.428571428571427 | EXPERIMENT_ONLY |
| test | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_non_southerly | 1073 | 277 | 0.7394531992807855 | 42.124883504193846 | EXPERIMENT_ONLY |
| test | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_southerly_flow | 315 | 89 | 0.7373963443963443 | 44.44444444444444 | EXPERIMENT_ONLY |
| test | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_non_southerly | 1073 | 277 | 1.5843429636533084 | 7.921714818266542 | EXPERIMENT_ONLY |
| test | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_southerly_flow | 315 | 89 | 0.9053968253968253 | 33.96825396825397 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1073 | 277 | 0.8745893662017227 | 34.01677539608574 | EXPERIMENT_ONLY |
| test | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 315 | 89 | 0.7306708334482941 | 47.61904761904761 | EXPERIMENT_ONLY |
| validation | 2024 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1069 | 275 | 1.0540698840699976 | 31.898971000935454 | EXPERIMENT_ONLY |
| validation | 2024 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 387 | 104 | 1.0676487203943323 | 32.55813953488372 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1069 | 275 | 1.5556265011387942 | 13.657623947614594 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 387 | 104 | 1.0435717848263142 | 21.188630490956072 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1069 | 275 | 1.5728250701590272 | 13.283442469597755 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 387 | 104 | 1.0574935400516794 | 23.25581395348837 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_median_raw | om family median raw | macro_non_southerly | 1069 | 275 | 1.5728250701590272 | 13.283442469597755 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_median_raw | om family median raw | macro_southerly_flow | 387 | 104 | 1.0574935400516794 | 23.25581395348837 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1069 | 275 | 0.935563154905051 | 31.15060804490178 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 387 | 104 | 0.7392348467352344 | 41.08527131782946 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_non_southerly | 1069 | 275 | 0.9094786404739632 | 31.898971000935454 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | macro_southerly_flow | 387 | 104 | 0.7156158484065459 | 45.21963824289406 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_non_southerly | 1069 | 275 | 0.9342507539522008 | 30.495790458372312 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | macro_southerly_flow | 387 | 104 | 1.0645958445997028 | 23.25581395348837 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_non_southerly | 1069 | 275 | 0.8830047091602238 | 35.07951356407858 | EXPERIMENT_ONLY |
| validation | 2024 | om_family_season_bias_corrected | om family season bias corrected | macro_southerly_flow | 387 | 104 | 0.7238897882031646 | 46.770025839793284 | EXPERIMENT_ONLY |
| validation | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_non_southerly | 1069 | 275 | 1.5362956033676332 | 13.84471468662301 | EXPERIMENT_ONLY |
| validation | 2024 | om_gfs_previous_runs_raw | om gfs previous runs raw | macro_southerly_flow | 387 | 104 | 1.05968992248062 | 23.772609819121445 | EXPERIMENT_ONLY |
| validation | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_non_southerly | 1069 | 275 | 0.9316782228377584 | 33.86342376052385 | EXPERIMENT_ONLY |
| validation | 2024 | open_meteo_augmented_onda3f | Open-Meteo augmented Onda 3F | macro_southerly_flow | 387 | 104 | 0.8643916992606975 | 36.69250645994832 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_non_southerly | 1020 | 265 | 1.080155517407174 | 31.56862745098039 | EXPERIMENT_ONLY |
| test | 2025 | local_only_onda3f | Local-only Onda 3F | macro_southerly_flow | 440 | 121 | 1.0035931774791682 | 30.0 | EXPERIMENT_ONLY |
| test | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_non_southerly | 1020 | 265 | 1.358597299557055 | 15.588235294117647 | EXPERIMENT_ONLY |
| test | 2025 | om_family_inverse_mae_weighted | om family inverse mae weighted | macro_southerly_flow | 440 | 121 | 0.8681525758797929 | 29.318181818181817 | EXPERIMENT_ONLY |
| test | 2025 | om_family_mean_raw | om family mean raw | macro_non_southerly | 1020 | 265 | 1.4668039215686273 | 14.215686274509803 | EXPERIMENT_ONLY |
| test | 2025 | om_family_mean_raw | om family mean raw | macro_southerly_flow | 440 | 121 | 0.8896818181818181 | 26.136363636363637 | EXPERIMENT_ONLY |
| test | 2025 | om_family_median_raw | om family median raw | macro_non_southerly | 1020 | 265 | 1.5170588235294118 | 12.84313725490196 | EXPERIMENT_ONLY |
| test | 2025 | om_family_median_raw | om family median raw | macro_southerly_flow | 440 | 121 | 0.8963636363636364 | 31.136363636363633 | EXPERIMENT_ONLY |
| test | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_non_southerly | 1020 | 265 | 0.8288526261839391 | 34.80392156862745 | EXPERIMENT_ONLY |
| test | 2025 | om_family_month_bias_corrected | om family month bias corrected | macro_southerly_flow | 440 | 121 | 0.7919332943867784 | 47.5 | EXPERIMENT_ONLY |

## Defensive Selection Guardrail

| outer_test_year | validation_year | candidate_id | candidate_label | baseline_candidate_id | binary_macro_regime_label | candidate_non_southerly_mae | augmented_non_southerly_mae | non_southerly_mae_delta | candidate_non_southerly_exact_pct | augmented_non_southerly_exact_pct | non_southerly_exact_delta_pp | blocked_by_non_southerly_mae | blocked_by_non_southerly_exact | eligible_by_non_southerly_guard | selected_fallback_candidate_id | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | 2023 | om_family_inverse_mae_weighted | om family inverse mae weighted | open_meteo_augmented_onda3f | macro_non_southerly | 1.5556265011387942 | 0.9316782228377584 | 0.6239482783010358 | 13.657623947614594 | 33.86342376052385 | -20.205799812909255 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_mean_raw | om family mean raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.5728250701590272 | 0.9316782228377584 | 0.6411468473212688 | 13.283442469597755 | 33.86342376052385 | -20.579981290926096 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_median_raw | om family median raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.5728250701590272 | 0.9316782228377584 | 0.6411468473212688 | 13.283442469597755 | 33.86342376052385 | -20.579981290926096 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_month_bias_corrected | om family month bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.935563154905051 | 0.9316782228377584 | 0.003884932067292679 | 31.15060804490178 | 33.86342376052385 | -2.712815715622071 | False | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_recent_bias_corrected | om family recent bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.9094786404739631 | 0.9316782228377584 | -0.022199582363795267 | 31.898971000935454 | 33.86342376052385 | -1.9644527595883972 | False | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_regime_bias_corrected | om family regime bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.9342507539522007 | 0.9316782228377584 | 0.0025725311144423335 | 30.495790458372312 | 33.86342376052385 | -3.367633302151539 | False | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2024 | 2023 | om_family_season_bias_corrected | om family season bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.8830047091602238 | 0.9316782228377584 | -0.048673513677534586 | 35.07951356407858 | 33.86342376052385 | 1.2160898035547305 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_inverse_mae_weighted | om family inverse mae weighted | open_meteo_augmented_onda3f | macro_non_southerly | 1.3941732670557614 | 0.8745893662017227 | 0.5195839008540387 | 12.022367194780987 | 34.01677539608574 | -21.994408201304754 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_mean_raw | om family mean raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.4569245107176143 | 0.8745893662017227 | 0.5823351445158916 | 11.276794035414724 | 34.01677539608574 | -22.739981360671017 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_median_raw | om family median raw | open_meteo_augmented_onda3f | macro_non_southerly | 1.47977632805219 | 0.8745893662017227 | 0.6051869618504674 | 12.022367194780987 | 34.01677539608574 | -21.994408201304754 | True | True | False | open_meteo_augmented_onda3f | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_month_bias_corrected | om family month bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7675159776613358 | 0.8745893662017227 | -0.10707338854038684 | 39.235787511649576 | 34.01677539608574 | 5.219012115563835 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_recent_bias_corrected | om family recent bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7148953091022056 | 0.8745893662017227 | -0.15969405709951712 | 41.47250698974837 | 34.01677539608574 | 7.455731593662627 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_regime_bias_corrected | om family regime bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7021921737216363 | 0.8745893662017227 | -0.17239719248008634 | 41.845293569431504 | 34.01677539608574 | 7.828518173345763 | False | False | True |  | EXPERIMENT_ONLY |
| 2025 | 2024 | om_family_season_bias_corrected | om family season bias corrected | open_meteo_augmented_onda3f | macro_non_southerly | 0.7394531992807853 | 0.8745893662017227 | -0.13513616692093733 | 42.124883504193846 | 34.01677539608574 | 8.108108108108105 | False | False | True |  | EXPERIMENT_ONLY |
