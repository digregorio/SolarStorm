# Open-Meteo 2022 Backfill Feasibility Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Dry-run audit for causal Previous Runs historical backfill. This report does not overwrite current Open-Meteo feature tables.

## Decision

| decision_status | decision_rationale | ready_rows | partial_rows | blocked_rows | production_status |
| --- | --- | --- | --- | --- | --- |
| OPEN_METEO_2022_BACKFILL_FEASIBILITY_READY | Previous Runs provider decisions allow a 2022 backfill attempt; dry-run did not mutate the current feature parquet. | 96 | 0 | 0 | EXPERIMENT_ONLY |

## Feasibility

| year | cp | endpoint | model | provider_family | requested_dates | observed_dates | missing_dates | coverage_pct | coverage_status | blocker | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 20:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 20:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 20:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 20:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 20:00 | previous_runs | gem_global | ECCC_GEM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 20:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | gem_global | ECCC_GEM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 21:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | gem_global | ECCC_GEM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 22:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | gem_global | ECCC_GEM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2022 | 23:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 0 | 365 | 0.0 | READY_FOR_BACKFILL | missing_all_requested_dates | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | gem_global | ECCC_GEM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 20:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | gem_global | ECCC_GEM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 21:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | gem_global | ECCC_GEM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 22:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | gem_global | ECCC_GEM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2023 | 23:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | gfs_seamless | NOAA_GFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | icon_seamless | DWD_ICON | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | gem_global | ECCC_GEM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 20:00 | previous_runs | jma_seamless | JMA_GSM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | gfs_seamless | NOAA_GFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | icon_seamless | DWD_ICON | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | gem_global | ECCC_GEM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 21:00 | previous_runs | jma_seamless | JMA_GSM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | gfs_seamless | NOAA_GFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | icon_seamless | DWD_ICON | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | gem_global | ECCC_GEM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 22:00 | previous_runs | jma_seamless | JMA_GSM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | gfs_seamless | NOAA_GFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | icon_seamless | DWD_ICON | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | gem_global | ECCC_GEM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2024 | 23:00 | previous_runs | jma_seamless | JMA_GSM | 366 | 366 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | icon_seamless | DWD_ICON | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | gem_global | ECCC_GEM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 20:00 | previous_runs | jma_seamless | JMA_GSM | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 21:00 | previous_runs | gfs_seamless | NOAA_GFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
| 2025 | 21:00 | previous_runs | ecmwf_ifs025 | ECMWF_IFS | 365 | 365 | 0 | 100.0 | READY_FOR_BACKFILL |  | EXPERIMENT_ONLY |
