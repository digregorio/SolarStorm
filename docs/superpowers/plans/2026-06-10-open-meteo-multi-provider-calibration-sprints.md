# Open-Meteo Multi-Provider Calibration Sprints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current GFS-only Open-Meteo experiment into a causal multi-provider historical feature table, then a calibrated ensemble sequence, without changing the production baseline.

**Architecture:** Keep `data/features.parquet` and the local Onda 3F/Onda 3H baseline immutable. Add experiment-only Open-Meteo modules that first prove provider availability and causal metadata, then build a provider-keyed historical Previous Runs feature table, then measure provider-specific error/bias, then test small calibrated candidates through the existing nested-validation harness.

**Tech Stack:** Python 3.12, Polars, NumPy ridge utilities already used by `solarstorm.onda3`, Typer, pytest, Ruff, Open-Meteo fixture/live probe pattern already used in `solarstorm.open_meteo`.

---

## Current Baseline and Constraints

- Current local-data model-selection baseline: Onda 3H selected Onda 3F across outer test years 2023, 2024, and 2025.
- Current GFS-only Open-Meteo pilot source: `previous_runs_gfs_temperature`,
  endpoint `previous_runs`, model `gfs_seamless`, day-1 fixed lead. It remains
  preserved in `data/open_meteo_features.parquet` for comparison.
- Current multi-provider Open-Meteo source: provider-keyed Previous Runs rows
  in `data/open_meteo_multi_provider_features.parquet`, covering 2023-01-01
  through 2025-12-31.
- Current Open-Meteo status: `PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION` on the daily all-CP nested surface, with only one valid outer fold because Open-Meteo coverage begins in 2023.
- Current Open-Meteo is not a calibrated ensemble and must not be documented
  or modeled as one until OM-M4 creates explicit family-deduplicated candidate
  predictions and OM-M5 validates them.
- Historical Weather/reanalysis remains blocked as a causal predictor.
- Historical Forecast remains audit-only until per-row CP-causal run/lead metadata is proven.
- Forecast API is live-forward collection only for backtest purposes.
- Single Runs remains the preferred full snapshot source, but is blocked until its endpoint/model request contract succeeds.
- Every sprint below writes only `EXPERIMENT_ONLY` artifacts.

## Sprint Sequence

| Sprint | Name | Primary Question | Exit Artifact |
| --- | --- | --- | --- |
| OM-M1 | Multi-provider availability and request-contract audit | Which Open-Meteo providers/models are causally available for Wellington by date, CP, lead, and endpoint? | `reports/open-meteo-multi-provider-availability/` |
| OM-M2 | Provider error and bias atlas | What does the current causal feature table prove, and where is it still GFS-only? | `reports/open-meteo-provider-error-atlas/` |
| OM-M3 | Historical multi-provider Previous Runs feature expansion | Can the providers proven by OM-M1 be fetched and stored as causal day-1 features over the covered historical window? | `data/open_meteo_multi_provider_features.parquet`, `reports/open-meteo-multi-provider-features/` |
| OM-M4 | Family-deduplicated ensemble and bias calibration | Does calibrated multi-provider information beat raw GFS Previous Runs without overfitting? | `reports/open-meteo-provider-calibration/` |
| OM-M5 | Nested validation of calibrated candidates | Should any calibrated Open-Meteo candidate advance beyond the current GFS-only augmentation? | `reports/onda3-open-meteo-calibrated-nested-validation/` |

Implementation status on 2026-06-10:

- OM-M1 is implemented with tests and generated artifacts. Plan-only artifacts
  live under `reports/open-meteo-multi-provider-availability/`; bounded
  live-smoke artifacts live under
  `reports/open-meteo-multi-provider-availability-live-smoke/`.
- OM-M2 is implemented with tests and generated artifacts under
  `reports/open-meteo-provider-error-atlas/`. The current historical feature
  table only contains GFS Previous Runs, so the first atlas is intentionally
  GFS-only despite OM-M1 proving sampled Previous Runs availability for other
  providers.
- OM-M3 is implemented with tests and generated artifacts. It writes
  `data/open_meteo_multi_provider_features.parquet` and
  `reports/open-meteo-multi-provider-features/`. The historical table covers
  2023-01-01 through 2025-12-31, has 26,304 provider-keyed feature rows, and
  exposes six overlapping provider families on the same `(date_local, cp)`
  surface.
- The provider error atlas has been recalculated on the OM-M3 table under
  `reports/open-meteo-provider-error-atlas-multi-provider/`.
- The recalculated multi-provider atlas has 18,440 non-null provider-error
  rows and 873 metric rows. Overall raw MAE ranks `icon_seamless` best at
  1.0844 C, then `gem_global` at 1.1674 C, `ecmwf_ifs025` at 1.3987 C,
  `gfs_seamless` at 1.4207 C, `ecmwf_aifs025_single` at 1.7495 C, and
  `jma_seamless` at 1.7867 C. These numbers justify calibration experiments;
  they do not approve production use.
- OM-M4 is implemented with tests and generated artifacts under
  `reports/open-meteo-provider-calibration/`. It generated 26,224
  experiment-only candidate rows. The best calibration-table candidate is
  `om_family_recent_bias_corrected` with MAE 0.8225 C, signed bias -0.2741 C,
  and exact-bracket rate 38.41%.
- OM-M5 is implemented with tests and generated artifacts under
  `reports/onda3-open-meteo-calibrated-nested-validation/`. The strict
  common-row nested comparison includes local-only Onda 3F, current
  GFS-augmented Onda 3F, raw GFS Previous Runs, and calibrated multi-provider
  candidates. Only one outer fold is valid, so the decision is
  `KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW`.

---

### Sprint OM-M1: Multi-Provider Availability and Request-Contract Audit

**Files:**
- Create: `solarstorm/open_meteo/_multi_provider_availability.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_open_meteo_multi_provider_availability.py`
- Create: `tests/test_open_meteo_multi_provider_availability_cli.py`
- Generate: `reports/open-meteo-multi-provider-availability/`

**Scope:**
- Add a candidate model registry for Open-Meteo provider/model keys observed in the downloaded reference projects:
  `ecmwf_ifs025`, `ecmwf_aifs025_single`, `gfs_seamless`, `icon_seamless`,
  `gem_seamless`, `gem_global`, and `jma_seamless`.
- Keep regional models such as `icon_eu`, `icon_d2`, `gem_regional`, and
  `gem_hrdps_continental` in the registry as expected non-Wellington or
  likely non-covering candidates, not as assumed usable inputs.
- Probe `previous_runs` first because it already has a working Wellington path.
- Probe `single_runs` second to resolve the current request-contract blocker.
- Record endpoint, model, variable, date, CP, run time, available time, lead,
  status code, response hash, and failure reason for every probe.

- [x] **Task OM-M1.1: Write provider registry tests**

Run first:

```powershell
uv run pytest tests/test_open_meteo_multi_provider_availability.py -q
```

Expected before implementation: FAIL because the module does not exist.

Required tests:

```python
from solarstorm.open_meteo import build_multi_provider_registry


def test_multi_provider_registry_separates_global_and_regional_candidates():
    registry = build_multi_provider_registry()
    by_model = {row["model"]: row for row in registry.iter_rows(named=True)}

    assert by_model["gfs_seamless"]["provider_family"] == "NOAA_GFS"
    assert by_model["ecmwf_ifs025"]["provider_family"] == "ECMWF_IFS"
    assert by_model["ecmwf_aifs025_single"]["provider_family"] == "ECMWF_AIFS"
    assert by_model["icon_seamless"]["provider_family"] == "DWD_ICON"
    assert by_model["gem_global"]["provider_family"] == "ECCC_GEM"
    assert by_model["jma_seamless"]["provider_family"] == "JMA_GSM"
    assert by_model["icon_d2"]["coverage_expectation"] == "regional_expected_missing_for_wellington"
```

- [x] **Task OM-M1.2: Implement provider registry**

Implement `build_multi_provider_registry()` returning a Polars DataFrame with:

```text
model, provider, provider_family, endpoint_priority, coverage_expectation,
causal_role, production_status
```

All rows must use `production_status = EXPERIMENT_ONLY`.

- [x] **Task OM-M1.3: Add bounded probe plan tests**

Required behavior:

```python
from datetime import date

from solarstorm.open_meteo import build_multi_provider_probe_plan


def test_multi_provider_probe_plan_includes_previous_runs_and_single_runs():
    plan = build_multi_provider_probe_plan(
        dates=[date(2024, 7, 15)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
        endpoints=["previous_runs", "single_runs"],
    )

    assert set(plan["endpoint"].to_list()) == {"previous_runs", "single_runs"}
    assert set(plan["model"].to_list()) == {"gfs_seamless", "ecmwf_ifs025"}
    assert set(plan["cp"].to_list()) == {"20:00", "23:00"}
    assert "request_url_sha256" in plan.columns
    assert set(plan["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [x] **Task OM-M1.4: Implement bounded probe plan and CLI**

Add command:

```powershell
uv run tmax open-meteo-multi-provider-availability --dates 2024-07-15,2025-01-15 --cps 20:00,23:00 --models gfs_seamless,ecmwf_ifs025,ecmwf_aifs025_single,icon_seamless,gem_global,jma_seamless --endpoints previous_runs,single_runs
```

Expected output directory:

```text
reports/open-meteo-multi-provider-availability/
```

Expected files:

```text
open_meteo_multi_provider_registry_v1.csv
open_meteo_multi_provider_probe_plan_v1.csv
open_meteo_multi_provider_probe_results_v1.csv
open_meteo_multi_provider_availability_matrix_v1.csv
open_meteo_multi_provider_decision_update_v1.csv
open_meteo_multi_provider_availability_report_v1.md
```

- [x] **Task OM-M1.5: Run verification**

```powershell
uv run pytest tests/test_open_meteo_multi_provider_availability.py tests/test_open_meteo_multi_provider_availability_cli.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_multi_provider_availability.py tests/test_open_meteo_multi_provider_availability_cli.py
```

Exit criteria:

- The report explicitly says which providers are feature-eligible, audit-only,
  blocked by availability, blocked by request contract, or blocked by causality.
- No feature table is written in this sprint.

---

### Sprint OM-M2: Provider Error and Bias Atlas

**Files:**
- Create: `solarstorm/open_meteo/_provider_error_atlas.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_open_meteo_provider_error_atlas.py`
- Create: `tests/test_open_meteo_provider_error_atlas_cli.py`
- Generate: `reports/open-meteo-provider-error-atlas/`

**Scope:**
- Read only provider/model rows approved by OM-M1.
- Join provider predictions to observed Tmax labels on identical `(date_local, cp)` rows.
- Compute raw provider metrics before any blending or model training.
- Slice by year, month, CP, `binary_macro_regime_label`, and provider family.

- [x] **Task OM-M2.1: Write metric tests**

Required behavior:

```python
from solarstorm.open_meteo import build_provider_error_metrics


def test_provider_error_metrics_report_signed_bias_and_exact_rate(provider_fixture):
    metrics = build_provider_error_metrics(provider_fixture)
    row = metrics.filter(
        (pl.col("model") == "gfs_seamless") & (pl.col("slice_name") == "overall")
    ).row(0, named=True)

    assert row["mae"] >= 0
    assert "signed_bias" in row
    assert "rmse" in row
    assert "exact_bracket_pct" in row
    assert row["production_status"] == "EXPERIMENT_ONLY"
```

- [x] **Task OM-M2.2: Implement error atlas**

Core output columns:

```text
endpoint, model, provider_family, slice_type, slice_name, n_rows,
mae, rmse, signed_bias, exact_bracket_pct, warm_bias_pct,
cold_bias_pct, production_status
```

- [x] **Task OM-M2.3: Add regime/month/CP slices**

Required slices:

```text
overall
year
month
cp
binary_macro_regime_label
month_cp
binary_macro_regime_label_cp
```

- [x] **Task OM-M2.4: Add CLI**

Command:

```powershell
uv run tmax open-meteo-provider-error-atlas --features data/open_meteo_features.parquet --labels-path data/labels.parquet --binary-assignments-path reports/regime-design/regime_binary_macro_assignments_v1.csv --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-dir reports/open-meteo-provider-error-atlas
```

- [x] **Task OM-M2.5: Run verification**

```powershell
uv run pytest tests/test_open_meteo_provider_error_atlas.py tests/test_open_meteo_provider_error_atlas_cli.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_provider_error_atlas.py tests/test_open_meteo_provider_error_atlas_cli.py
```

Exit criteria:

- The report identifies whether any provider has a stable signed warm/cold bias
  worth calibrating.
- The report explicitly warns when a provider's slice has too few rows for
  calibration.

---

### Sprint OM-M3: Historical Multi-Provider Previous Runs Feature Expansion

**Files:**
- Create: `solarstorm/open_meteo/_multi_provider_features.py`
- Modify: `solarstorm/open_meteo/_features.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_open_meteo_multi_provider_features.py`
- Create: `tests/test_open_meteo_multi_provider_features_cli.py`
- Generate: `data/open_meteo_multi_provider_features.parquet`
- Generate: `reports/open-meteo-multi-provider-features/`

**Scope:**
- Build a historical feature table for the `previous_runs` providers that
  OM-M1 marked `OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS`.
- Preserve the existing GFS-only `data/open_meteo_features.parquet` as the
  current pilot artifact; write the new table to
  `data/open_meteo_multi_provider_features.parquet`.
- Use the same CP-to-UTC causal semantics as OM-M1. CP strings are UTC
  checkpoints in the model surface and must be converted with
  `cp_to_utc(date_local, cp, TZ_NAME)` when deriving Open-Meteo run windows.
- Store provider/model/family metadata per row so later sprints can deduplicate
  families and audit overlap.
- Do not include `single_runs` until its request contract succeeds.

- [x] **Task OM-M3.1: Write source-selection tests**

Required behavior:

```python
import polars as pl

from solarstorm.open_meteo import select_multi_provider_feature_sources


def test_select_multi_provider_feature_sources_uses_ready_previous_runs_only():
    decisions = pl.DataFrame(
        {
            "endpoint": ["previous_runs", "previous_runs", "single_runs"],
            "model": ["gfs_seamless", "ecmwf_ifs025", "gfs_seamless"],
            "provider_family": ["NOAA_GFS", "ECMWF_IFS", "NOAA_GFS"],
            "decision_status": [
                "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "BLOCK_OPEN_METEO_PROVIDER_BY_REQUEST_CONTRACT",
            ],
            "production_status": ["EXPERIMENT_ONLY"] * 3,
        }
    )

    selected = select_multi_provider_feature_sources(decisions)

    assert selected.select("endpoint").to_series().to_list() == [
        "previous_runs",
        "previous_runs",
    ]
    assert set(selected["model"].to_list()) == {"gfs_seamless", "ecmwf_ifs025"}
    assert set(selected["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [x] **Task OM-M3.2: Write feature-table contract tests**

Required behavior:

```python
from datetime import date

from solarstorm.open_meteo import build_multi_provider_previous_runs_features


def test_multi_provider_features_are_long_provider_keyed(fake_previous_runs_cache):
    features = build_multi_provider_previous_runs_features(
        cache=fake_previous_runs_cache,
        dates=[date(2024, 7, 15)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    assert {
        "date_local",
        "cp",
        "endpoint",
        "model",
        "provider_family",
        "om_provider_tmax_pred_c",
        "om_provider_run_time_utc",
        "om_provider_lead_hours",
        "production_status",
    }.issubset(features.columns)
    assert features.select(["date_local", "cp", "model"]).is_duplicated().sum() == 0
    assert set(features["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [x] **Task OM-M3.3: Implement multi-provider feature builder**

Implementation requirements:

```text
input decision file:
  reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv
input raw/cache source:
  existing Open-Meteo fetch/cache machinery, extended to accept provider model keys
output parquet:
  data/open_meteo_multi_provider_features.parquet
output report directory:
  reports/open-meteo-multi-provider-features/
minimum output columns:
  date_local, cp, endpoint, model, provider_family, provider,
  om_provider_tmax_pred_c, om_provider_run_time_utc,
  om_provider_available_time_utc, om_provider_lead_hours,
  request_url_sha256, response_sha256, source_decision_status,
  production_status
```

The builder must reject duplicate `(date_local, cp, endpoint, model)` rows and
must never overwrite `data/features.parquet`.

- [x] **Task OM-M3.4: Add CLI**

Command:

```powershell
uv run tmax open-meteo-build-multi-provider-features --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-features data/open_meteo_multi_provider_features.parquet --output-dir reports/open-meteo-multi-provider-features
```

Implemented command supports deterministic cache input and live historical
range fetching:

```powershell
uv run tmax open-meteo-build-multi-provider-features --live --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-features data/open_meteo_multi_provider_features.parquet --output-dir reports/open-meteo-multi-provider-features --date-range 2023-01-01:2025-12-31 --cps 20:00,21:00,22:00,23:00 --models gfs_seamless,ecmwf_ifs025,ecmwf_aifs025_single,icon_seamless,gem_global,jma_seamless --fetch-window-days 31 --timeout-seconds 30
```

Required CLI behavior:

```text
prints output feature path
prints provider family coverage summary
prints that all artifacts are EXPERIMENT_ONLY
exits non-zero if fewer than two provider families have overlapping rows
```

- [x] **Task OM-M3.5: Run verification**

```powershell
uv run pytest tests/test_open_meteo_multi_provider_features.py tests/test_open_meteo_multi_provider_features_cli.py -q
uv run pytest tests/test_open_meteo_features.py tests/test_open_meteo_multi_provider_availability.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_multi_provider_features.py tests/test_open_meteo_multi_provider_features_cli.py
```

Exit criteria:

- `data/open_meteo_multi_provider_features.parquet` exists and is long-format,
  provider-keyed, causal, and `EXPERIMENT_ONLY`.
- At least two provider families overlap on the same `(date_local, cp)` keys,
  or the report blocks OM-M4 by coverage instead of pretending an ensemble
  exists.
- The current GFS-only `data/open_meteo_features.parquet` remains intact for
  comparison with the earlier pilot.

---

### Sprint OM-M4: Family-Deduplicated Ensemble and Bias Calibration

**Files:**
- Create: `solarstorm/open_meteo/_provider_calibration.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_open_meteo_provider_calibration.py`
- Create: `tests/test_open_meteo_provider_calibration_cli.py`
- Generate: `reports/open-meteo-provider-calibration/`

**Scope:**
- Build candidate features from `data/open_meteo_multi_provider_features.parquet`
  only after OM-M3 proves overlapping provider-family coverage.
- Deduplicate provider families before averaging or weighting, following the
  reference pattern observed in the downloaded GitHub/quarantine projects:
  keep one representative per provider family so variants from one institution
  do not overweight that institution.
- Add signed-bias correction with shrinkage.
- Add optional regime-conditioned bias correction only when sample thresholds
  are satisfied.

- [x] **Task OM-M4.1: Write family dedup tests**

Required behavior:

```python
from solarstorm.open_meteo import collapse_provider_family_predictions


def test_collapse_provider_family_keeps_one_value_per_family():
    collapsed = collapse_provider_family_predictions(
        [
            {"model": "icon_seamless", "provider_family": "DWD_ICON", "value": 18.0},
            {"model": "icon_d2", "provider_family": "DWD_ICON", "value": 19.0},
            {"model": "gfs_seamless", "provider_family": "NOAA_GFS", "value": 17.5},
        ],
        priority=["icon_d2", "icon_seamless", "gfs_seamless"],
    )

    assert collapsed == {
        "DWD_ICON": {"model": "icon_d2", "value": 19.0},
        "NOAA_GFS": {"model": "gfs_seamless", "value": 17.5},
    }
```

- [x] **Task OM-M4.2: Re-run provider error atlas on multi-provider features**

Command:

```powershell
uv run tmax open-meteo-provider-error-atlas --features data/open_meteo_multi_provider_features.parquet --labels-path data/labels.parquet --binary-assignments-path reports/regime-design/regime_binary_macro_assignments_v1.csv --provider-decision-path reports/open-meteo-multi-provider-availability-live-smoke/open_meteo_multi_provider_decision_update_v1.csv --output-dir reports/open-meteo-provider-error-atlas-multi-provider
```

Required behavior:

```text
atlas includes one or more rows for each provider family present in OM-M3
atlas reports overlap support by provider family
calibration is blocked if only NOAA_GFS is present
all rows keep production_status = EXPERIMENT_ONLY
```

- [x] **Task OM-M4.3: Implement calibrated candidates**

Candidate IDs:

```text
om_gfs_previous_runs_raw
om_family_mean_raw
om_family_median_raw
om_family_inverse_mae_weighted
om_family_recent_bias_corrected
om_family_regime_bias_corrected
```

Each candidate row must include:

```text
date_local, cp, candidate_id, prediction, n_provider_families,
calibration_window_days, bias_adjustment, bias_samples, production_status
```

- [x] **Task OM-M4.4: Add calibration guardrails**

Guardrails:

```text
minimum overall bias samples = 30 rows
minimum regime-conditioned bias samples = 60 rows per regime
maximum absolute bias adjustment = 2.0 C
shrinkage denominator = 30 samples
fallback = raw family mean when sample thresholds fail
```

- [x] **Task OM-M4.5: Add CLI**

Command:

```powershell
uv run tmax open-meteo-provider-calibration --provider-features data/open_meteo_multi_provider_features.parquet --error-atlas-dir reports/open-meteo-provider-error-atlas-multi-provider --output-dir reports/open-meteo-provider-calibration
```

- [x] **Task OM-M4.6: Run verification**

```powershell
uv run pytest tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_provider_calibration_cli.py -q
uv run pytest tests/test_open_meteo_provider_error_atlas.py tests/test_open_meteo_multi_provider_features.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_provider_calibration_cli.py
```

Exit criteria:

- Calibrated candidates exist only for rows with causal provider coverage.
- The report shows raw versus calibrated MAE, signed bias, and exact bracket
  on validation-like historical windows.
- Any regime-conditioned correction with insufficient support is disabled and
  reported, not silently estimated.

---

### Sprint OM-M5: Nested Validation of Calibrated Open-Meteo Candidates

**Files:**
- Create: `solarstorm/open_meteo/_calibrated_nested.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_open_meteo_calibrated_nested.py`
- Create: `tests/test_open_meteo_calibrated_nested_cli.py`
- Generate: `reports/onda3-open-meteo-calibrated-nested-validation/`

**Scope:**
- Compare current local-only Onda 3F, current GFS Previous Runs augmented
  Onda 3F, and calibrated multi-provider candidates on identical covered rows.
- Use the same nested semantics as Onda 3H and the existing Open-Meteo nested
  validation: train through `Y-2`, validate on `Y-1`, test on `Y`.
- Selection rule: validation MAE, then validation final `23:00` exact rate,
  then simpler candidate.
- If OM-M3 coverage still starts in 2023 and produces only one valid outer
  fold, the result may advance only to experiment review, not to a final model
  decision.

- [x] **Task OM-M5.1: Write nested comparison tests**

Required behavior:

```python
from solarstorm.open_meteo import build_open_meteo_calibrated_nested_validation


def test_calibrated_nested_uses_identical_rows_for_all_candidates(fixture_frames):
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=fixture_frames.local_features,
        labels=fixture_frames.labels,
        open_meteo_features=fixture_frames.open_meteo_features,
        calibrated_candidates=fixture_frames.calibrated_candidates,
        test_years=[2025],
    )

    scope = artifacts["onda3_open_meteo_calibrated_nested_candidate_scope_v1"]
    assert scope["n_rows"].n_unique() == 1
    assert set(scope["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [x] **Task OM-M5.2: Implement nested comparison**

Output files:

```text
onda3_open_meteo_calibrated_nested_candidate_scope_v1.csv
onda3_open_meteo_calibrated_nested_model_results_v1.csv
onda3_open_meteo_calibrated_nested_predictions_v1.csv
onda3_open_meteo_calibrated_nested_metric_summary_v1.csv
onda3_open_meteo_calibrated_nested_selection_v1.csv
onda3_open_meteo_calibrated_nested_selected_test_summary_v1.csv
onda3_open_meteo_calibrated_nested_by_month_v1.csv
onda3_open_meteo_calibrated_nested_by_month_cp_v1.csv
onda3_open_meteo_calibrated_nested_regime_performance_v1.csv
onda3_open_meteo_calibrated_nested_decision_update_v1.csv
onda3_open_meteo_calibrated_nested_report_v1.md
```

- [x] **Task OM-M5.3: Add decision gate**

Allowed decisions:

```text
KEEP_LOCAL_ONLY_REFERENCE
KEEP_GFS_PREVIOUS_RUNS_AUGMENTATION
PROMOTE_CALIBRATED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION
KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW
BLOCK_CALIBRATED_OPEN_METEO_BY_COVERAGE
BLOCK_CALIBRATED_OPEN_METEO_BY_CAUSALITY
```

- [x] **Task OM-M5.4: Add CLI**

Command:

```powershell
uv run tmax onda3-open-meteo-calibrated-nested-validation --test-years 2024,2025 --features-path data/features.parquet --labels-path data/labels.parquet --open-meteo-features-path data/open_meteo_features.parquet --calibrated-candidates-path reports/open-meteo-provider-calibration/open_meteo_provider_calibrated_candidates_v1.parquet --binary-assignments-path reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir reports/onda3-open-meteo-calibrated-nested-validation --train-start 2012-01-01
```

- [x] **Task OM-M5.5: Run verification**

```powershell
uv run pytest tests/test_open_meteo_calibrated_nested.py tests/test_open_meteo_calibrated_nested_cli.py -q
uv run pytest tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_calibrated_nested.py tests/test_open_meteo_calibrated_nested_cli.py
```

Exit criteria:

- The report states whether calibrated Open-Meteo beats both local-only Onda 3F
  and current GFS Previous Runs augmentation on identical covered rows.
- If fewer than two valid outer folds exist, the decision must remain
  experiment-review even when metrics improve.
- No production, EV, pricing, shadow trading, or execution status is emitted.

---

## Documentation Updates Required After Each Sprint

- Update `ROADMAP.md` under the Open-Meteo integration gate.
- Update `CHANGELOG.md` under `[Unreleased] - 2026-06-10`.
- If a source becomes feature-eligible, update
  `docs/superpowers/specs/2026-06-10-open-meteo-causal-feature-integration-design.md`
  with its causal contract and limitations.
- If a source remains blocked, update the blocked-source register and explain
  whether the blocker is availability, request contract, metadata, or causality.

## Current Post-OM-M5 Direction

1. OM-M1 through OM-M5 are implemented and generated as `EXPERIMENT_ONLY`
   artifacts. Do not re-run them except to refresh provider decisions, rebuild
   provider history, or reproduce the current evidence.
2. The OM-M5 decision is
   `KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW`, not a model promotion.
   The strict common-row comparison has only one valid outer fold.
3. The next sprint should be OM-M6 forensics, not production integration:
   explain why `open_meteo_augmented_onda3f` beats
   `om_family_recent_bias_corrected` on the 2025 same-row test MAE even though
   validation selected the calibrated provider candidate.
4. Investigate coverage expansion options only if they preserve causality:
   additional fixed leads, repaired Single Runs request contract, or other
   Open-Meteo sources with per-row CP-causal metadata.
5. Keep production, EV, pricing, shadow trading, and execution blocked until a
   model has enough valid nested folds and passes predictive, uncertainty,
   causality, and coverage gates.

## Completed Sprint Cadence

- **Sprint A - OM-M4A raw family candidates:** implemented
  `_provider_calibration.py`, emitted `om_gfs_previous_runs_raw`,
  `om_family_mean_raw`, and `om_family_median_raw`, and reported coverage by
  candidate.
- **Sprint B - OM-M4B bias calibration:** implemented recent signed-bias
  correction with shrinkage and regime-conditioned correction with explicit
  fallback statuses.
- **Sprint C - OM-M4C calibration review:** generated raw and calibrated
  candidate metrics under `reports/open-meteo-provider-calibration/`.
- **Sprint D - OM-M5A nested validation:** compared local-only Onda 3F, current
  GFS-augmented Onda 3F, raw GFS Previous Runs, and calibrated candidates on
  identical covered rows.
- **Sprint E - OM-M5B documentation and decision freeze:** updated ROADMAP,
  CHANGELOG, specs, and reports; no production, EV, pricing, or execution
  claim is allowed.

## Final Verification Before Any Claim of Progress

```powershell
uv run pytest tests/test_open_meteo_availability.py tests/test_open_meteo_features.py tests/test_open_meteo_pilot.py -q
uv run pytest tests/test_open_meteo_multi_provider_availability.py tests/test_open_meteo_provider_error_atlas.py tests/test_open_meteo_multi_provider_features.py tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_calibrated_nested.py -q
uv run ruff check solarstorm/open_meteo tests
```

Expected status after OM-M5: all Open-Meteo tests pass, calibrated candidates
have experiment-only decisions, the project still has no production model
approval, and any "ensemble" claim remains limited to experiment-only evidence
from overlapping historical rows from at least two independent provider
families.
