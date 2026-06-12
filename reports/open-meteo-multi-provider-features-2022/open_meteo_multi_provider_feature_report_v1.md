# Open-Meteo Multi-Provider Feature Build Report

Generated: 2026-06-11

production_status: EXPERIMENT_ONLY

This report builds causal Previous Runs features and audits provider-family overlap. It does not train, blend, calibrate, or approve production use.

## Feature Decision

| decision_status | decision_reason | n_feature_rows | n_provider_families | n_overlapping_provider_families | production_status |
| --- | --- | --- | --- | --- | --- |
| OPEN_METEO_MULTI_PROVIDER_FEATURES_READY | at_least_two_provider_families_overlap | 8760 | 6 | 6 | EXPERIMENT_ONLY |

## Coverage

| n_feature_rows | n_dates | n_cps | n_models | n_provider_families | n_overlapping_provider_families | min_date | max_date | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8760 | 365 | 4 | 6 | 6 | 6 | 2022-01-01 | 2022-12-31 | EXPERIMENT_ONLY |

## Source Selection

| endpoint | model | provider | provider_family | decision_status | feature_gate_scope | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| previous_runs | ecmwf_aifs025_single | ECMWF | ECMWF_AIFS | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF | ECMWF_IFS | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC | ECCC_GEM | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA | NOAA_GFS | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD | DWD_ICON | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA | JMA_GSM | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |

## Feature Manifest

| feature | feature_source | non_null_rows | n_rows | production_status |
| --- | --- | --- | --- | --- |
| om_source_id | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| om_causal_class | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| feature_gate_scope | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| om_provider_tmax_pred_c | open_meteo_multi_provider_previous_runs | 2920 | 8760 | EXPERIMENT_ONLY |
| om_provider_run_time_utc | open_meteo_multi_provider_previous_runs | 0 | 8760 | EXPERIMENT_ONLY |
| om_provider_available_time_utc | open_meteo_multi_provider_previous_runs | 0 | 8760 | EXPERIMENT_ONLY |
| om_provider_lead_hours | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| request_url_sha256 | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| response_sha256 | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| source_decision_status | open_meteo_multi_provider_previous_runs | 8760 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_temp_23_local_c | open_meteo_multi_provider_previous_runs | 2920 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_temp_cp_c | open_meteo_multi_provider_previous_runs | 2920 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_remaining_warming_c | open_meteo_multi_provider_previous_runs | 2920 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_day_min_c | open_meteo_multi_provider_previous_runs | 2920 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_cloud_cover_mean_pct | open_meteo_multi_provider_previous_runs | 1460 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_cloud_cover_low_mean_pct | open_meteo_multi_provider_previous_runs | 0 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_pressure_msl_mean_hpa | open_meteo_multi_provider_previous_runs | 1460 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_wind_speed_10m_mean | open_meteo_multi_provider_previous_runs | 1352 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_wind_gusts_10m_max | open_meteo_multi_provider_previous_runs | 0 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_wind_dir_10m_circular_mean | open_meteo_multi_provider_previous_runs | 1372 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_dewpoint_depression_23_local_c | open_meteo_multi_provider_previous_runs | 1460 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_foehn_support | open_meteo_multi_provider_previous_runs | 1352 | 8760 | EXPERIMENT_ONLY |
| om_prev_d1_stratus_support | open_meteo_multi_provider_previous_runs | 0 | 8760 | EXPERIMENT_ONLY |
