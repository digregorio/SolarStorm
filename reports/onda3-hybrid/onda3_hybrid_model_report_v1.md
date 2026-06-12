# Onda 3 P1 Horizon Hybrid Model Report

Generated: 2026-06-12

All outputs remain EXPERIMENT_ONLY.

No production, EV, pricing, shadow trading, or execution work is unlocked.

## Decision

| decision_status | decision_rationale | om_same_row_mae | reference_same_row_mae | om_beats_reference_same_row | production_status |
| --- | --- | --- | --- | --- | --- |
| READY_FOR_P2_DISTRIBUTION_DESIGN | P1 hybrid candidates judged by P0 honest gates plus the pre-registered same-row MAE comparison against hybrid_local_only_covered_rows (spec success criterion 2). | 0.726 | 0.951 | true | EXPERIMENT_ONLY |

## Honest Gates per Candidate

| gate_id | gate_name | gate_status | gate_detail | production_status | model_name |
| --- | --- | --- | --- | --- | --- |
| H1 | Per-CP honest lift | PASS | model MAE is below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_local_only |
| H2 | Anticipation stratum | BLOCK | model does not beat honest null on every supported CP | EXPERIMENT_ONLY | hybrid_local_only |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_local_only |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_local_only |
| H1 | Per-CP honest lift | BLOCK | model MAE is not below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H2 | Anticipation stratum | BLOCK | model does not beat honest null on every supported CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H1 | Per-CP honest lift | PASS | model MAE is below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_om_augmented |
| H2 | Anticipation stratum | PASS | model beats honest null on supported forecast_2_plus CP rows | EXPERIMENT_ONLY | hybrid_om_augmented |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_om_augmented |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_om_augmented |

## Model vs Honest Null by CP per Candidate

| cp | n_rows | model_mae | null_mae | model_exact_rate | null_exact_rate | model_beats_null | production_status | model_name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20:00 | 1096 | 1.138 | 1.589 | 0.268 | 0.216 | true | EXPERIMENT_ONLY | hybrid_local_only |
| 21:00 | 1096 | 0.997 | 1.364 | 0.323 | 0.234 | true | EXPERIMENT_ONLY | hybrid_local_only |
| 22:00 | 1096 | 0.884 | 1.084 | 0.364 | 0.285 | true | EXPERIMENT_ONLY | hybrid_local_only |
| 23:00 | 1096 | 0.818 | 0.831 | 0.390 | 0.372 | true | EXPERIMENT_ONLY | hybrid_local_only |
| 20:00 | 712 | 1.117 | 1.548 | 0.274 | 0.233 | true | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| 21:00 | 712 | 0.992 | 1.333 | 0.324 | 0.236 | true | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| 22:00 | 712 | 0.868 | 1.063 | 0.399 | 0.284 | true | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| 23:00 | 712 | 0.825 | 0.823 | 0.385 | 0.376 | false | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| 20:00 | 712 | 0.786 | 1.548 | 0.410 | 0.233 | true | EXPERIMENT_ONLY | hybrid_om_augmented |
| 21:00 | 712 | 0.760 | 1.333 | 0.445 | 0.236 | true | EXPERIMENT_ONLY | hybrid_om_augmented |
| 22:00 | 712 | 0.702 | 1.063 | 0.455 | 0.284 | true | EXPERIMENT_ONLY | hybrid_om_augmented |
| 23:00 | 712 | 0.656 | 0.823 | 0.469 | 0.376 | true | EXPERIMENT_ONLY | hybrid_om_augmented |

## Model Results

| test_year | model_name | n_train | n_test | mae | exact_rate | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | hybrid_local_only | 16753 | 1460 | 0.961 | 0.328 | EXPERIMENT_ONLY |
| 2024 | hybrid_local_only | 18213 | 1464 | 0.987 | 0.328 | EXPERIMENT_ONLY |
| 2025 | hybrid_local_only | 19677 | 1460 | 0.930 | 0.353 | EXPERIMENT_ONLY |
| 2024 | hybrid_om_augmented | 1456 | 1388 | 0.740 | 0.441 | EXPERIMENT_ONLY |
| 2025 | hybrid_om_augmented | 2844 | 1460 | 0.713 | 0.449 | EXPERIMENT_ONLY |
| 2024 | hybrid_local_only_covered_rows | 1456 | 1388 | 0.972 | 0.338 | EXPERIMENT_ONLY |
| 2025 | hybrid_local_only_covered_rows | 2844 | 1460 | 0.930 | 0.353 | EXPERIMENT_ONLY |

## Feature Audit

| feature | candidate | feature_role | production_status |
| --- | --- | --- | --- |
| slope_3h | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| dewpoint_depression | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| tmax_dminus1 | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| tmin_delta_tmax | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| wind_dir_change_s_to_n | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| precip_disruption | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| pressure_trend_3h | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| warming_rate_06_09 | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| nocturnal_plateau_flag | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| dewpoint_collapse_rate_3h | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| prefrontal_warming_window | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| nw_sector_not_foehn | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_base_transparency | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| k_cp | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cp_sin | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cp_cos | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| month_sin | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| month_cos | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| doy_sin | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| doy_cos | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score_x_macro_non_southerly | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score_x_macro_southerly_flow | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_non_southerly | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_southerly_flow | hybrid_local_only | local_remaining_warming_input | EXPERIMENT_ONLY |
| slope_3h | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| dewpoint_depression | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| tmax_dminus1 | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| tmin_delta_tmax | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| wind_dir_change_s_to_n | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| precip_disruption | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| pressure_trend_3h | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| warming_rate_06_09 | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| nocturnal_plateau_flag | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| dewpoint_collapse_rate_3h | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| prefrontal_warming_window | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| nw_sector_not_foehn | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_base_transparency | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| k_cp | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cp_sin | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cp_cos | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| month_sin | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| month_cos | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| doy_sin | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| doy_cos | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score_x_macro_non_southerly | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| foehn_score_x_macro_southerly_flow | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_non_southerly | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| cloud_cover_suppression_x_macro_southerly_flow | hybrid_om_augmented | local_remaining_warming_input | EXPERIMENT_ONLY |
| om_anchor_max | hybrid_om_augmented | nwp_anchor_input | EXPERIMENT_ONLY |
| om_anchor_delta | hybrid_om_augmented | nwp_anchor_input | EXPERIMENT_ONLY |
| om_anchor_delta_x_lead | hybrid_om_augmented | nwp_anchor_input | EXPERIMENT_ONLY |
| binary_macro_regime_label | all | categorical_input | EXPERIMENT_ONLY |
