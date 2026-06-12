# Open-Meteo Provider Calibration Report

Generated: 2026-06-11

production_status: EXPERIMENT_ONLY

This report builds family-deduplicated raw and bias-corrected provider candidates. It does not approve production use.

## Decision

| decision_status | decision_rationale | best_candidate_id | best_candidate_mae | n_candidate_rows | production_status |
| --- | --- | --- | --- | --- | --- |
| READY_FOR_CALIBRATED_OPEN_METEO_NESTED_VALIDATION | Raw and bias-corrected provider-family candidates were generated as experiment-only inputs for nested validation. | om_family_recent_bias_corrected | 0.8417836177120818 | 46672 | EXPERIMENT_ONLY |

## Candidate Metrics

| candidate_id | n_rows | n_dates | mae | rmse | signed_bias | exact_bracket_pct | mean_provider_families | mean_bias_adjustment | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| om_family_recent_bias_corrected | 5844 | 1461 | 0.8417836177120818 | 1.086734399204893 | -0.27268613906339995 | 37.713894592744694 | 3.6550308008213555 | 1.0009278239756145 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | 5844 | 1461 | 0.8735747462375755 | 1.1410970287371005 | -0.2417720152537676 | 38.19301848049281 | 3.6550308008213555 | 1.0318419477852467 | EXPERIMENT_ONLY |
| om_family_regime_bias_corrected | 5844 | 1461 | 0.9106600216416734 | 1.1551633107446442 | -0.5211171209434395 | 32.39219712525667 | 3.6550308008213555 | 0.7524968420955748 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | 5844 | 1461 | 0.9493447982099853 | 1.2199621199255481 | -0.4274686794701839 | 33.81245722108145 | 3.6550308008213555 | 0.8461452835688306 | EXPERIMENT_ONLY |
| om_family_inverse_mae_weighted | 5844 | 1461 | 1.3783937441889724 | 1.6418359721444633 | -1.210198842056862 | 16.01642710472279 | 3.6550308008213555 | 0.0 | EXPERIMENT_ONLY |
| om_gfs_previous_runs_raw | 5764 | 1441 | 1.4172796668979875 | 1.6716582665624429 | -1.1634281748785567 | 15.891741845940318 | 3.691880638445524 | 0.0 | EXPERIMENT_ONLY |
| om_family_mean_raw | 5844 | 1461 | 1.4200958247775497 | 1.683643987481846 | -1.2736139630390144 | 15.811088295687886 | 3.6550308008213555 | 0.0 | EXPERIMENT_ONLY |
| om_family_median_raw | 5844 | 1461 | 1.4364134154688568 | 1.697866761569078 | -1.2826146475017113 | 16.153319644079396 | 3.6550308008213555 | 0.0 | EXPERIMENT_ONLY |

## Candidate Coverage

| candidate_id | n_rows | n_dates | n_cps | min_provider_families | max_provider_families | min_date | max_date | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| om_family_inverse_mae_weighted | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_mean_raw | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_median_raw | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_recent_bias_corrected | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_regime_bias_corrected | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | 5844 | 1461 | 4 | 1 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |
| om_gfs_previous_runs_raw | 5764 | 1441 | 4 | 2 | 6 | 2022-01-01 | 2025-12-31 | EXPERIMENT_ONLY |

## Stabilized Calibration Support

| candidate_id | slice_type | slice_name | n_rows | mean_bias_samples | min_bias_samples | fallback_pct | mean_abs_bias_adjustment | support_warning | adjustment_warning | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_STABILIZED | overall | overall | 11688 | 362.53661875427787 | 0 | 9.308692676249144 | 0.9389936156770387 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | binary_macro_regime_label | macro_non_southerly | 4254 | 180.62717442407146 | 0 | 11.800658204043254 | 0.8514063320211125 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | binary_macro_regime_label | macro_southerly_flow | 1590 | 178.01006289308177 | 0 | 13.71069182389937 | 0.8320694973323476 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 20:00 | 1461 | 179.9151266255989 | 0 | 12.320328542094456 | 0.8461452835688305 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 21:00 | 1461 | 179.9151266255989 | 0 | 12.320328542094456 | 0.8461452835688305 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 22:00 | 1461 | 179.9151266255989 | 0 | 12.320328542094456 | 0.8461452835688305 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | cp | 23:00 | 1461 | 179.9151266255989 | 0 | 12.320328542094456 | 0.8461452835688305 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 01 | 496 | 184.0 | 0 | 12.096774193548388 | 0.9692314019803026 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 02 | 452 | 167.50442477876106 | 0 | 13.274336283185841 | 0.9509188442117654 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 03 | 496 | 183.0 | 0 | 12.096774193548388 | 0.8091760837934991 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 04 | 480 | 177.0 | 0 | 12.5 | 0.8473061816188839 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 05 | 496 | 183.0 | 0 | 12.096774193548388 | 0.742212822698409 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 06 | 480 | 177.0 | 0 | 12.5 | 0.6842463627040687 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 07 | 496 | 183.0 | 0 | 12.096774193548388 | 0.5726891424205262 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 08 | 496 | 183.0 | 0 | 12.096774193548388 | 0.6738452261937564 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 09 | 480 | 177.0 | 0 | 12.5 | 0.9352958558464448 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 10 | 496 | 183.0 | 0 | 12.096774193548388 | 0.9019655343648121 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 11 | 480 | 177.0 | 0 | 12.5 | 1.0307904320705583 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | month | 12 | 496 | 183.0 | 0 | 12.096774193548388 | 1.0490069662046393 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | DJF | 1444 | 178.49307479224376 | 0 | 12.465373961218837 | 0.9909013491713636 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | JJA | 1472 | 181.04347826086956 | 0 | 12.228260869565217 | 0.6431516990017917 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | MAM | 1472 | 181.04347826086956 | 0 | 12.228260869565217 | 0.7990461038023442 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | season | SON | 1456 | 179.04395604395606 | 0 | 12.362637362637363 | 0.9554232989320801 |  |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2022 | 1460 | 58.88219178082192 | 0 | 49.31506849315068 | 0.4129956292826624 | fallback_pct_gt_40 |  | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2023 | 1460 | 180.64657534246575 | 112 | 0.0 | 1.002137738786644 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2024 | 1464 | 240.13114754098362 | 224 | 0.0 | 1.015540234716021 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_month_bias_corrected | year | 2025 | 1460 | 239.83561643835617 | 224 | 0.0 | 0.9534434357334274 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | binary_macro_regime_label | macro_non_southerly | 4254 | 551.8993888105313 | 0 | 6.0413728255759285 | 1.0411661667456824 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | binary_macro_regime_label | macro_southerly_flow | 1590 | 527.1220125786164 | 0 | 6.981132075471698 | 1.0068952638495905 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 20:00 | 1461 | 545.1581108829569 | 0 | 6.297056810403833 | 1.0318419477852467 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 21:00 | 1461 | 545.1581108829569 | 0 | 6.297056810403833 | 1.0318419477852467 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 22:00 | 1461 | 545.1581108829569 | 0 | 6.297056810403833 | 1.0318419477852467 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | cp | 23:00 | 1461 | 545.1581108829569 | 0 | 6.297056810403833 | 1.0318419477852467 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 01 | 496 | 480.0 | 0 | 18.548387096774192 | 0.9966033377299596 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 02 | 452 | 540.6017699115044 | 124 | 0.0 | 1.2251985294700496 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 03 | 496 | 488.0 | 0 | 18.548387096774192 | 0.8880747340904224 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 04 | 480 | 549.0 | 124 | 0.0 | 1.0424694706901383 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 05 | 496 | 610.0 | 244 | 0.0 | 1.0886290310739353 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 06 | 480 | 487.0 | 0 | 19.166666666666668 | 0.7295438411769734 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 07 | 496 | 548.0 | 120 | 0.0 | 0.8801591411935473 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 08 | 496 | 610.0 | 244 | 0.0 | 0.8686477716480968 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 09 | 480 | 482.0 | 0 | 19.166666666666668 | 0.9920663969254978 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 10 | 496 | 543.0 | 120 | 0.0 | 1.2032611665478732 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 11 | 480 | 604.0 | 244 | 0.0 | 1.2344688578429095 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | month | 12 | 496 | 598.0 | 236 | 0.0 | 1.245978236166711 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | DJF | 1444 | 539.5013850415512 | 0 | 6.371191135734072 | 1.1538159251892044 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | JJA | 1472 | 549.0 | 0 | 6.25 | 0.8271666253630453 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | MAM | 1472 | 549.0 | 0 | 6.25 | 1.0059989221826005 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | season | SON | 1456 | 543.0 | 0 | 6.318681318681318 | 1.1439247670992998 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2022 | 1460 | 180.5150684931507 | 0 | 25.205479452054796 | 0.7549060779567545 |  |  | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2023 | 1460 | 545.5452054794521 | 360 | 0.0 | 1.1603620455294195 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2024 | 1464 | 727.0273224043716 | 720 | 0.0 | 1.1399100292542914 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
| om_family_season_bias_corrected | year | 2025 | 1460 | 727.0465753424658 | 720 | 0.0 | 1.07189356146499 |  | mean_abs_bias_adjustment_gt_1 | EXPERIMENT_ONLY |
