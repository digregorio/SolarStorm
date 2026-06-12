# Open-Meteo Availability Report - 2026-06-10

production_status: EXPERIMENT_ONLY

This is an audit-only availability report. It does not write Open-Meteo causal features or promote any source by itself.

Historical Weather / reanalysis is blocked from causal feature generation.
Historical Forecast remains audit-only unless CP-causal run metadata is proven.
Single Runs can narrow a pilot to its available history instead of changing the Onda 3H baseline.
This availability audit does not write open_meteo_features.parquet.

## Decision Update

| source_id | endpoint | model | causal_class | n_probes | n_success | n_success_years | success_pct | decision_status | pilot_scope_note | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forecast_api_best_match | forecast | best_match | live_seamless_forecast | 0 | 0 | 0 | 0.00 | OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA | live_forward_collection_only | EXPERIMENT_ONLY |
| historical_forecast_best_match | historical_forecast | best_match | seamless_historical_forecast | 64 | 0 | 0 | 0.00 | OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY | requires_run_metadata_before_causal_use | EXPERIMENT_ONLY |
| historical_weather_era5 | historical_weather | era5 | reanalysis_not_forecast | 64 | 0 | 0 | 0.00 | OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA | diagnostic_only_reanalysis | EXPERIMENT_ONLY |
| previous_runs_gfs_temperature | previous_runs | gfs_seamless | fixed_lead_forecast | 64 | 0 | 0 | 0.00 | OPEN_METEO_BLOCKED_BY_AVAILABILITY | no_successful_probe | EXPERIMENT_ONLY |
| single_runs_ecmwf_ifs_hres | single_runs | ecmwf_ifs025 | forecast_snapshot | 28 | 0 | 0 | 0.00 | OPEN_METEO_BLOCKED_BY_AVAILABILITY | no_successful_probe | EXPERIMENT_ONLY |

## Availability by Source

| source_id | endpoint | model | causal_class | n_probes | n_success | n_success_years | has_run_metadata | has_lead_metadata | success_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forecast_api_best_match | forecast | best_match | live_seamless_forecast | 0 | 0 | 0 | False | False | 0.00 | EXPERIMENT_ONLY |
| historical_forecast_best_match | historical_forecast | best_match | seamless_historical_forecast | 64 | 0 | 0 | False | False | 0.00 | EXPERIMENT_ONLY |
| historical_weather_era5 | historical_weather | era5 | reanalysis_not_forecast | 64 | 0 | 0 | False | False | 0.00 | EXPERIMENT_ONLY |
| previous_runs_gfs_temperature | previous_runs | gfs_seamless | fixed_lead_forecast | 64 | 0 | 0 | False | False | 0.00 | EXPERIMENT_ONLY |
| single_runs_ecmwf_ifs_hres | single_runs | ecmwf_ifs025 | forecast_snapshot | 28 | 0 | 0 | True | True | 0.00 | EXPERIMENT_ONLY |

## Blocked Source Register

| source_id | endpoint | model | causal_class | causal_feature_allowed | blocked_reason | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| forecast_api_best_match | forecast | best_match | live_seamless_forecast | False | live_seamless_no_historical_runs | EXPERIMENT_ONLY |
| historical_forecast_best_match | historical_forecast | best_match | seamless_historical_forecast | False | seamless_no_run_metadata_until_proven | EXPERIMENT_ONLY |
| previous_runs_gfs_temperature | previous_runs | gfs_seamless | fixed_lead_forecast | False | fixed_lead_audit_only | EXPERIMENT_ONLY |
| single_runs_ecmwf_ifs_hres | single_runs | ecmwf_ifs025 | forecast_snapshot | True | run_initialisation_preserved | EXPERIMENT_ONLY |
| historical_weather_era5 | historical_weather | era5 | reanalysis_not_forecast | False | reanalysis_not_forecast | EXPERIMENT_ONLY |
