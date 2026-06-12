# Open-Meteo Coverage Expansion Next Sprints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the OM-M10 finding into the next measurable Open-Meteo work: prove or block a causal 2022 Previous Runs backfill, then rerun the two-fold validation surface if the backfill succeeds.

**Architecture:** Keep the current experimental baseline `open_meteo_augmented_onda3f` frozen while coverage is expanded. Use the same provider-keyed Previous Runs contract from OM-M3, then reuse existing provider atlas, calibration, nested validation, forensics, and OM-M10 coverage-audit commands on the expanded strict common-row surface.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, Ruff, existing `solarstorm.open_meteo` feature/cache builders, existing Open-Meteo Previous Runs API client.

---

## Current OM-M10 Evidence

- Current strict common-row coverage:
  - dates: 2023-01-01 through 2025-12-31
  - common dates: 1,076
  - common `(date_local, cp)` rows: 4,304
  - valid outer folds for test years 2024 and 2025: 1
- Backfill scenario:
  - causal Previous Runs history from 2022-01-01 would create two valid outer
    folds for test years 2024 and 2025.
- Single Runs:
  - 24 sampled `single_runs` probes, 0 success, 24 HTTP 400.
  - status: `BLOCKED_BY_REQUEST_CONTRACT`.
- Decision:
  - `COVERAGE_EXPANSION_REQUIRES_2022_HISTORY`.

## Sprint Sequence

| Sprint | Name | Primary Question | Measurable Exit Artifact |
| --- | --- | --- | --- |
| OM-M11 | Historical backfill feasibility | Can Previous Runs provide the missing causal 2022 rows for the same provider/CP contract as OM-M3? | `reports/open-meteo-2022-backfill-feasibility/` and optionally expanded parquet |
| OM-M12 | Two-fold nested refresh | If 2022 rows exist, do calibrated and augmented Open-Meteo candidates still behave consistently across two strict outer folds? | refreshed atlas/calibration/nested/forensics plus OM-M10 rerun showing 2 folds |
| OM-M13 | Expanded-surface decision review | Does expanded coverage change the current experimental baseline decision? | policy metrics, slices, report, and explicit decision under `reports/open-meteo-expanded-decision-review-2022-2025/` |
| OM-M14 | Forward collection design | What live-forward Forecast API protocol will accumulate future folds without leakage? | `docs/superpowers/specs/2026-06-11-open-meteo-forecast-forward-collection-design.md` and implementation plan |

## Sprint OM-M11: Historical Backfill Feasibility

Implementation status on 2026-06-11:

- OM-M11 dry-run is implemented. It writes
  `reports/open-meteo-2022-backfill-feasibility/` and records
  `OPEN_METEO_2022_BACKFILL_FEASIBILITY_READY`.
- OM-M11 live 2022 backfill is implemented. It writes
  `data/open_meteo_multi_provider_features_2022.parquet` and
  `reports/open-meteo-multi-provider-features-2022/`.
- The original `data/open_meteo_features.parquet` and
  `data/open_meteo_multi_provider_features.parquet` are preserved.

**Files:**
- Modify: `solarstorm/open_meteo/_multi_provider_features.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_open_meteo_multi_provider_features.py`
- Test: `tests/test_open_meteo_multi_provider_features_cli.py`
- Generate: `reports/open-meteo-2022-backfill-feasibility/`
- Optional generate: `data/open_meteo_multi_provider_features_2022_2025.parquet`

- [x] **Step 1: Add a failing test for 2022 dry-run feasibility**

Required behavior:

```python
def test_backfill_feasibility_reports_missing_provider_years():
    report = build_multi_provider_backfill_feasibility(
        provider_features=fixture_2023_2025_features(),
        requested_start=date(2022, 1, 1),
        requested_end=date(2025, 12, 31),
        cps=["20:00", "21:00", "22:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    assert "coverage_status" in report.columns
    assert set(report["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

Run:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_multi_provider_features.py -q
```

Expected before implementation: fail because `build_multi_provider_backfill_feasibility` does not exist.

- [x] **Step 2: Implement feasibility artifact builder**

The builder must output one row per `year, cp, model` with:

```text
year, cp, endpoint, model, provider_family, requested_dates,
observed_dates, missing_dates, coverage_pct, coverage_status,
blocker, production_status
```

Allowed `coverage_status` values:

```text
READY_FOR_BACKFILL
PARTIAL_BACKFILL_WITH_GAPS
BLOCKED_NO_OBSERVED_ROWS
BLOCKED_REQUEST_CONTRACT
```

- [x] **Step 3: Add CLI dry-run mode**

Command:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-build-multi-provider-features --date-range 2022-01-01:2025-12-31 --cps 20:00,21:00,22:00,23:00 --models gfs_seamless,ecmwf_ifs025,ecmwf_aifs025_single,icon_seamless,gem_global,jma_seamless --dry-run-feasibility --output-dir reports/open-meteo-2022-backfill-feasibility
```

Exit criterion:

- The dry-run writes a feasibility CSV and report without mutating existing
  `data/open_meteo_multi_provider_features.parquet`.

- [x] **Step 4: Run bounded live backfill only if feasibility is acceptable**

Command shape:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-build-multi-provider-features --live --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-features data/open_meteo_multi_provider_features_2022_2025.parquet --output-dir reports/open-meteo-multi-provider-features-2022-2025 --date-range 2022-01-01:2025-12-31 --cps 20:00,21:00,22:00,23:00 --models gfs_seamless,ecmwf_ifs025,ecmwf_aifs025_single,icon_seamless,gem_global,jma_seamless --fetch-window-days 31 --timeout-seconds 30
```

Exit criteria:

- No duplicate `(date_local, cp, endpoint, model)` rows.
- At least two provider families overlap in 2022.
- All rows have `production_status = EXPERIMENT_ONLY`.
- Existing `data/open_meteo_multi_provider_features.parquet` remains intact
  unless a later explicit promotion step replaces it.

## Sprint OM-M12: Two-Fold Nested Refresh

Implementation status on 2026-06-11:

- OM-M12 is generated on expanded 2022-2025 surfaces.
- Expanded inputs:
  `data/open_meteo_multi_provider_features_2022_2025.parquet` and
  `data/open_meteo_features_2022_2025.parquet`.
- Coverage audit records `CURRENT_COVERAGE_SUPPORTS_TWO_STRICT_FOLDS`.
- Defensive nested validation records
  `PROMOTE_CALIBRATED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`.

**Files:**
- Reuse: `solarstorm/open_meteo/_provider_error_atlas.py`
- Reuse: `solarstorm/open_meteo/_provider_calibration.py`
- Reuse: `solarstorm/open_meteo/_calibrated_nested.py`
- Reuse: `solarstorm/open_meteo/_forensics.py`
- Reuse: `solarstorm/open_meteo/_coverage_expansion.py`
- Generate: `reports/open-meteo-provider-error-atlas-2022-2025/`
- Generate: `reports/open-meteo-provider-calibration-2022-2025/`
- Generate: `reports/onda3-open-meteo-defensive-selection-2022-2025/`
- Generate: `reports/open-meteo-forensics-2022-2025/`
- Generate: `reports/open-meteo-coverage-expansion-2022-2025/`

- [x] **Step 1: Rerun provider atlas**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-provider-error-atlas --features data/open_meteo_multi_provider_features_2022_2025.parquet --labels-path data/labels.parquet --binary-assignments-path reports/regime-design/regime_binary_macro_assignments_v1.csv --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-dir reports/open-meteo-provider-error-atlas-2022-2025
```

- [x] **Step 2: Rerun stabilized calibration**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-provider-calibration --provider-features data/open_meteo_multi_provider_features_2022_2025.parquet --output-dir reports/open-meteo-provider-calibration-2022-2025
```

- [x] **Step 3: Rerun defensive nested validation**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax onda3-open-meteo-calibrated-nested-validation --features-path data/features.parquet --open-meteo-features-path data/open_meteo_features.parquet --calibrated-candidates-path reports/open-meteo-provider-calibration-2022-2025/open_meteo_provider_calibrated_candidates_v1.parquet --output-dir reports/onda3-open-meteo-defensive-selection-2022-2025 --test-years 2024,2025 --train-start 2012-01-01 --selection-rule validation_mae_then_non_southerly_guard_then_cp23
```

- [x] **Step 4: Rerun OM-M10 on expanded coverage**

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run tmax open-meteo-coverage-expansion --multi-provider-features-path data/open_meteo_multi_provider_features_2022_2025.parquet --calibrated-candidates-path reports/open-meteo-provider-calibration-2022-2025/open_meteo_provider_calibrated_candidates_v1.parquet --output-dir reports/open-meteo-coverage-expansion-2022-2025 --test-years 2024,2025
```

Exit criteria:

- `open_meteo_coverage_expansion_decision_v1.csv` records at least two valid
  strict common-row outer folds.
- Selection and forensics include test rows for both 2024 and 2025.
- Any candidate promotion remains `EXPERIMENT_ONLY` until a separate model
  decision gate is passed.

## Sprint OM-M13: Expanded-Surface Decision Review

**Files:**
- Create: `solarstorm/open_meteo/_expanded_decision_review.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_open_meteo_expanded_decision_review.py`
- Test: `tests/test_open_meteo_expanded_decision_review_cli.py`
- Generate: `reports/open-meteo-expanded-decision-review-2022-2025/`

- [x] **Step 1: Compare the four policy surfaces**

Compared:

```text
selected_policy
always_season
always_recent
always_augmented
```

- [x] **Step 2: Audit all required slices**

The generated slice artifact covers:

```text
year, month, CP, binary macro regime, year-regime, month-CP
```

- [x] **Step 3: Record the explicit decision**

Decision:

```text
PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION
```

Evidence:

```text
selected MAE: 0.7835
always-augmented MAE: 0.8239
selected exact delta versus augmented: +1.30 pp
best observed global policy: always-season, MAE 0.7616
```

The promotion is limited to the next experiment-only iteration. No production,
EV, pricing, shadow trading, or execution work is unlocked.

## Sprint OM-M14: Forward Collection Implementation

Implementation status on 2026-06-11:

- OM-M14 fixture-mode forward collection is implemented.
- Generated smoke artifacts live under `reports/open-meteo-forward-collection/`.
- The smoke row is `pending`, CP-causal, `EXPERIMENT_ONLY`, and excluded from
  nested validation until labels settle.

**Files:**
- Create: `solarstorm/open_meteo/_forward_collection.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_open_meteo_forward_collection.py`
- Fixture: `tests/fixtures/open_meteo_forecast_fixture.json`
- Generate: `reports/open-meteo-forward-collection/`
- Existing spec: `docs/superpowers/specs/2026-06-11-open-meteo-forecast-forward-collection-design.md`
- Existing plan: `docs/superpowers/plans/2026-06-11-open-meteo-forecast-forward-collection.md`

- [x] **Step 1: Write the spec**

The spec defines:

```text
collection key: target_date_local, cp, endpoint, model, run_time_utc
causality gate: available_time_utc <= cp_utc
storage: raw response cache plus normalized provider-feature table
maturity: pending until labels settle
availability audit: endpoint, model, horizon
```

- [x] **Step 2: Write the TDD implementation plan**

The plan includes tests proving pending/mature lifecycle, timestamp causality,
duplicate-key rejection, nested-validation exclusion, and differentiated
endpoint/model/horizon availability.

Exit criterion:

- Fixture-mode forward collection can write raw cache metadata, normalized
  provider-feature rows, maturity/causality/availability audits, duplicate-key
  report, and markdown report without relying on ambiguous historical API
  behavior. Live collection remains a separate explicit `--live` follow-up.

## Final Verification

Run after any implementation sprint:

```powershell
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run pytest tests/test_open_meteo_multi_provider_features.py tests/test_open_meteo_provider_error_atlas.py tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_calibrated_nested.py tests/test_open_meteo_coverage_expansion.py -q
$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'; uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_multi_provider_features.py tests/test_open_meteo_coverage_expansion.py
```

Expected status:

- Tests pass.
- Ruff passes.
- All generated rows remain `EXPERIMENT_ONLY`.
- Coverage decisions are based on strict common `(date_local, cp)` rows only.
