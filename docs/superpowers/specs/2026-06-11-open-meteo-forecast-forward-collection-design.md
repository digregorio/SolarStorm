# Open-Meteo Forecast Forward Collection Design

## Status

Drafted on 2026-06-11 for OM-M14. This spec defines the live-forward Forecast
API collection protocol for accumulating future Open-Meteo folds with
CP-causal metadata and without historical leakage.

All outputs remain `EXPERIMENT_ONLY`. This spec does not unlock production, EV,
pricing, shadow trading, or execution.

## Context

The Open-Meteo work has already separated historical backtest sources from live
forecast collection:

- Historical Weather/reanalysis is blocked as a causal predictor.
- Historical Forecast is audit-only unless per-row CP-causal run metadata is
  proven.
- Previous Runs can support fixed-lead historical experiments, but it is not a
  full live Forecast API snapshot reconstruction.
- Forecast API calls are live-forward only. Ordinary calls cannot recreate the
  exact forecast surface that would have been visible at past checkpoints.

OM-M14 therefore defines a collection protocol for future target days. The goal
is to start collecting forecast snapshots now, store their issuance metadata,
and later admit only mature, CP-causal rows into experiment-only validation.

## Goals

1. Define a stable collection key for live-forward Forecast API snapshots.
2. Preserve raw API responses and normalized provider-feature rows.
3. Enforce `available_time_utc <= cp_utc` before a row can become usable.
4. Keep future target rows `pending` until target-day labels have settled.
5. Prevent immature forecast rows from entering historical or nested validation.
6. Audit availability by endpoint, model, horizon, variable, and CP because
   Open-Meteo history differs by forecast source type.
7. Keep every generated artifact `EXPERIMENT_ONLY`.

## Non-Goals

- Do not reconstruct historical Forecast API snapshots from current live calls.
- Do not backfill historical nested validation with rows that were not collected
  live-forward under this protocol.
- Do not use pending rows in Onda 3 or Open-Meteo nested validation.
- Do not promote any Open-Meteo source to production.
- Do not implement EV, pricing, shadow trading, or execution.

## Collection Key

Each live-forward collection attempt is uniquely identified by:

```text
target_date_local
cp
endpoint
model
run_time_utc
```

Definitions:

- `target_date_local`: Wellington local date whose label will eventually be
  evaluated.
- `cp`: local checkpoint string, currently `20:00`, `21:00`, `22:00`, or
  `23:00`.
- `endpoint`: Open-Meteo endpoint, initially `forecast`.
- `model`: Open-Meteo model identifier or explicit API model value.
- `run_time_utc`: model run or forecast issuance anchor recorded from the
  response or request metadata.

Duplicate collection keys must be rejected. A retry of the same key may only
attach retry/audit metadata to the existing raw object; it must not create a
second normalized provider-feature row.

## Causality Gate

For each normalized forecast row:

```text
available_time_utc <= cp_utc
```

Required timestamps:

- `cp_utc`: local `(target_date_local, cp)` converted to UTC using the project
  timezone.
- `run_time_utc`: model run or issuance anchor.
- `available_time_utc`: earliest time the project believes this response was
  available for causal use. This must include any model-availability lag and
  safety margin used by the collector.
- `retrieved_at_utc`: wall-clock time when the collector fetched the response.
- `valid_time_utc`: forecast valid time for the hourly value or derived
  feature.

Rows that fail the gate are stored for audit with `row_status =
blocked_by_causality`. They cannot be used as predictor rows.

## Row Lifecycle and Maturity

Forward collection has a two-stage lifecycle:

1. `pending`: forecast data has been collected, cached, normalized, and passed
   basic schema checks, but labels for `target_date_local` have not settled.
2. `mature`: the target-day labels have settled and the row can be considered
   for experiment-only validation if it also passes the causality gate and
   availability audit.

Allowed row statuses:

```text
pending
mature
blocked_by_causality
blocked_by_duplicate_key
blocked_by_availability
blocked_by_schema
```

Maturity is label-driven, not forecast-driven. A row cannot become `mature`
until the downstream label source has finalized the target-day outcome used by
the Onda validation harness. The maturity process must record:

- `label_settled_at_utc`;
- `label_source`;
- `maturity_decision`;
- `maturity_notes`.

Pending rows may be reported in collection coverage dashboards, but they are
not training, validation, calibration, pricing, or decision rows.

## Storage Contract

The collector must write two surfaces.

### Raw Response Cache

The raw cache stores the unmodified API response and sidecar metadata. It must
include:

- collection key fields;
- request URL or canonical request parameters;
- `request_url_sha256`;
- `response_sha256`;
- `retrieved_at_utc`;
- HTTP status and error text when present;
- collector version;
- `production_status = EXPERIMENT_ONLY`.

The raw cache is the audit source of truth. Normalized tables must be
rebuildable from it.

### Normalized Provider-Feature Table

The normalized table is long/provider keyed and must include:

```text
target_date_local
cp
cp_utc
endpoint
model
provider_family
run_time_utc
available_time_utc
retrieved_at_utc
valid_time_utc
horizon_hours
variable
feature_name
feature_value
collection_key_sha256
request_url_sha256
response_sha256
row_status
label_settled_at_utc
production_status
```

Feature columns must remain provider-feature rows until a separate
experiment-only builder pivots or aggregates them. The forward collection table
is not a production feature store.

## Availability Audit

The collector must maintain an availability audit by:

- endpoint;
- model;
- variable;
- horizon or lead bucket;
- target year/month;
- CP;
- request success/failure;
- causality status;
- maturity status.

This audit is required because Open-Meteo coverage is limited differently by
forecast type. Forecast API live-forward collection, Historical Forecast,
Previous Runs, Single Runs, and Historical Weather have different historical
semantics and availability windows. A model/endpoint/horizon that works for one
source class must not be assumed to work for another.

The audit must be explicit when a row is absent because of request failure,
model coverage, horizon coverage, schema mismatch, causality failure, duplicate
key rejection, or label immaturity.

## Validation Rules

No forward Forecast API row may enter historical or nested validation until all
of these are true:

1. `row_status = mature`;
2. `production_status = EXPERIMENT_ONLY`;
3. `available_time_utc <= cp_utc`;
4. the collection key is unique;
5. the raw response cache contains the referenced response hash;
6. the endpoint/model/horizon availability audit marks the row usable;
7. target labels are settled and recorded.

Historical/nested validation must filter out `pending`, causality-blocked,
availability-blocked, duplicate, and schema-blocked rows. It must also report
the count of excluded rows by reason.

## Artifacts

Expected future artifact families:

- `data/open_meteo_forward_raw/`
  - raw response cache and sidecar metadata.
- `data/open_meteo_forward_provider_features.parquet`
  - normalized provider-feature rows.
- `reports/open-meteo-forward-collection/`
  - collection manifest;
  - duplicate-key rejection report;
  - availability audit by endpoint/model/horizon;
  - maturity audit;
  - causality audit;
  - collection report.

Every artifact must include or state `production_status = EXPERIMENT_ONLY`.

## Acceptance Criteria

- Collection keys use exactly
  `(target_date_local, cp, endpoint, model, run_time_utc)`.
- Duplicate collection keys are rejected.
- Every normalized row records `available_time_utc`.
- Every usable row passes `available_time_utc <= cp_utc`.
- Future target rows remain `pending` until labels settle.
- Pending rows never enter historical or nested validation.
- Availability is audited by endpoint, model, and horizon.
- Raw responses are cached and normalized provider-feature rows reference their
  hashes.
- Documentation explicitly freezes production, EV, pricing, shadow trading, and
  execution.
