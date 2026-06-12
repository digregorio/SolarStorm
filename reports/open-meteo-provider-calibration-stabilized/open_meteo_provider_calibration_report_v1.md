# Open-Meteo Provider Calibration Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

This report builds family-deduplicated raw and bias-corrected provider candidates. It does not approve production use.

## Decision

| decision_status | decision_rationale | best_candidate_id | best_candidate_mae | n_candidate_rows | production_status |
| --- | --- | --- | --- | --- | --- |
| READY_FOR_CALIBRATED_OPEN_METEO_NESTED_VALIDATION | Raw and bias-corrected provider-family candidates were generated as experiment-only inputs for nested validation. | om_family_recent_bias_corrected | 0.8225165258605939 | 34992 | EXPERIMENT_ONLY |

## Candidate Metrics

| candidate_id | n_rows | n_dates | mae | rmse | signed_bias | exact_bracket_pct | mean_provider_families | mean_bias_adjustment | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| om_family_recent_bias_corrected | 4384 | 1096 | 0.8225165258605939 | 1.0619027203348386 | -0.27411731542287404 | 38.41240875912409 | 4.206204379562044 | 0.9693133415114326 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | 4384 | 1096 | 0.8791105986863216 | 1.150300541776646 | -0.27259745912882055 | 37.95620437956204 | 4.206204379562044 | 0.970833197805486 | EXPERIMENT_ONLY |
| om_family_regime_bias_corrected | 4384 | 1096 | 0.8849793382677764 | 1.1274341328346977 | -0.49828402327437377 | 33.325729927007295 | 4.206204379562044 | 0.7451466336599328 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | 4384 | 1096 | 0.9620203757670119 | 1.2355292390680468 | -0.4774483384329758 | 32.66423357664234 | 4.206204379562044 | 0.7659823185013307 | EXPERIMENT_ONLY |
| om_family_inverse_mae_weighted | 4384 | 1096 | 1.3409438699920169 | 1.6086745749866012 | -1.1727877938690325 | 16.87956204379562 | 4.206204379562044 | 0.0 | EXPERIMENT_ONLY |
| om_family_mean_raw | 4384 | 1096 | 1.3897901459854014 | 1.6583141802804011 | -1.2434306569343065 | 16.33211678832117 | 4.206204379562044 | 0.0 | EXPERIMENT_ONLY |
| om_family_median_raw | 4384 | 1096 | 1.4115419708029198 | 1.6775330829898847 | -1.2554288321167884 | 16.78832116788321 | 4.206204379562044 | 0.0 | EXPERIMENT_ONLY |
| om_gfs_previous_runs_raw | 4304 | 1076 | 1.420724907063197 | 1.6684169867379341 | -1.2017657992565054 | 15.241635687732341 | 4.265799256505576 | 0.0 | EXPERIMENT_ONLY |

## Candidate Coverage

| candidate_id | n_rows | n_dates | n_cps | min_provider_families | max_provider_families | min_date | max_date | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| om_family_inverse_mae_weighted | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_mean_raw | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_median_raw | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_recent_bias_corrected | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_regime_bias_corrected | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | 4384 | 1096 | 4 | 1 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_gfs_previous_runs_raw | 4304 | 1076 | 4 | 2 | 6 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |

## Stabilized Calibration Support

| candidate_id | slice_type | slice_name | n_rows | mean_bias_samples | min_bias_samples | fallback_pct | mean_abs_bias_adjustment | support_warning | adjustment_warning | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_STABILIZED | overall | overall | 8768 | 322.2153284671533 | 0 | 12.408759124087592 | 0.8684077581534084 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | binary_macro_regime_label | macro_non_southerly | 3225 | 158.2337984496124 | 0 | 16.868217054263567 | 0.7600699666087833 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | binary_macro_regime_label | macro_southerly_flow | 1159 | 164.33477135461604 | 0 | 15.185504745470233 | 0.7824338584956927 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 20:00 | 1096 | 159.84671532846716 | 0 | 16.423357664233578 | 0.7659823185013308 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 21:00 | 1096 | 159.84671532846716 | 0 | 16.423357664233578 | 0.7659823185013308 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 22:00 | 1096 | 159.84671532846716 | 0 | 16.423357664233578 | 0.7659823185013308 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 23:00 | 1096 | 159.84671532846716 | 0 | 16.423357664233578 | 0.7659823185013308 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 01 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.9029000458289942 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 02 | 340 | 148.89411764705883 | 0 | 17.647058823529413 | 0.8585548931188957 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 03 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.9719629155793623 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 04 | 360 | 157.33333333333334 | 0 | 16.666666666666668 | 0.7047794620658133 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 05 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.5448560656576672 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 06 | 360 | 157.33333333333334 | 0 | 16.666666666666668 | 0.5153043942131817 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 07 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.4551568120224819 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 08 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.5710259974503841 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 09 | 360 | 157.33333333333334 | 0 | 16.666666666666668 | 0.8519737283187857 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 10 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 0.8160016254887356 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 11 | 360 | 157.33333333333334 | 0 | 16.666666666666668 | 0.979144812544872 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 12 | 372 | 162.66666666666666 | 0 | 16.129032258064516 | 1.0276797575370378 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | DJF | 1084 | 158.3468634686347 | 0 | 16.605166051660518 | 0.9318121314691774 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | JJA | 1104 | 160.92753623188406 | 0 | 16.304347826086957 | 0.5138130317397206 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | MAM | 1104 | 160.92753623188406 | 0 | 16.304347826086957 | 0.7409214378295903 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | SON | 1092 | 159.15018315018315 | 0 | 16.483516483516482 | 0.8816440287479179 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2023 | 1460 | 58.88219178082192 | 0 | 49.31506849315068 | 0.3948641647723177 | fallback_pct_gt_40 |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2024 | 1464 | 180.76502732240436 | 112 | 0.0 | 0.9491375598165617 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2025 | 1460 | 239.83561643835617 | 224 | 0.0 | 0.9534434357334274 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | binary_macro_regime_label | macro_non_southerly | 3225 | 482.97922480620156 | 0 | 7.9689922480620154 | 0.9796823266415243 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | binary_macro_regime_label | macro_southerly_flow | 1159 | 489.04918032786884 | 0 | 9.577221742881795 | 0.946209866920047 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 20:00 | 1096 | 484.5839416058394 | 0 | 8.394160583941606 | 0.970833197805486 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 21:00 | 1096 | 484.5839416058394 | 0 | 8.394160583941606 | 0.970833197805486 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 22:00 | 1096 | 484.5839416058394 | 0 | 8.394160583941606 | 0.970833197805486 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 23:00 | 1096 | 484.5839416058394 | 0 | 8.394160583941606 | 0.970833197805486 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 01 | 372 | 400.0 | 0 | 24.731182795698924 | 0.8957030339112365 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 02 | 340 | 480.0470588235294 | 124 | 0.0 | 1.131010296596608 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 03 | 372 | 406.6666666666667 | 0 | 24.731182795698924 | 0.8380374788572433 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 04 | 360 | 488.0 | 124 | 0.0 | 1.124992460806177 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 05 | 372 | 569.3333333333334 | 244 | 0.0 | 1.0960911917202492 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 06 | 360 | 405.3333333333333 | 0 | 25.555555555555557 | 0.5695086901293395 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 07 | 372 | 486.6666666666667 | 120 | 0.0 | 0.7271536233028719 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 08 | 372 | 569.3333333333334 | 244 | 0.0 | 0.7397778230329245 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 09 | 360 | 401.3333333333333 | 0 | 25.555555555555557 | 0.9133485181195269 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 10 | 372 | 482.6666666666667 | 120 | 0.0 | 1.2044673653311326 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 11 | 360 | 564.0 | 244 | 0.0 | 1.2314660722179518 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 12 | 372 | 558.6666666666666 | 236 | 0.0 | 1.1908005899683352 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | DJF | 1084 | 479.55719557195573 | 0 | 8.487084870848708 | 1.0707775359096379 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | JJA | 1104 | 488.0 | 0 | 8.333333333333334 | 0.6800014732640204 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | MAM | 1104 | 488.0 | 0 | 8.333333333333334 | 1.0185626370879086 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | SON | 1092 | 482.6666666666667 | 0 | 8.424908424908425 | 1.1173947915976867 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2023 | 1460 | 180.5150684931507 | 0 | 25.205479452054796 | 0.7344578483685804 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2024 | 1464 | 546.0218579234972 | 360 | 0.0 | 1.105778470506993 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2025 | 1460 | 727.0465753424658 | 720 | 0.0 | 1.07189356146499 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
