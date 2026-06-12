# Open-Meteo Availability-First Integration Design

## Status

Draft for review on 2026-06-09. This spec defines the next Open-Meteo/NWP
integration step after Onda 3H. Implementation and model training remain
blocked until this availability and causality design is approved.

All outputs from this step remain `EXPERIMENT_ONLY`. This spec does not unlock
production, EV, market pricing, shadow trading, or live execution.

## Problem

Onda 3H selected Onda 3F as the local-data model-selection surface, but the next
information source is external forecast data. Open-Meteo has several APIs whose
historical coverage and causal meaning are different:

- live/seamless forecast data;
- historical forecast time series;
- previous model runs at fixed lead offsets;
- single model runs by run initialisation time;
- historical weather/reanalysis.

The quarantined Wellington project already captured the important rule:
NWP features must be forecast snapshots, not reanalysis/archive used as if they
were forecasts. It required storing `(model, run_time_utc, lead_hours,
valid_time_utc)` and failing the build if reanalysis/archive was labelled as
forecast. This spec keeps that rule and adds an explicit availability audit
because the usable history differs by Open-Meteo endpoint and model.

## Source Notes

Official Open-Meteo docs checked on 2026-06-09:

- Forecast API: live forecast endpoint stitches latest model runs into a
  seamless time series and does not preserve individual run structure.
  https://open-meteo.com/en/docs
- Historical Forecast API: seamless historical forecast-model time series;
  model availability varies, often starting from 2021 or 2022, with IFS HRES
  listed from 2017 and GFS from 2021-03-23.
  https://open-meteo.com/en/docs/historical-forecast-api
- Previous Model Runs API: fixed lead offsets of 1-7 days; most models archived
  from January 2024, while GFS 2 m temperature extends to March 2021.
  https://open-meteo.com/en/docs/previous-runs-api
- Single Runs API: exact model run by UTC initialisation time; ECMWF IFS HRES
  from 2024-03-14, most other models from 2025-09-01.
  https://open-meteo.com/en/docs/single-runs-api
- Historical Weather API: reanalysis/historical weather, not forecast. It can
  go back to 1940 for ERA5, 1950 for ERA5-Land, and 2017 for ECMWF IFS, but it
  is not a causal forecast snapshot.
  https://open-meteo.com/en/docs/historical-weather-api
- Model Updates API: exposes model availability timing and notes that servers
  are eventually consistent; recent runs should wait an additional 10 minutes
  after availability.
  https://open-meteo.com/en/docs/model-updates

## Goals

1. Build an Open-Meteo availability audit before any model feature is accepted.
2. Classify every candidate data source by causal status:
   `forecast_snapshot`, `fixed_lead_forecast`, `seamless_historical_forecast`,
   `live_seamless_forecast`, or `reanalysis_not_forecast`.
3. Quantify coverage by endpoint, model, variable, year, month, CP, and lead.
4. Prove whether the source can reconstruct information available at each
   checkpoint without using future data.
5. Produce a decision artifact that says which source, if any, can feed the
   next model experiment.
6. Keep Historical Weather/reanalysis out of causal model features unless it is
   explicitly marked as diagnostic-only.

## Non-Goals

- Do not train an Open-Meteo model in this spec.
- Do not blend Open-Meteo into Onda 3F until the availability gate passes.
- Do not use Historical Weather/reanalysis as a causal forecast input.
- Do not treat a seamless historical time series as a run/lead snapshot unless
  the response supplies enough metadata to reconstruct issuance before CP.
- Do not implement market, EV, pricing, or execution logic.

## API Source Taxonomy

| Source | Causal Use | Historical Limitation | Default Decision |
|---|---|---|---|
| Forecast API | Live forward use only. It stitches latest runs and is suitable for future snapshots if request time is recorded. | No full historical run reconstruction from ordinary calls. | Use later for forward collection after backtest source is chosen. |
| Historical Forecast API | Candidate for broad ML covariates only after audit. It is seamless and forecast-model-derived, but not automatically a CP-available run snapshot. | Coverage depends on model. Some global models start 2021/2022; IFS HRES is listed from 2017. | Audit-only until metadata proves causal selection. |
| Previous Model Runs API | Useful for fixed lead-skill curves and bias baselines. | Fixed offsets 1-7 days; most models from Jan 2024, GFS 2 m temperature from Mar 2021. This is coarse for same-day intraday CPs. | Lead audit candidate, not primary intraday source. |
| Single Runs API | Preferred causal source because it preserves run initialisation and full horizon. | ECMWF IFS HRES from 2024-03-14; most other models from 2025-09-01. | Primary pilot candidate if coverage is enough. |
| Historical Weather API | Diagnostic or comparison only. | Long history, but reanalysis/historical reconstruction, not issued forecast. | Block as model predictor for causal backtests. |

## Causality Rules

For any feature row `(date_local, cp)`:

1. Convert the local checkpoint to `cp_utc` using the project timezone.
2. A forecast run is eligible only if:
   `run_initialisation_time_utc + model_availability_lag + safety_margin <= cp_utc`.
3. Default `safety_margin` is 10 minutes beyond Open-Meteo availability time for
   live/current checks. For historical Single Runs, use model-class defaults
   unless the Model Updates API supplies concrete availability:
   - global models: 6 hours after run initialisation;
   - regional models: 3 hours after run initialisation.
4. Store `selected_run_time_utc`, `selected_valid_time_utc`, `selected_lead_h`,
   `endpoint`, `model`, `variable`, `request_url_sha256`, and
   `response_sha256`.
5. Reject any candidate feature where `valid_time_utc <= run_time_utc` for
   a value that is labelled as forecast lead output.
6. Reject any backtest row whose selected run is initialised or available after
   the CP.

## Availability Audit Design

The first implementation should be audit-only:

1. Define a source registry for NZWN:
   - endpoint;
   - model name or `best_match`;
   - variables;
   - nominal available-from date;
   - expected run cadence;
   - expected horizon;
   - causal class.
2. Probe candidate endpoints over the Onda 3H years:
   - `2022`, `2023`, `2024`, `2025` where possible;
   - all current CPs: `20:00`, `21:00`, `22:00`, `23:00`;
   - target valid anchors for same-day Tmax and late-spike windows.
3. Record per-request success/failure without soft-failing.
4. Produce coverage tables by:
   - source;
   - model;
   - variable;
   - year;
   - month;
   - CP;
   - lead bucket;
   - selected run cycle.
5. Decide source eligibility:
   - `Single Runs` can proceed to pilot if it covers at least two evaluation
     years or if the report explicitly narrows the pilot to its available
     post-2024 window.
   - `Previous Runs` can proceed only as a fixed-lead skill audit.
   - `Historical Forecast` can proceed only if the audit can prove CP-causal
     selection or is labelled as seamless diagnostic covariate.
   - `Historical Weather` remains diagnostic-only.

## Proposed Variables

Initial variables should be narrow and physically tied to the known Wellington
failure modes:

- `temperature_2m`
- `dew_point_2m`
- `relative_humidity_2m`
- `surface_pressure`
- `pressure_msl` or `sealevel_pressure`
- `cloud_cover`, `cloud_cover_low`, `cloud_cover_mid`, `cloud_cover_high`
- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- optional later: boundary-layer or pressure-level variables if coverage is
  proven and call volume remains manageable.

Derived candidate features are audit-only until the availability gate passes:

- forecasted remaining-day Tmax after CP;
- forecasted day Tmax and its lead;
- model residual target: `actual_tmax - nwp_tmax_pred`;
- forecasted foehn/NW support: wind sector plus dewpoint depression;
- forecasted stratus/cloud suppression;
- run-to-run disagreement if multiple eligible runs or models are available.

## Artifacts

Expected output directory:

- `reports/open-meteo-availability/`

Expected artifacts:

- `open_meteo_source_registry_v1.csv`
- `open_meteo_probe_plan_v1.csv`
- `open_meteo_probe_results_v1.csv`
- `open_meteo_availability_by_source_v1.csv`
- `open_meteo_availability_by_year_month_cp_v1.csv`
- `open_meteo_causal_selection_audit_v1.csv`
- `open_meteo_blocked_source_register_v1.csv`
- `open_meteo_decision_update_v1.csv`
- `open_meteo_availability_report_v1.md`

No `data/open_meteo_features.parquet` should be created until the decision
artifact says a source is eligible for model feature generation.

## Decision Statuses

- `OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT`
- `OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT`
- `OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY`
- `OPEN_METEO_BLOCKED_BY_AVAILABILITY`
- `OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA`

## Acceptance Criteria

- The availability report includes all five source classes in the taxonomy.
- The audit explicitly states which endpoints are forecast snapshots and which
  are not.
- The audit reports coverage by year, month, CP, model, endpoint, and variable.
- Any source without run/lead or availability metadata is blocked from causal
  backtest features unless it is explicitly labelled diagnostic-only.
- Historical Weather/reanalysis is blocked from causal model features.
- Every output includes `production_status = EXPERIMENT_ONLY`.
- The report explains when the available historical window is too short for the
  existing 2023-2025 nested validation and proposes a narrower pilot instead of
  silently changing the split.

## Open Questions

1. Should the first pilot prefer ECMWF IFS HRES Single Runs because it is the
   cleanest run/lead source despite starting in 2024-03?
2. Should GFS Previous Runs be used only as a lead-skill baseline because its
   2 m temperature history reaches 2021-03 but the API exposes fixed D1-D7
   offsets rather than same-day run selection?
3. Should Historical Forecast be allowed as a seamless broad covariate if it
   improves skill, or kept strictly diagnostic until run metadata is available?

## Recommendation

Proceed with an availability-first implementation. The first code step should
not train a model. It should build the source registry, run bounded probes, and
produce the decision report. Only after that should we create Open-Meteo feature
columns or compare them against the Onda 3H local-data baseline.
