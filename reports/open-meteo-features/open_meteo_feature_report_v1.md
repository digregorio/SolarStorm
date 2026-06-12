# Open-Meteo Feature Build Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Historical Weather and Historical Forecast remain blocked as causal predictors.

Previous Runs features are fixed-lead experiment-only predictors.

## Coverage

| n_feature_rows | n_dates | n_cps | min_date | max_date | production_status |
| --- | --- | --- | --- | --- | --- |
| 4384 | 1096 | 4 | 2023-01-01 | 2025-12-31 | EXPERIMENT_ONLY |

## Source Eligibility

| source_id | endpoint | model | causal_class | decision_status | n_success | feature_generation_allowed | feature_generation_reason | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forecast_api_best_match | forecast | best_match | live_seamless_forecast | OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA | 0 | False | live_forecast_forward_collection_only | EXPERIMENT_ONLY |
| historical_forecast_best_match | historical_forecast | best_match | seamless_historical_forecast | OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY | 1 | False | seamless_historical_forecast_lacks_run_metadata | EXPERIMENT_ONLY |
| historical_weather_era5 | historical_weather | era5 | reanalysis_not_forecast | OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA | 1 | False | reanalysis_blocked_as_predictor | EXPERIMENT_ONLY |
| previous_runs_gfs_temperature | previous_runs | gfs_seamless | fixed_lead_forecast | OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT | 1 | True | fixed_lead_forecast_pilot_allowed | EXPERIMENT_ONLY |
| single_runs_ecmwf_ifs_hres | single_runs | ecmwf_ifs025 | forecast_snapshot | OPEN_METEO_BLOCKED_BY_AVAILABILITY | 0 | False | forecast_snapshot_not_available | EXPERIMENT_ONLY |

## Feature Manifest

| feature | feature_source | non_null_rows | n_rows | production_status |
| --- | --- | --- | --- | --- |
| om_source_id | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_endpoint | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_model | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_causal_class | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_feature_status | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_request_url_sha256 | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_response_sha256 | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_run_time_utc | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |
| om_available_time_utc | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |
| om_valid_time_utc | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |
| om_lead_h | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |
| om_fixed_lead_days | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_fixed_lead_hours | open_meteo_previous_runs | 4384 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_temp_23_local_c | open_meteo_previous_runs | 4300 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_temp_cp_c | open_meteo_previous_runs | 4303 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_remaining_warming_c | open_meteo_previous_runs | 4300 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_day_max_c | open_meteo_previous_runs | 4304 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_day_min_c | open_meteo_previous_runs | 4304 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_cloud_cover_mean_pct | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_cloud_cover_low_mean_pct | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_pressure_msl_mean_hpa | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_wind_speed_10m_mean | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_wind_gusts_10m_max | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_wind_dir_10m_circular_mean | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_dewpoint_depression_23_local_c | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_foehn_support | open_meteo_previous_runs | 2848 | 4384 | EXPERIMENT_ONLY |
| om_prev_d1_stratus_support | open_meteo_previous_runs | 0 | 4384 | EXPERIMENT_ONLY |

## Blocked Sources

_No rows._
