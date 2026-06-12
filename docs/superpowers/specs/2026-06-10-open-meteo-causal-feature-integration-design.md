# Open-Meteo Causal Feature Integration Design

## Status

Drafted on 2026-06-10 after the availability-first audit. This spec defines the
first technical integration of Open-Meteo data into experiment-only feature and
model artifacts. It does not approve production, EV, market pricing, shadow
trading, or live execution.

All outputs remain `EXPERIMENT_ONLY`.

## Context

The first Open-Meteo audit created a source taxonomy, bounded probe runner,
causal metadata checks, decision artifacts, and a no-features guard. The
plan-only report under `reports/open-meteo-availability/` intentionally did not
create `data/open_meteo_features.parquet`.

The live smoke report under `reports/open-meteo-availability-live-smoke/`
showed:

- Historical Forecast responded successfully, but remains audit-only because it
  is a seamless historical forecast time series without per-row CP-causal run
  metadata.
- Previous Runs responded successfully and is eligible only for fixed-lead skill
  audit and conservative feature pilots.
- Historical Weather responded successfully but is blocked as reanalysis.
- Single Runs returned HTTP 400 for the current ECMWF request contract. It
  remains the preferred full snapshot source, but feature generation from it is
  blocked until a live or fixture-backed probe proves the exact endpoint/model
  contract.

Official Open-Meteo documentation checked on 2026-06-10:

- Single Runs preserves individual model run structure and uses `run` as the
  UTC initialization time. ECMWF IFS HRES 9 km is listed from 2024-03-14, while
  most other models are archived from 2025-09-01.
  https://open-meteo.com/en/docs/single-runs-api
- Previous Runs exposes fixed lead-time offsets. `temperature_2m_previous_day1`
  is the value predicted 24 hours before valid time, and offsets continue
  through day 7. GFS 2 m temperature is listed from March 2021.
  https://open-meteo.com/en/docs/previous-runs-api
- Historical Forecast stitches the first hours of model updates into a seamless
  hourly time series from around 2022 onward. It points users to Single Runs for
  full individual run horizons.
  https://open-meteo.com/en/docs/historical-forecast-api
- Historical Weather is based on reanalysis datasets and can fill observation
  gaps using modeled estimates. It is not a forecast snapshot.
  https://open-meteo.com/en/docs/historical-weather-api

## Goals

1. Create an experiment-only Open-Meteo feature pipeline with strict source
   eligibility.
2. Permit `data/open_meteo_features.parquet` only after an explicit decision
   artifact allows the selected source class.
3. Integrate Previous Runs as the first conservative source because it has
   live-smoke evidence and stable fixed-lead semantics.
4. Preserve Single Runs support as the preferred future snapshot path, while
   blocking feature generation until its request contract is proven.
5. Join Open-Meteo features to the Onda 3H nested-validation harness without
   overwriting `data/features.parquet` or changing the local-data baseline.
6. Produce reports that compare local-only Onda 3F against Open-Meteo-augmented
   candidates on identical temporal folds.

## Non-Goals

- Do not use Historical Weather/reanalysis as a model predictor.
- Do not use Historical Forecast as a causal backtest predictor until run and
  lead metadata are present per feature row.
- Do not treat Previous Runs as equivalent to a full intraday model snapshot.
- Do not promote any Open-Meteo model to production.
- Do not mutate the existing `data/features.parquet`.
- Do not require network access in unit tests.

## Source Eligibility

| Source class | Integration status | Reason |
| --- | --- | --- |
| `fixed_lead_forecast` / Previous Runs | Allowed for conservative feature pilot after live or fixture success. | Fixed lead offsets have clear meaning and the live smoke succeeded. |
| `forecast_snapshot` / Single Runs | Implemented but blocked for feature output until contract success. | It is the correct full-snapshot source, but the current live smoke returned HTTP 400. |
| `seamless_historical_forecast` | Audit-only. | Seamless stitched series lacks per-row CP run/lead metadata. |
| `reanalysis_not_forecast` | Blocked. | Reanalysis is not an issued forecast. |
| `live_seamless_forecast` | Forward collection only. | Ordinary live calls cannot reconstruct historical run snapshots. |

## Data Artifacts

New generated artifacts:

- `data/open_meteo_raw/`
  - raw response text or JSON for live/manual fetches;
  - sidecar metadata with request URL hash, response hash, source id,
    endpoint, model, date, CP, and retrieval timestamp.
- `data/open_meteo_features.parquet`
  - one row per `(date_local, cp)` where at least one eligible Open-Meteo
    source produced usable causal features;
  - never written if no eligible decision exists;
  - never written by the availability audit command.
- `reports/open-meteo-features/`
  - feature manifest;
  - coverage by year, month, CP, source, and variable;
  - source-decision snapshot copied from the availability gate;
  - blocked-source register;
  - report explaining which source classes were used or blocked.
- `reports/onda3-open-meteo-pilot/`
  - nested-validation comparison between local-only and Open-Meteo-augmented
    candidates;
  - prediction rows with exact-bracket diagnostics;
  - regime/month/CP slices;
  - decision update that remains `EXPERIMENT_ONLY`.
- `data/open_meteo_multi_provider_features.parquet`
  - long-format provider-keyed Previous Runs table generated by the
    multi-provider follow-up sprint;
  - key surface: `(date_local, cp, endpoint, model)`;
  - preserves provider and provider-family metadata so calibration can
    deduplicate model families before averaging or weighting;
  - generated coverage as of 2026-06-10: 26,304 rows, 1,096 dates, 2023-01-01
    through 2025-12-31, four CPs, and six provider families.
- `reports/open-meteo-provider-error-atlas-multi-provider/`
  - recalculated provider error atlas on the multi-provider feature table;
  - generated state as of 2026-06-10: 18,440 non-null provider-error rows and
    873 metric rows;
  - all rows remain `EXPERIMENT_ONLY`.

## Feature Contract

The Open-Meteo feature table must contain:

- keys: `date_local`, `cp`;
- source metadata: `om_source_id`, `om_endpoint`, `om_model`,
  `om_causal_class`, `om_feature_status`;
- request metadata: `om_request_url_sha256`, `om_response_sha256`;
- causal metadata where available:
  `om_run_time_utc`, `om_available_time_utc`, `om_valid_time_utc`,
  `om_lead_h`;
- lead-offset metadata for Previous Runs:
  `om_fixed_lead_days`, `om_fixed_lead_hours`;
- physically motivated numeric features with `om_` prefix.

Initial Previous Runs features:

- `om_prev_d1_temp_23_local_c`
- `om_prev_d1_temp_cp_c`
- `om_prev_d1_remaining_warming_c`
- `om_prev_d1_day_max_c`
- `om_prev_d1_day_min_c`
- `om_prev_d1_cloud_cover_mean_pct`
- `om_prev_d1_cloud_cover_low_mean_pct`
- `om_prev_d1_pressure_msl_mean_hpa`
- `om_prev_d1_wind_speed_10m_mean`
- `om_prev_d1_wind_gusts_10m_max`
- `om_prev_d1_wind_dir_10m_circular_mean`
- `om_prev_d1_dewpoint_depression_23_local_c`
- `om_prev_d1_foehn_support`
- `om_prev_d1_stratus_support`

The first implementation may support only day-1 features if the API coverage
for other offsets is incomplete. Additional fixed lead days can be added after
coverage evidence, using the same schema pattern.

## Causality Rules

For every Open-Meteo feature row:

1. Convert `(date_local, cp)` to `cp_utc` using the project timezone.
2. Reject any source whose decision artifact blocks feature generation.
3. Reject Historical Weather and Historical Forecast as causal predictors even
   if responses contain complete data.
4. For Single Runs, require `run_time_utc`, `available_time_utc`,
   `valid_time_utc`, and `lead_h`, and require
   `available_time_utc <= cp_utc`.
5. For Previous Runs, record the fixed lead offset explicitly. Day-1 means a
   value predicted 24 hours before the valid time. It is eligible for
   conservative fixed-lead features, not for claiming full CP snapshot
   reconstruction.
6. Feature names must identify the source and lead class; no Open-Meteo column
   can be named like a local METAR feature.
7. Feature generation fails if duplicate `(date_local, cp)` rows are produced.

## Commands

Add these CLIs:

- `open-meteo-fetch`
  - creates bounded raw/cache artifacts for eligible sources;
  - supports `--live` for network access;
  - supports fixture mode for tests and reproducible development;
  - never trains a model.
- `open-meteo-build-features`
  - reads the source decision artifact and raw/cache responses;
  - writes `data/open_meteo_features.parquet` only when the selected source is
    allowed;
  - writes `reports/open-meteo-features/`.
- `onda3-open-meteo-pilot`
  - reads local features, labels, binary macro assignments, and
    `data/open_meteo_features.parquet`;
  - joins on `(date_local, cp)`;
  - runs a nested validation comparison using the Onda 3H split semantics;
  - writes `reports/onda3-open-meteo-pilot/`.

## Model Experiment Design

The first pilot should compare:

1. **Local-only reference:** current Onda 3F selected through Onda 3H.
2. **Previous Runs augmented:** Onda 3F feature set plus the allowed
   `om_prev_d1_*` features.
3. **Single Runs augmented:** disabled until Single Runs feature generation is
   unlocked by decision artifact.

The pilot window must be narrowed to rows with Open-Meteo feature coverage. The
local-only reference must be recomputed on the same narrowed rows so the
comparison is fair.

## Next Evolution After Current GFS Previous Runs Pilot

The first implemented Open-Meteo feature source is intentionally narrow:
`previous_runs_gfs_temperature` uses `gfs_seamless` from the Previous Runs API.
It is not a multi-provider ensemble. The later OM-M3 table expands the source
surface to several provider families, but it is still not a calibrated
ensemble. Any future reference to "Open-Meteo ensemble" must distinguish
between:

- Open-Meteo as an access API;
- the underlying provider/model key such as GFS, ECMWF, AIFS, ICON, GEM, or
  JMA;
- Open-Meteo's separate ensemble endpoint;
- a project-local ensemble built by blending provider predictions.

The next technical wave should not expand local model complexity first. It
should continue the multi-provider audit and calibration sequence:

1. Probe provider/model availability and request contracts for Wellington,
   starting with Previous Runs and Single Runs. Status: implemented for OM-M1;
   Previous Runs passed sampled checks for six families, Single Runs remains
   blocked by request contract.
2. Build a causal, provider-keyed historical Previous Runs feature table for
   providers that pass the availability/request-contract gate. Status:
   implemented for OM-M3 in
   `data/open_meteo_multi_provider_features.parquet`; the GFS-only
   `data/open_meteo_features.parquet` remains preserved.
3. Measure raw provider error and signed bias by year, month, CP, and binary
   macro regime on the expanded table. Status: implemented in
   `reports/open-meteo-provider-error-atlas-multi-provider/`.
4. Build family-deduplicated candidates so multiple variants from one provider
   family do not overweight that institution. Status: implemented for OM-M4
   under `reports/open-meteo-provider-calibration/`.
5. Test recent signed-bias correction with shrinkage and disable
   regime-conditioned correction when slice support is insufficient. Status:
   implemented for OM-M4; all rows remain `EXPERIMENT_ONLY`.
6. Re-run nested validation against local-only Onda 3F and the current GFS
   Previous Runs augmentation on identical covered rows. Status: implemented
   for OM-M5 under
   `reports/onda3-open-meteo-calibrated-nested-validation/`.

Calibration is now unblocked because the expanded table has overlapping
historical rows from six independent provider families. OM-M4 and OM-M5 now
exist, but the final model-selection blocker remains coverage: the strict
common-row nested comparison has only one valid outer fold. A calibrated
ensemble claim remains experiment-only until more valid folds or a stronger
coverage/cross-validation design can support a decision.

The detailed sprint plan is
`docs/superpowers/plans/2026-06-10-open-meteo-multi-provider-calibration-sprints.md`.

## Decision Rules

The Open-Meteo pilot may only emit experiment decisions:

- `KEEP_LOCAL_ONLY_REFERENCE`
- `KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW`
- `PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`
- `BLOCK_OPEN_METEO_BY_CAUSALITY`
- `BLOCK_OPEN_METEO_BY_AVAILABILITY`

It may not emit production or trading readiness.

## Testing Requirements

- Unit tests use fixture JSON and fake clients only.
- TDD must cover:
  - source eligibility blocks;
  - no Historical Weather predictor generation;
  - no Historical Forecast predictor generation;
  - Previous Runs feature extraction from fixture payload;
  - duplicate key rejection;
  - no overwrite of `data/features.parquet`;
  - Open-Meteo pilot joins only covered rows;
  - nested comparison uses identical rows for local-only and augmented
    candidates;
  - all outputs remain `EXPERIMENT_ONLY`.
- Optional live smoke tests can run manually but must not be required for CI.

## Acceptance Criteria

- `open-meteo-build-features` can write `data/open_meteo_features.parquet` from
  an allowed Previous Runs fixture or live cache.
- The generated feature table contains only `om_` feature columns plus key and
  metadata columns.
- Historical Weather and Historical Forecast cannot produce causal feature
  rows, even when their API probes succeed.
- Single Runs support exists but remains blocked until a successful
  source-decision row permits it.
- `onda3-open-meteo-pilot` produces experiment-only artifacts comparing
  local-only and Open-Meteo-augmented candidates on identical narrowed rows.
- Existing Onda 3H and `data/features.parquet` remain unchanged.
