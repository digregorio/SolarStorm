# Open-Meteo Forecast Forward Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement OM-M14 live-forward Forecast API collection so future Open-Meteo rows accumulate with CP-causal metadata, mature only after labels settle, and remain blocked from historical leakage.

**Architecture:** Add a focused forward-collection layer under `solarstorm.open_meteo` that writes a raw response cache, normalized provider-feature rows, maturity audits, and availability audits. The validation harness must consume only mature, CP-causal, non-duplicate rows. All outputs stay `EXPERIMENT_ONLY` and do not unlock production, EV, pricing, shadow trading, or execution.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, Ruff, existing `solarstorm.open_meteo` Open-Meteo client/cache patterns, existing Onda 3/Open-Meteo nested validation filters.

---

## Implementation Status

Implemented on 2026-06-11 in fixture-mode.

- Code: `solarstorm/open_meteo/_forward_collection.py`.
- CLI: `open-meteo-forward-collection`.
- Tests: `tests/test_open_meteo_forward_collection.py`.
- Fixture: `tests/fixtures/open_meteo_forecast_fixture.json`.
- Smoke artifacts: `reports/open-meteo-forward-collection/`.
- Live network collection is intentionally still outside this implementation
  and must be added behind an explicit `--live` gate in a later sprint.

The task checklist below is retained as the original TDD execution plan. Its
runtime scope is now covered by `tests/test_open_meteo_forward_collection.py`
and the generated smoke artifacts in `reports/open-meteo-forward-collection/`.

## Guardrails

- All generated rows and reports must include `production_status = EXPERIMENT_ONLY`.
- Do not overwrite existing historical Open-Meteo feature parquet files.
- Do not mutate `data/features.parquet` or label artifacts.
- Do not use the live Forecast API to reconstruct historical snapshots.
- Do not let `pending` rows enter historical or nested validation.
- Unit tests must not hit the network.
- Live collection, if later added, must be behind an explicit `--live` flag.
- No production, EV, pricing, shadow trading, or execution work is unlocked.

## File Structure

- Create `solarstorm/open_meteo/_forward_collection.py`
  - Collection key model, duplicate rejection, raw cache metadata, normalized
    provider-feature rows, maturity transition, and availability audit.
- Modify `solarstorm/open_meteo/__init__.py`
  - Export forward-collection builders and validators.
- Modify `solarstorm/__main__.py`
  - Add future CLI commands for fixture/live collection and maturity audit.
- Modify the Open-Meteo nested validation input path used by existing
  validation code
  - Filter forward rows to mature, causality-passing rows only.
- Create `tests/test_open_meteo_forward_collection.py`
  - TDD coverage for pending rows, `available_time_utc`, duplicate keys,
    maturity, raw-cache metadata, and availability audit.
- Create or extend the relevant nested-validation test file
  - Prove immature forward rows are excluded from historical/nested validation.
- Generate future reports under `reports/open-meteo-forward-collection/`
  - Manifest, causality audit, maturity audit, availability audit, and duplicate
    rejection report.

---

### Task 1: Collection Schema and Pending Rows

**Files:**
- Create: `tests/test_open_meteo_forward_collection.py`
- Create: `solarstorm/open_meteo/_forward_collection.py`
- Modify: `solarstorm/open_meteo/__init__.py`

- [ ] **Step 1: Write the failing pending-row test**

Add a test that builds normalized rows from a fixture Forecast API payload for a
future target date whose label is not settled:

```python
def test_future_target_rows_are_pending_until_labels_settle():
    rows = build_forward_provider_features(
        target_date_local="2026-06-12",
        cp="20:00",
        endpoint="forecast",
        model="gfs_seamless",
        run_time_utc="2026-06-11T12:00:00Z",
        available_time_utc="2026-06-11T18:10:00Z",
        retrieved_at_utc="2026-06-11T18:15:00Z",
        response=fixture_forecast_response(),
        settled_labels=pl.DataFrame({"target_date_local": [], "label_settled_at_utc": []}),
    )

    assert set(rows["row_status"].to_list()) == {"pending"}
    assert rows["label_settled_at_utc"].null_count() == rows.height
    assert set(rows["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_forward_collection.py::test_future_target_rows_are_pending_until_labels_settle -q
```

Expected: FAIL because the forward collection module does not exist.

- [ ] **Step 3: Implement the minimal schema and pending status**

Implement `build_forward_provider_features(...)` so each normalized row includes:

```text
target_date_local, cp, cp_utc, endpoint, model, provider_family,
run_time_utc, available_time_utc, retrieved_at_utc, valid_time_utc,
horizon_hours, variable, feature_name, feature_value,
collection_key_sha256, request_url_sha256, response_sha256,
row_status, label_settled_at_utc, production_status
```

For target dates absent from `settled_labels`, set `row_status = pending`.

- [ ] **Step 4: Run the pending-row test**

Run the same focused pytest command.

Expected: PASS.

### Task 2: Available-Time Causality Gate

**Files:**
- Modify: `tests/test_open_meteo_forward_collection.py`
- Modify: `solarstorm/open_meteo/_forward_collection.py`

- [ ] **Step 1: Write failing causality tests**

Add tests proving `available_time_utc` is present on every row and rows with
`available_time_utc > cp_utc` are blocked:

```python
def test_available_time_utc_is_recorded_on_every_forward_row():
    rows = fixture_pending_forward_rows()

    assert "available_time_utc" in rows.columns
    assert rows["available_time_utc"].null_count() == 0


def test_rows_available_after_cp_are_blocked_by_causality():
    rows = build_forward_provider_features(
        target_date_local="2026-06-12",
        cp="20:00",
        endpoint="forecast",
        model="gfs_seamless",
        run_time_utc="2026-06-11T18:00:00Z",
        available_time_utc="2026-06-12T08:30:00Z",
        retrieved_at_utc="2026-06-12T08:35:00Z",
        response=fixture_forecast_response(),
        settled_labels=fixture_settled_labels("2026-06-12"),
    )

    assert set(rows["row_status"].to_list()) == {"blocked_by_causality"}
```

- [ ] **Step 2: Run the red causality tests**

Run:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_forward_collection.py::test_available_time_utc_is_recorded_on_every_forward_row tests/test_open_meteo_forward_collection.py::test_rows_available_after_cp_are_blocked_by_causality -q
```

Expected: FAIL until `available_time_utc` validation and the CP gate are
implemented.

- [ ] **Step 3: Implement the causality gate**

Convert `(target_date_local, cp)` to `cp_utc`, require non-null
`available_time_utc`, and set `row_status = blocked_by_causality` whenever
`available_time_utc > cp_utc`.

- [ ] **Step 4: Run the causality tests**

Expected: PASS.

### Task 3: Duplicate Collection Key Rejection

**Files:**
- Modify: `tests/test_open_meteo_forward_collection.py`
- Modify: `solarstorm/open_meteo/_forward_collection.py`

- [ ] **Step 1: Write the failing duplicate-key test**

Add:

```python
def test_duplicate_collection_keys_are_rejected():
    existing_manifest = pl.DataFrame(
        {
            "target_date_local": ["2026-06-12"],
            "cp": ["20:00"],
            "endpoint": ["forecast"],
            "model": ["gfs_seamless"],
            "run_time_utc": ["2026-06-11T12:00:00Z"],
        }
    )

    with pytest.raises(ValueError, match="duplicate collection key"):
        validate_new_collection_key(
            existing_manifest=existing_manifest,
            target_date_local="2026-06-12",
            cp="20:00",
            endpoint="forecast",
            model="gfs_seamless",
            run_time_utc="2026-06-11T12:00:00Z",
        )
```

- [ ] **Step 2: Run the red duplicate-key test**

Run:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_forward_collection.py::test_duplicate_collection_keys_are_rejected -q
```

Expected: FAIL because the validator does not exist.

- [ ] **Step 3: Implement duplicate-key validation**

Implement `validate_new_collection_key(...)` with exact key fields:

```text
target_date_local, cp, endpoint, model, run_time_utc
```

Raise `ValueError("duplicate collection key: ...")` when the key already
exists.

- [ ] **Step 4: Run the duplicate-key test**

Expected: PASS.

### Task 4: Raw Response Cache and Normalized Provider Features

**Files:**
- Modify: `tests/test_open_meteo_forward_collection.py`
- Modify: `solarstorm/open_meteo/_forward_collection.py`

- [ ] **Step 1: Write failing cache-metadata tests**

Add a test that writes fixture raw metadata and normalized rows to a temp
directory:

```python
def test_raw_cache_and_normalized_rows_share_response_hash(tmp_path):
    artifacts = write_forward_collection_artifacts(
        output_dir=tmp_path,
        collection_request=fixture_collection_request(),
        response_text=fixture_forecast_response_text(),
        normalized_rows=fixture_pending_forward_rows(),
    )

    raw_meta = pl.read_csv(artifacts.raw_manifest_path)
    rows = pl.read_parquet(artifacts.provider_features_path)

    assert raw_meta.row(0, named=True)["response_sha256"] == rows.row(0, named=True)["response_sha256"]
    assert set(raw_meta["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert set(rows["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [ ] **Step 2: Run the red cache test**

Run the focused test.

Expected: FAIL until artifact writing exists.

- [ ] **Step 3: Implement artifact writing**

Write:

- raw response text or JSON under `data/open_meteo_forward_raw/` or the passed
  output directory;
- `open_meteo_forward_raw_manifest_v1.csv`;
- `open_meteo_forward_provider_features_v1.parquet`;
- SHA-256 fields shared between manifest and normalized rows.

- [ ] **Step 4: Run the cache test**

Expected: PASS.

### Task 5: Maturity Transition

**Files:**
- Modify: `tests/test_open_meteo_forward_collection.py`
- Modify: `solarstorm/open_meteo/_forward_collection.py`

- [ ] **Step 1: Write failing maturity tests**

Add:

```python
def test_pending_rows_become_mature_after_labels_settle():
    pending = fixture_pending_forward_rows(target_date_local="2026-06-12")
    settled_labels = fixture_settled_labels(
        target_date_local="2026-06-12",
        label_settled_at_utc="2026-06-13T12:00:00Z",
    )

    matured = apply_forward_row_maturity(pending, settled_labels)

    assert set(matured["row_status"].to_list()) == {"mature"}
    assert matured["label_settled_at_utc"].null_count() == 0
```

- [ ] **Step 2: Run the red maturity test**

Expected: FAIL until maturity transition exists.

- [ ] **Step 3: Implement maturity transition**

Implement `apply_forward_row_maturity(...)` so only rows that are currently
`pending`, have settled labels, and pass the causality gate become `mature`.
Causality-blocked rows must stay blocked.

- [ ] **Step 4: Run the maturity test**

Expected: PASS.

### Task 6: Nested Validation Exclusion Until Mature

**Files:**
- Modify: relevant Open-Meteo nested validation test file
- Modify: relevant nested validation input/filter module

- [ ] **Step 1: Write failing validation-exclusion test**

Add a test that combines one mature and one pending forward row before building
the validation input:

```python
def test_forward_rows_do_not_enter_nested_validation_until_mature():
    forward_rows = pl.concat(
        [
            fixture_forward_row(target_date_local="2026-06-12", row_status="mature"),
            fixture_forward_row(target_date_local="2026-06-13", row_status="pending"),
        ]
    )

    eligible = filter_forward_rows_for_nested_validation(forward_rows)

    assert eligible.height == 1
    assert eligible.row(0, named=True)["target_date_local"] == "2026-06-12"
    assert set(eligible["row_status"].to_list()) == {"mature"}
```

- [ ] **Step 2: Run the red validation-exclusion test**

Run the focused nested validation test.

Expected: FAIL until the filter exists or existing validation code ignores
`row_status`.

- [ ] **Step 3: Implement the filter**

Filter forward rows to:

```text
row_status == "mature"
production_status == "EXPERIMENT_ONLY"
available_time_utc <= cp_utc
duplicate_key_status != "duplicate"
availability_status == "usable"
```

Also report excluded row counts by reason.

- [ ] **Step 4: Run the validation-exclusion test**

Expected: PASS.

### Task 7: Availability Audit by Endpoint, Model, and Horizon

**Files:**
- Modify: `tests/test_open_meteo_forward_collection.py`
- Modify: `solarstorm/open_meteo/_forward_collection.py`

- [ ] **Step 1: Write failing availability-audit test**

Add:

```python
def test_availability_audit_groups_by_endpoint_model_and_horizon():
    rows = pl.DataFrame(
        {
            "endpoint": ["forecast", "forecast", "forecast"],
            "model": ["gfs_seamless", "gfs_seamless", "ecmwf_ifs025"],
            "horizon_hours": [12, 36, 12],
            "row_status": ["mature", "blocked_by_availability", "pending"],
            "production_status": ["EXPERIMENT_ONLY"] * 3,
        }
    )

    audit = build_forward_availability_audit(rows)

    assert set(["endpoint", "model", "horizon_hours"]).issubset(audit.columns)
    assert set(audit["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert audit.filter(pl.col("row_status") == "blocked_by_availability").height == 1
```

- [ ] **Step 2: Run the red availability-audit test**

Expected: FAIL until the audit builder exists.

- [ ] **Step 3: Implement availability audit**

Aggregate counts by:

```text
endpoint, model, horizon_hours, variable, cp, target_year, target_month,
row_status
```

Include requested rows, usable rows, pending rows, blocked rows, coverage
percentage, blocker, and `production_status`.

- [ ] **Step 4: Run the availability-audit test**

Expected: PASS.

### Task 8: CLI and Reports

**Files:**
- Modify: `solarstorm/__main__.py`
- Modify: `tests/test_open_meteo_forward_collection.py` or create a CLI test

- [ ] **Step 1: Write failing CLI smoke test**

Add a fixture-mode CLI test that calls the future command without network:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-forward-collection --fixture tests/fixtures/open_meteo_forecast_fixture.json --target-date-local 2026-06-12 --cp 20:00 --model gfs_seamless --output-dir <tmp>
```

Assert it writes raw manifest, provider-feature parquet, maturity audit,
causality audit, availability audit, duplicate-key report, and a markdown
collection report.

- [ ] **Step 2: Run the red CLI smoke test**

Expected: FAIL until the CLI is wired.

- [ ] **Step 3: Implement fixture-mode CLI**

Wire a command that reads a fixture response, validates the collection key,
writes raw and normalized artifacts, and prints `production_status:
EXPERIMENT_ONLY`.

- [ ] **Step 4: Run the CLI smoke test**

Expected: PASS.

### Task 9: Verification

**Files:**
- No additional files beyond implementation, tests, and generated reports.

- [ ] **Step 1: Run focused forward-collection tests**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_forward_collection.py -q
```

Expected: PASS.

- [ ] **Step 2: Run relevant Open-Meteo validation tests**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_forward_collection.py tests/test_open_meteo_calibrated_nested.py tests/test_open_meteo_coverage_expansion.py -q
```

Expected: PASS.

- [ ] **Step 3: Run Ruff on touched code**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_forward_collection.py
```

Expected: PASS.

- [ ] **Step 4: Confirm freeze conditions**

Search generated reports and docs for:

```text
EXPERIMENT_ONLY
No production, EV, pricing, shadow trading, or execution work is unlocked.
```

Expected: both statements are present in the collection report or decision
artifact.

## Self-Review Checklist

- [ ] Spec coverage: collection key, causality gate, pending/mature lifecycle,
  duplicate rejection, raw cache, normalized provider-feature table,
  endpoint/model/horizon availability audit, validation exclusion, and freeze
  conditions are all implemented.
- [ ] Placeholder scan: no placeholder tokens or vague follow-up steps remain.
- [ ] Type consistency: timestamp, key, status, and production-status column
  names match between tests, implementation, reports, and validation filters.
