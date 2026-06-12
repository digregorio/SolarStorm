# Open-Meteo Multi-Provider Availability Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

This audit proves request contracts and availability only. It does not create model features or approve production use.

## Decision Update

| endpoint | model | provider | provider_family | coverage_expectation | causal_role | n_probes | n_success | n_success_years | has_run_metadata | has_lead_metadata | errors | success_pct | decision_status | feature_gate_scope | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_runs | gfs_seamless | NOAA | NOAA_GFS | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | gfs_seamless | NOAA | NOAA_GFS | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF | ECMWF_IFS | global_candidate | snapshot_preferred_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | ecmwf_ifs025 | ECMWF | ECMWF_IFS | global_candidate | snapshot_preferred_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF | ECMWF_AIFS | global_candidate | snapshot_preferred_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | ecmwf_aifs025_single | ECMWF | ECMWF_AIFS | global_candidate | snapshot_preferred_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD | DWD_ICON | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | icon_seamless | DWD | DWD_ICON | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC | ECCC_GEM | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | gem_global | ECCC | ECCC_GEM | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA | JMA_GSM | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 4 | 2 | False | False |  | 100.0 | OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS | fixed_lead_provider_error_atlas | EXPERIMENT_ONLY |
| single_runs | jma_seamless | JMA | JMA_GSM | global_candidate | fixed_lead_and_snapshot_candidate | 4 | 0 | 0 | True | True | http_400 | 0.0 | OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT | single_runs_request_contract_not_proven | EXPERIMENT_ONLY |

## Availability Matrix

| endpoint | model | provider_family | calendar_year | month | cp | n_probes | n_success | has_run_metadata | has_lead_metadata | success_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD_ICON | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD_ICON | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD_ICON | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | icon_seamless | DWD_ICON | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA_GSM | 2024 | 2024-07 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA_GSM | 2024 | 2024-07 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA_GSM | 2025 | 2025-01 | 20:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| previous_runs | jma_seamless | JMA_GSM | 2025 | 2025-01 | 23:00 | 1 | 1 | False | False | 100.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2024 | 2024-07 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2024 | 2024-07 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2025 | 2025-01 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_aifs025_single | ECMWF_AIFS | 2025 | 2025-01 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_ifs025 | ECMWF_IFS | 2024 | 2024-07 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_ifs025 | ECMWF_IFS | 2024 | 2024-07 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_ifs025 | ECMWF_IFS | 2025 | 2025-01 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | ecmwf_ifs025 | ECMWF_IFS | 2025 | 2025-01 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gem_global | ECCC_GEM | 2024 | 2024-07 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gem_global | ECCC_GEM | 2024 | 2024-07 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gem_global | ECCC_GEM | 2025 | 2025-01 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gem_global | ECCC_GEM | 2025 | 2025-01 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gfs_seamless | NOAA_GFS | 2024 | 2024-07 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gfs_seamless | NOAA_GFS | 2024 | 2024-07 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gfs_seamless | NOAA_GFS | 2025 | 2025-01 | 20:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |
| single_runs | gfs_seamless | NOAA_GFS | 2025 | 2025-01 | 23:00 | 1 | 0 | True | True | 0.0 | EXPERIMENT_ONLY |

## Registry

| station | latitude | longitude | model | provider | provider_family | endpoint_priority | coverage_expectation | causal_role | priority_rank | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NZWN | -41.3272 | 174.8053 | gfs_seamless | NOAA | NOAA_GFS | previous_runs,single_runs | global_candidate | fixed_lead_and_snapshot_candidate | 10 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | ecmwf_ifs025 | ECMWF | ECMWF_IFS | single_runs,previous_runs | global_candidate | snapshot_preferred_candidate | 20 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | ecmwf_aifs025_single | ECMWF | ECMWF_AIFS | single_runs,previous_runs | global_candidate | snapshot_preferred_candidate | 30 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | icon_seamless | DWD | DWD_ICON | previous_runs,single_runs | global_candidate | fixed_lead_and_snapshot_candidate | 40 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | icon_eu | DWD | DWD_ICON | previous_runs,single_runs | regional_expected_missing_for_wellington | coverage_probe_only | 41 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | icon_d2 | DWD | DWD_ICON | previous_runs,single_runs | regional_expected_missing_for_wellington | coverage_probe_only | 42 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | gem_seamless | ECCC | ECCC_GEM | previous_runs,single_runs | global_candidate | fixed_lead_and_snapshot_candidate | 50 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | gem_global | ECCC | ECCC_GEM | previous_runs,single_runs | global_candidate | fixed_lead_and_snapshot_candidate | 51 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | gem_regional | ECCC | ECCC_GEM | previous_runs,single_runs | regional_expected_missing_for_wellington | coverage_probe_only | 52 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | gem_hrdps_continental | ECCC | ECCC_GEM | previous_runs,single_runs | regional_expected_missing_for_wellington | coverage_probe_only | 53 | EXPERIMENT_ONLY |
| NZWN | -41.3272 | 174.8053 | jma_seamless | JMA | JMA_GSM | previous_runs,single_runs | global_candidate | fixed_lead_and_snapshot_candidate | 60 | EXPERIMENT_ONLY |
