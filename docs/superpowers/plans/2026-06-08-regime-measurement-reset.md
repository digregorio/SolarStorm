# Regime Measurement Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Onda C judge regime classifiability on the causal meteorological Onda 2E matrix, with a persisted feature-basis audit, instead of falling back to arbitrary numeric model features.

**Architecture:** Reuse `_build_cluster_matrix()` and `CLUSTER_INPUT_COLUMNS` from `solarstorm/onda2e/_full_eda.py` to build the physical morning-state matrix. Add a strict selector and audit writer inside `solarstorm/onda2e/_regime_classifiability.py`, then update the CLI to rebuild the physical matrix from `features.parquet`, `labels.parquet`, and `obs.parquet`. Existing Onda C artifacts remain, with two new feature-basis audit artifacts.

**Tech Stack:** Python 3.12, Polars, NumPy, scikit-learn, Typer, pytest, ruff.

---

## File Structure

- Modify `solarstorm/onda2e/_regime_classifiability.py`
  - Add physical feature constants and audit schema.
  - Replace default unrestricted numeric fallback for physical Onda C.
  - Add `select_physical_classifiability_features()`.
  - Add `build_regime_classifiability_feature_basis_audit()`.
  - Include feature-basis audit artifacts in the build and writer.
  - Add diagnostics for physical basis validity.

- Modify `solarstorm/__main__.py`
  - Update `regime-classifiability-benchmark` with `--labels-path`, `--obs-path`, and `--basis-mode`.
  - In `physical` mode, rebuild classifiability features with `_build_cluster_matrix()`.
  - Fail fast when required physical inputs are missing.

- Modify `solarstorm/onda2e/__init__.py`
  - Export any new public classifiability helpers only if tests need package-level access.

- Modify `tests/test_regime_classifiability.py`
  - Add RED tests for strict physical feature selection.
  - Add RED tests for forbidden fallback columns.
  - Add RED tests for audit artifact generation and CLI physical-mode run.

- Generate under `reports/regime-classifiability/`
  - `regime_classifiability_feature_basis_audit_v1.csv`
  - `regime_classifiability_feature_basis_audit_v1.md`
  - regenerated Onda C CSV/MD artifacts.

---

### Task 1: Add RED Tests for Physical Feature Selection

**Files:**
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add imports for new helpers**

At the existing import block from `solarstorm.onda2e._regime_classifiability`, add:

```python
from solarstorm.onda2e._regime_classifiability import (
    build_regime_classifiability_artifacts,
    prepare_classifiability_feature_matrix,
    select_physical_classifiability_features,
    write_regime_classifiability_artifacts,
)
```

- [ ] **Step 2: Add a physical matrix fixture**

Add this helper near `_features()`:

```python
def _physical_features_with_forbidden_columns() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "drct_sin_mean": -0.1,
                "drct_cos_mean": 0.9,
                "sknt_mean": 15.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.5,
                "tmax_anomaly": 3.0,
                "remaining_warming": 2.0,
                "tmax_dminus1": 25.0,
                "foehn_score": 70.0,
                "regime_label": "strong_nw_foehn",
            },
            {
                "date_local": dt.date(2020, 1, 2),
                "cp": "20:00",
                "drct_sin_mean": 0.0,
                "drct_cos_mean": -1.0,
                "sknt_mean": 18.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum": 0.2,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp": -0.4,
                "tmax_anomaly": -2.0,
                "remaining_warming": -1.0,
                "tmax_dminus1": 22.0,
                "foehn_score": 5.0,
                "regime_label": "southerly_disrupted",
            },
        ]
    )
```

- [ ] **Step 3: Add the failing selector test**

```python
def test_physical_feature_selector_uses_only_approved_meteorological_columns():
    selected, audit = select_physical_classifiability_features(
        _physical_features_with_forbidden_columns()
    )

    assert selected == [
        "drct_sin_mean",
        "drct_cos_mean",
        "sknt_mean",
        "qnh_hpa_mean",
        "relh_mean",
        "dewpoint_depression_mean",
        "precip_pre_cp_sum",
        "cloud_cover_score_mean",
        "temp_slope_pre_cp",
    ]
    assert set(audit.get_column("production_status")) == {"EXPERIMENT_ONLY"}

    included = audit.filter(pl.col("included_in_classifiability"))
    assert set(included.get_column("feature")) == set(selected)

    rejected = audit.filter(~pl.col("included_in_classifiability"))
    rejected_by_feature = {
        row["feature"]: row for row in rejected.iter_rows(named=True)
    }
    assert rejected_by_feature["tmax_anomaly"]["leakage_class"] == "excluded_outcome"
    assert rejected_by_feature["remaining_warming"]["leakage_class"] == "excluded_outcome"
    assert rejected_by_feature["tmax_dminus1"]["leakage_class"] == "excluded_model_feature"
    assert rejected_by_feature["foehn_score"]["leakage_class"] == "excluded_quarantined_label"
    assert rejected_by_feature["regime_label"]["leakage_class"] == "excluded_quarantined_label"
```

- [ ] **Step 4: Run RED test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_physical_feature_selector_uses_only_approved_meteorological_columns -q
```

Expected: FAIL with `ImportError` or missing `select_physical_classifiability_features`.

---

### Task 2: Implement Strict Physical Feature Selector and Audit Schema

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`

- [ ] **Step 1: Add constants and schema**

Add after `DIAGNOSTICS_SCHEMA`:

```python
PHYSICAL_CLASSIFIABILITY_FEATURES: tuple[str, ...] = (
    "drct_sin_mean",
    "drct_cos_mean",
    "sknt_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp",
)

OUTCOME_FEATURE_COLUMNS = {
    "tmax_int",
    "tmax_hour",
    "remaining_warming",
    "tmax_anomaly",
}

QUARANTINED_LABEL_COLUMNS = {
    "regime_label",
    "current_regime_label",
    "regime_flags",
    "foehn_score",
    "candidate_regime_label",
    "macro_regime_label",
    "subtype_label",
}

IDENTIFIER_COLUMNS = {
    "date_local",
    "month",
    "season",
    "cp",
    "candidate_version",
    "production_status",
    "causal_window",
}

FEATURE_BASIS_AUDIT_SCHEMA = {
    "feature": pl.Utf8,
    "source": pl.Utf8,
    "included_in_classifiability": pl.Boolean,
    "required_for_physical_basis": pl.Boolean,
    "causal_availability": pl.Utf8,
    "leakage_class": pl.Utf8,
    "missing_rate": pl.Float64,
    "variance_status": pl.Utf8,
    "selection_reason": pl.Utf8,
    "production_status": pl.Utf8,
}
```

- [ ] **Step 2: Add helper functions**

Add below `_require_columns()`:

```python
def _missing_rate(frame: pl.DataFrame, column: str) -> float:
    if column not in frame.columns or frame.height == 0:
        return 1.0
    return float(frame.get_column(column).null_count() / frame.height)


def _variance_status(frame: pl.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return "missing"
    values = frame.get_column(column)
    if not values.dtype.is_numeric():
        return "non_numeric"
    if values.null_count() == values.len():
        return "all_null"
    numeric = values.drop_nulls().to_numpy().astype(float)
    if len(numeric) == 0:
        return "all_null"
    if float(np.nanstd(numeric)) <= 1e-12:
        return "constant"
    return "usable"


def _source_for_feature(column: str) -> str:
    sources = {
        "drct_sin_mean": "obs.drct",
        "drct_cos_mean": "obs.drct",
        "sknt_mean": "obs.sknt",
        "qnh_hpa_mean": "obs.alti",
        "relh_mean": "obs.relh",
        "dewpoint_depression_mean": "obs.dw_depression_c_int or tmp-dwp",
        "precip_pre_cp_sum": "obs.p01i",
        "cloud_cover_score_mean": "obs.skyc1",
        "temp_slope_pre_cp": "obs.tmp_c_int",
    }
    return sources.get(column, "inspected_input")


def _leakage_class_for_feature(column: str) -> str:
    if column in PHYSICAL_CLASSIFIABILITY_FEATURES:
        return "causal_input"
    if column in OUTCOME_FEATURE_COLUMNS:
        return "excluded_outcome"
    if column in QUARANTINED_LABEL_COLUMNS:
        return "excluded_quarantined_label"
    if column in IDENTIFIER_COLUMNS:
        return "excluded_identifier"
    return "excluded_model_feature"
```

- [ ] **Step 3: Add strict selector**

```python
def select_physical_classifiability_features(
    features: pl.DataFrame,
    *,
    min_features: int = 2,
) -> tuple[list[str], pl.DataFrame]:
    inspected = list(dict.fromkeys([*PHYSICAL_CLASSIFIABILITY_FEATURES, *features.columns]))
    rows: list[dict[str, object]] = []
    selected: list[str] = []

    for column in inspected:
        required = column in PHYSICAL_CLASSIFIABILITY_FEATURES
        leakage_class = _leakage_class_for_feature(column)
        variance_status = _variance_status(features, column)
        include = required and leakage_class == "causal_input" and variance_status == "usable"
        if include:
            selected.append(column)
        if required and column not in features.columns:
            reason = "required physical feature is missing"
        elif include:
            reason = "approved causal meteorological feature"
        elif leakage_class != "causal_input":
            reason = f"excluded by leakage class {leakage_class}"
        else:
            reason = f"excluded by variance status {variance_status}"
        rows.append(
            {
                "feature": column,
                "source": _source_for_feature(column),
                "included_in_classifiability": include,
                "required_for_physical_basis": required,
                "causal_availability": "valid < CP" if leakage_class == "causal_input" else "excluded",
                "leakage_class": leakage_class,
                "missing_rate": _missing_rate(features, column),
                "variance_status": variance_status,
                "selection_reason": reason,
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    audit = pl.DataFrame(rows, schema=FEATURE_BASIS_AUDIT_SCHEMA, strict=False)
    if len(selected) < min_features:
        raise ValueError(
            "physical classifiability basis has fewer than "
            f"{min_features} usable approved meteorological features"
        )
    return selected, audit
```

- [ ] **Step 4: Run selector test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_physical_feature_selector_uses_only_approved_meteorological_columns -q
```

Expected: PASS.

---

### Task 3: Add RED Tests for Failing Fast on Missing Physical Basis

**Files:**
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add missing-basis test**

```python
def test_physical_feature_selector_rejects_model_feature_fallback_basis():
    model_features = pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "tmax_dminus1": 20.0,
                "late_warming_anomaly": 1.5,
                "foehn_score": 80.0,
            },
            {
                "date_local": dt.date(2020, 1, 2),
                "cp": "20:00",
                "tmax_dminus1": 21.0,
                "late_warming_anomaly": 2.0,
                "foehn_score": 10.0,
            },
        ]
    )

    with pytest.raises(ValueError, match="physical classifiability basis"):
        select_physical_classifiability_features(model_features)
```

- [ ] **Step 2: Run RED/PASS check**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_physical_feature_selector_rejects_model_feature_fallback_basis -q
```

Expected after Task 2 implementation: PASS. If it fails because no exception is raised, fix `select_physical_classifiability_features()` before continuing.

---

### Task 4: Wire Strict Basis into Onda C Build

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add RED test that build artifacts includes audit and diagnostics**

```python
def test_onda_c_builds_feature_basis_audit_and_physical_diagnostics():
    res = build_regime_classifiability_artifacts(
        features=_physical_features_with_forbidden_columns().drop(
            ["tmax_anomaly", "remaining_warming", "tmax_dminus1", "foehn_score", "regime_label"]
        ),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v21(),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
    )

    assert "regime_classifiability_feature_basis_audit" in res
    audit = res["regime_classifiability_feature_basis_audit"]
    assert audit.filter(pl.col("included_in_classifiability")).height == 9

    diagnostics = res["regime_classifiability_diagnostics"]
    diagnostic_names = set(diagnostics.get_column("diagnostic_item"))
    assert "physical_feature_basis_loaded" in diagnostic_names
    assert "approved_physical_feature_count" in diagnostic_names
    assert "forbidden_numeric_fallback_not_used" in diagnostic_names
    assert "outcome_columns_excluded" in diagnostic_names
    assert "quarantined_labels_excluded" in diagnostic_names
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_builds_feature_basis_audit_and_physical_diagnostics -q
```

Expected: FAIL because build artifacts does not return `regime_classifiability_feature_basis_audit`.

- [ ] **Step 3: Modify build function**

Inside `build_regime_classifiability_artifacts()`, replace:

```python
cols = _get_numeric_features(features)
```

with:

```python
cols, feature_basis_audit = select_physical_classifiability_features(features)
```

Add diagnostics after existing `diagnostics_rows`:

```python
included_count = feature_basis_audit.filter(pl.col("included_in_classifiability")).height
outcome_included = feature_basis_audit.filter(
    pl.col("included_in_classifiability") & (pl.col("leakage_class") == "excluded_outcome")
).height
quarantined_included = feature_basis_audit.filter(
    pl.col("included_in_classifiability") & (pl.col("leakage_class") == "excluded_quarantined_label")
).height
diagnostics_rows.extend(
    [
        {
            "diagnostic_item": "physical_feature_basis_loaded",
            "status": "PASS",
            "detail": "Onda C used the approved physical meteorological feature basis.",
            "n_rows": included_count,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "approved_physical_feature_count",
            "status": "PASS" if included_count >= 2 else "FAIL",
            "detail": f"{included_count} approved physical features survived preprocessing.",
            "n_rows": included_count,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "forbidden_numeric_fallback_not_used",
            "status": "PASS",
            "detail": "Unrestricted numeric fallback is disabled for physical regime classifiability.",
            "n_rows": 0,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "outcome_columns_excluded",
            "status": "PASS" if outcome_included == 0 else "FAIL",
            "detail": f"{outcome_included} outcome columns were included.",
            "n_rows": outcome_included,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "quarantined_labels_excluded",
            "status": "PASS" if quarantined_included == 0 else "FAIL",
            "detail": f"{quarantined_included} quarantined label columns were included.",
            "n_rows": quarantined_included,
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
)
```

Add the audit to the return dict:

```python
return {
    "regime_classifiability_assignments": all_assignments,
    "regime_classifiability_metrics": metrics_df,
    "regime_classifiability_comparison": comparison_df,
    "regime_classifiability_diagnostics": diagnostics_df,
    "regime_classifiability_feature_basis_audit": feature_basis_audit,
}
```

- [ ] **Step 4: Run test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_builds_feature_basis_audit_and_physical_diagnostics -q
```

Expected: PASS.

---

### Task 5: Update Legacy Tests to Use Physical Column Names

**Files:**
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Update `_features()`**

Replace old columns:

```python
"wind_dir_deg": 350.0,
"wind_speed": 15.0,
"qnh_hpa": 1012.0,
"relh": 60.0,
"dewpoint_depression": 8.0,
"cloud_cover_score": 1.0,
```

with:

```python
"drct_sin_mean": -0.173648,
"drct_cos_mean": 0.984807,
"sknt_mean": 15.0,
"qnh_hpa_mean": 1012.0,
"relh_mean": 60.0,
"dewpoint_depression_mean": 8.0,
"cloud_cover_score_mean": 1.0,
```

For southerly rows use:

```python
"drct_sin_mean": 0.0,
"drct_cos_mean": -1.0,
"sknt_mean": 16.0,
"qnh_hpa_mean": 1007.0,
"relh_mean": 85.0,
"dewpoint_depression_mean": 2.0,
"cloud_cover_score_mean": 3.0,
```

- [ ] **Step 2: Update all synthetic feature rows**

Use `rg -n "wind_dir_deg|wind_speed|qnh_hpa\"|dewpoint_depression\"|cloud_cover_score\"" tests/test_regime_classifiability.py` and replace every classifiability fixture with physical column names. Do not change unrelated tests in other files.

- [ ] **Step 3: Run full classifiability tests**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py -q
```

Expected: all tests pass.

---

### Task 6: Write Feature-Basis Audit Artifacts

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add RED test for audit CSV/MD**

Extend `test_write_regime_classifiability_artifacts()`:

```python
assert (tmp_path / "regime_classifiability_feature_basis_audit_v1.csv").exists()
assert (tmp_path / "regime_classifiability_feature_basis_audit_v1.md").exists()

feature_basis_report = (
    tmp_path / "regime_classifiability_feature_basis_audit_v1.md"
).read_text(encoding="utf-8")
assert "Regime Classifiability Feature Basis Audit" in feature_basis_report
assert "physical" in feature_basis_report.lower()
assert "forbidden numeric fallback" in feature_basis_report.lower()
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_write_regime_classifiability_artifacts -q
```

Expected: FAIL because audit files are not written.

- [ ] **Step 3: Add markdown helper**

Add this function before `write_regime_classifiability_artifacts()`:

```python
def _feature_basis_report_lines(audit: pl.DataFrame, today: dt.date) -> list[str]:
    included = audit.filter(pl.col("included_in_classifiability"))
    fallback_attempted = False
    valid = included.height >= 2
    lines = [
        f"# Regime Classifiability Feature Basis Audit - {today.isoformat()}",
        "",
        "This audit is EXPERIMENT_ONLY and does not promote a production classifier.",
        "",
        "- Basis mode: physical",
        f"- Included approved physical features: {included.height}",
        f"- Forbidden numeric fallback attempted: {fallback_attempted}",
        f"- Valid for physical regime decisions: {valid}",
        "",
        "## Included Features",
        "",
        "| Feature | Source | Missing Rate | Variance |",
        "|---|---|---:|---|",
    ]
    for row in included.sort("feature").iter_rows(named=True):
        lines.append(
            f"| {row['feature']} | {row['source']} | "
            f"{row['missing_rate']:.4f} | {row['variance_status']} |"
        )
    lines += [
        "",
        "## Rejected Features",
        "",
        "| Feature | Leakage Class | Reason |",
        "|---|---|---|",
    ]
    rejected = audit.filter(~pl.col("included_in_classifiability"))
    for row in rejected.sort("feature").iter_rows(named=True):
        lines.append(
            f"| {row['feature']} | {row['leakage_class']} | {row['selection_reason']} |"
        )
    return lines
```

- [ ] **Step 4: Update writer**

Inside `write_regime_classifiability_artifacts()` after diagnostics write:

```python
feature_basis_audit = artifacts.get(
    "regime_classifiability_feature_basis_audit",
    pl.DataFrame(schema=FEATURE_BASIS_AUDIT_SCHEMA),
)
csv_feature_basis = out_dir / "regime_classifiability_feature_basis_audit_v1.csv"
feature_basis_audit.write_csv(csv_feature_basis)

feature_basis_report = out_dir / "regime_classifiability_feature_basis_audit_v1.md"
feature_basis_report.write_text(
    "\n".join(_feature_basis_report_lines(feature_basis_audit, report_date)),
    encoding="utf-8",
)
```

Add returned paths:

```python
"feature_basis_audit_csv": csv_feature_basis,
"feature_basis_audit_md": feature_basis_report,
```

- [ ] **Step 5: Run writer test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_write_regime_classifiability_artifacts -q
```

Expected: PASS.

---

### Task 7: Update CLI to Rebuild Physical Matrix from obs/labels/features

**Files:**
- Modify: `solarstorm/__main__.py`
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add RED CLI physical-mode test**

Add compact fixtures:

```python
def _labels_for_physical_cli() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "day_complete": True,
                "tmax_int": 25,
                "tmax_hour": 14,
                "k_cp__cp_2000": 21,
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "day_complete": True,
                "tmax_int": 18,
                "tmax_hour": 13,
                "k_cp__cp_2000": 20,
            },
        ]
    )


def _obs_for_physical_cli() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "valid": dt.datetime(2020, 1, 1, 7, 0, tzinfo=dt.UTC),
                "tmp_c_int": 20,
                "dwp_c_int": 12,
                "dw_depression_c_int": 8,
                "drct": 350.0,
                "sknt": 15.0,
                "alti": 29.90,
                "relh": 60.0,
                "p01i": 0.0,
                "skyc1": "FEW",
                "dq_tmp_c_int": "ok",
            },
            {
                "valid": dt.datetime(2022, 1, 1, 7, 0, tzinfo=dt.UTC),
                "tmp_c_int": 16,
                "dwp_c_int": 14,
                "dw_depression_c_int": 2,
                "drct": 180.0,
                "sknt": 16.0,
                "alti": 29.70,
                "relh": 85.0,
                "p01i": 0.1,
                "skyc1": "BKN",
                "dq_tmp_c_int": "ok",
            },
        ]
    )
```

Then add:

```python
def test_regime_classifiability_cli_physical_mode_writes_feature_basis_audit(tmp_path: Path):
    runner = CliRunner()
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    assignments_v2_path = tmp_path / "v2.csv"
    assignments_v21_path = tmp_path / "v21.csv"
    candidate_v2_path = tmp_path / "candidate.csv"
    comparison_v21_path = tmp_path / "comparison.csv"
    output_dir = tmp_path / "regime-classifiability"

    pl.DataFrame(
        [
            {"date_local": dt.date(2020, 1, 1), "cp": "20:00", "regime_label": "macro_nw_continuum"},
            {"date_local": dt.date(2022, 1, 1), "cp": "20:00", "regime_label": "macro_southerly_flow"},
        ]
    ).write_parquet(features_path)
    _labels_for_physical_cli().write_parquet(labels_path)
    _obs_for_physical_cli().write_parquet(obs_path)
    _assignments_v21().write_csv(assignments_v2_path)
    _assignments_v21().write_csv(assignments_v21_path)
    _candidate_v2().write_csv(candidate_v2_path)
    _comparison_v21().write_csv(comparison_v21_path)

    result = runner.invoke(
        app,
        [
            "regime-classifiability-benchmark",
            "--basis-mode",
            "physical",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--assignments-v2-path",
            str(assignments_v2_path),
            "--assignments-v21-path",
            str(assignments_v21_path),
            "--candidate-v2-path",
            str(candidate_v2_path),
            "--comparison-v21-path",
            str(comparison_v21_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2021-12-31",
            "--test-start",
            "2022-01-01",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_classifiability_feature_basis_audit_v1.csv").exists()
    audit = pl.read_csv(output_dir / "regime_classifiability_feature_basis_audit_v1.csv")
    assert audit.filter(pl.col("included_in_classifiability")).height >= 2
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_regime_classifiability_cli_physical_mode_writes_feature_basis_audit -q
```

Expected: FAIL because CLI lacks `--basis-mode`, `--labels-path`, or `--obs-path`.

- [ ] **Step 3: Update CLI imports**

In `solarstorm/__main__.py`, import:

```python
from solarstorm.onda2e._full_eda import _build_cluster_matrix
```

- [ ] **Step 4: Add CLI options**

In `regime_classifiability_benchmark()`, add:

```python
labels_path: str | None = typer.Option(
    None,
    "--labels-path",
    help="Path to labels parquet for physical feature-basis reconstruction.",
),
obs_path: str | None = typer.Option(
    None,
    "--obs-path",
    help="Path to obs parquet for physical feature-basis reconstruction.",
),
basis_mode: str = typer.Option(
    "physical",
    "--basis-mode",
    help="Feature basis mode: physical or precomputed.",
),
tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
```

- [ ] **Step 5: Rebuild physical matrix**

Replace:

```python
features = pl.read_parquet(features_path)
```

with:

```python
features_input = pl.read_parquet(features_path)
if basis_mode == "physical":
    if labels_path is None or obs_path is None:
        print("ERROR: --labels-path and --obs-path are required for physical basis mode")
        raise typer.Exit(2)
    labels_file = Path(labels_path)
    obs_file = Path(obs_path)
    if not labels_file.exists():
        print(f"ERROR: labels parquet not found: {labels_file}")
        raise typer.Exit(2)
    if not obs_file.exists():
        print(f"ERROR: obs parquet not found: {obs_file}")
        raise typer.Exit(2)
    labels_df = pl.read_parquet(labels_file)
    obs_df = pl.read_parquet(obs_file)
    features = _build_cluster_matrix(
        features_input,
        labels_df,
        obs_df,
        tz_name=tz_name,
    )
    if features.height == 0:
        print("ERROR: physical classifiability matrix is empty")
        raise typer.Exit(2)
elif basis_mode == "precomputed":
    features = features_input
else:
    print(f"ERROR: unsupported --basis-mode: {basis_mode}")
    raise typer.Exit(2)
```

- [ ] **Step 6: Run CLI physical test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_regime_classifiability_cli_physical_mode_writes_feature_basis_audit -q
```

Expected: PASS.

---

### Task 8: Preserve a Precomputed Debug Mode Without Default Fallback

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Modify: `solarstorm/__main__.py`
- Modify: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Add test for precomputed mode rejecting old names**

```python
def test_precomputed_classifiability_rejects_legacy_wind_column_names():
    legacy = _features()
    with pytest.raises(ValueError, match="physical classifiability basis"):
        build_regime_classifiability_artifacts(
            features=legacy,
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )
```

If `_features()` was updated to physical columns in Task 5, create a local `legacy` frame with `wind_dir_deg`, `wind_speed`, `qnh_hpa`, `relh`, `dewpoint_depression`, `cloud_cover_score`, and `temp_slope_pre_cp`.

- [ ] **Step 2: Run test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_precomputed_classifiability_rejects_legacy_wind_column_names -q
```

Expected: PASS after strict selector is wired.

- [ ] **Step 3: Confirm CLI default is physical**

Run:

```powershell
uv run python -m solarstorm regime-classifiability-benchmark --help
```

Expected: help text includes `--basis-mode` with default `physical`.

---

### Task 9: Generate Real Measurement Reset Artifacts

**Files:**
- Generate: `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
- Generate: `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`
- Regenerate: existing `reports/regime-classifiability/regime_classifiability_*_v1.*`

- [ ] **Step 1: Run corrected Onda C**

Run:

```powershell
uv run python -m solarstorm regime-classifiability-benchmark `
  --basis-mode physical `
  --features-path data/features.parquet `
  --labels-path data/labels.parquet `
  --obs-path data/obs.parquet `
  --assignments-v2-path reports/regime-design/regime_candidate_assignments_v2.csv `
  --assignments-v21-path reports/regime-design/regime_candidate_assignments_v2_1.csv `
  --candidate-v2-path reports/onda2e/regime_design_candidate_v2.csv `
  --comparison-v21-path reports/regime-design/regime_candidate_v2_v21_comparison.csv `
  --output-dir reports/regime-classifiability `
  --train-end 2025-12-31 `
  --test-start 2026-01-01
```

Expected:

```text
Onda C Classifiability Benchmark complete.
Written assignments: reports\regime-classifiability\regime_classifiability_assignments_v1.csv
Written metrics: reports\regime-classifiability\regime_classifiability_metrics_v1.csv
Written comparison: reports\regime-classifiability\regime_classifiability_comparison_v1.csv
Written diagnostics: reports\regime-classifiability\regime_classifiability_diagnostics_v1.csv
Written report: reports\regime-classifiability\regime_classifiability_report_v1.md
```

- [ ] **Step 2: Inspect audit artifact**

Run:

```powershell
Get-Content reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md -TotalCount 80
```

Expected:

- includes `Basis mode: physical`;
- includes at least two included approved physical features;
- says forbidden numeric fallback was not attempted.

- [ ] **Step 3: Inspect corrected Onda C decision**

Run:

```powershell
Get-Content reports/regime-classifiability/regime_classifiability_report_v1.md -TotalCount 120
```

Expected:

- report remains non-production;
- report names Onda C before Onda 3;
- report has either `READY_FOR_ONDA3_DESIGN_REVIEW` or `KEEP_IN_REGIME_DESIGN_REVIEW`;
- if still `KEEP`, next action is v2.2 design, not another blind feature probe.

---

### Task 10: Update Documentation and Gate Notes

**Files:**
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/onda4_robustness_plan.md`
- Modify: `docs/regime_model_card.md`
- Modify: `ROADMAP.md`

- [ ] **Step 1: Add ADR-012 note**

In `docs/decisions/012-evidence-to-decision-gate.md`, add a short section:

```markdown
### WCT-REGIME Measurement Reset

Onda C must use the audited physical meteorological feature basis before its
classifiability verdict can drive Onda 3 or v2.2 decisions. The required audit
artifacts are:

- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`

The unrestricted numeric fallback is not valid evidence for regime promotion.
If physical-basis Onda C fails, the next allowed action is v2.2 regime redesign
with calm/radiative restored as a candidate protected macro.
```

- [ ] **Step 2: Add robustness plan note**

In `docs/onda4_robustness_plan.md`, add:

```markdown
## Onda C Measurement Reset

The previous Onda C result is treated as non-actionable until the benchmark is
rerun on the physical meteorological basis. Onda 4/v2.1 evidence remains useful,
but Onda 3 stays blocked unless the corrected Onda C returns
`READY_FOR_ONDA3_DESIGN_REVIEW`.
```

- [ ] **Step 3: Add model-card note**

In `docs/regime_model_card.md`, add:

```markdown
## Measurement Basis Warning

Regime classifiability must be evaluated on causal meteorological inputs:
wind direction sine/cosine, wind speed, QNH, relative humidity, dewpoint
depression, rain, cloud score, and pre-CP temperature slope. Model-facing lags,
outcomes, quarantined labels, and Foehn heuristic scores are not valid as the
default physical regime benchmark basis.
```

- [ ] **Step 4: Add roadmap note**

In `ROADMAP.md`, add:

```markdown
### Current Regime Blocker

Before v2.2 or Onda 3, complete the Regime Measurement Reset. The decision
sequence is:

1. Rerun Onda C on audited physical meteorological inputs.
2. If Onda C passes, proceed to Onda 3 design review.
3. If Onda C fails on the valid physical basis, write and implement v2.2.
```

- [ ] **Step 5: Run docs grep**

Run:

```powershell
rg -n "Measurement Reset|physical meteorological|numeric fallback|v2.2" docs ROADMAP.md
```

Expected: all four docs show the new notes.

---

### Task 11: Final Verification

**Files:**
- No new code edits unless verification fails.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run broader non-network tests**

Run:

```powershell
uv run pytest -q -m "not network"
```

Expected: all non-network tests pass. Existing sklearn convergence/PCA warnings may appear only if already present.

- [ ] **Step 3: Run ruff**

Run:

```powershell
uv run ruff check solarstorm/onda2e/_regime_classifiability.py solarstorm/__main__.py tests/test_regime_classifiability.py
```

Expected:

```text
All checks passed!
```

- [ ] **Step 4: Confirm no production/model artifacts**

Run:

```powershell
Get-ChildItem -Recurse -File | Where-Object { $_.Extension -in ".pkl",".pickle",".joblib" } | Select-Object FullName
```

Expected: no new model artifact paths.

- [ ] **Step 5: Summarize actual Onda C outcome**

Open:

```powershell
Get-Content reports/regime-classifiability/regime_classifiability_report_v1.md -TotalCount 80
Get-Content reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md -TotalCount 80
```

Report:

- number of physical features included;
- Onda C verdict;
- whether Onda 3 is unblocked or v2.2 is next;
- any tests or commands that failed.

---

## Self-Review

- Spec coverage: The plan covers strict physical basis, audit artifacts, CLI physical rebuild, diagnostics, artifact generation, documentation updates, and verification.
- Placeholder scan: No `TBD`, `TODO`, or "fill in later" steps remain.
- Type consistency: Function names used consistently: `select_physical_classifiability_features`, `FEATURE_BASIS_AUDIT_SCHEMA`, `PHYSICAL_CLASSIFIABILITY_FEATURES`, `regime_classifiability_feature_basis_audit`.
- Scope check: v2.2 and Foehn physical score remain explicitly out of scope.
