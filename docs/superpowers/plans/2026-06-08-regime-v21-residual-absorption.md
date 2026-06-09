# Regime v2.1 Residual Absorption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a non-production Regime Ontology v2.1 screening experiment that absorbs the dead residual macro into nearest physical macros while preserving residual evidence as audit metadata.

**Architecture:** Add a focused residual-absorption module that transforms v2 assignments into v2.1 assignments and diagnostics. Extend regime validation with a v2-v2.1 comparison writer and CLI command, then refresh foundation experiment results and docs from generated artifacts. No production classifier or source feature parquet is mutated.

**Tech Stack:** Python, Polars, Typer, existing Onda2E regime validation helpers, pytest, ruff.

---

## File Structure

- Create `solarstorm/onda2e/_regime_residual_absorption.py`
  - Responsibility: build v2.1 assignment and ontology artifacts from v2 assignments, plus residual absorption diagnostics.
- Create `tests/test_regime_residual_absorption.py`
  - Responsibility: unit and writer tests for residual absorption.
- Modify `solarstorm/onda2e/_regime_design_validation.py`
  - Responsibility: compare v2 R2 with v2.1 R2 and write v2.1 validation artifacts.
- Modify `tests/test_regime_design_validation.py`
  - Responsibility: focused comparison, writer, and CLI tests.
- Modify `solarstorm/onda2e/_foundation_experiment_results.py`
  - Responsibility: accept v2.1 comparison artifacts as the preferred dead-regime evidence.
- Modify `tests/test_foundation_experiment_results.py`
  - Responsibility: regression tests for v2.1 comparison consumption.
- Modify `solarstorm/onda2e/__init__.py`
  - Responsibility: export new helpers.
- Modify `solarstorm/__main__.py`
  - Responsibility: add `regime-design-v21-validate` and optional foundation v2.1 comparison path.
- Modify `docs/decisions/012-evidence-to-decision-gate.md`, `ROADMAP.md`, and `docs/regime_model_card.md`
  - Responsibility: record generated v2.1 state and preserve Onda C as planned follow-up.

---

## Task 1: Residual Absorption Builder

**Files:**
- Create: `solarstorm/onda2e/_regime_residual_absorption.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_residual_absorption.py`

- [ ] **Step 1: Write failing test for residual reassignment**

Create `tests/test_regime_residual_absorption.py` with:

```python
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl

from solarstorm.onda2e import (
    build_regime_residual_absorption_artifacts,
    write_regime_residual_absorption_artifacts,
)


def _v2_assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 2, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "subtype_label": "subtype_maritime_cloudy",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "source_candidate_id": "RDC-V1-MONTH-2-C02",
                "component_argmax": "RDC-V1-MONTH-2-C02",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-2-C02": 0.6}),
                "family_probabilities": json.dumps(
                    {
                        "macro_light_marine_or_residual": 0.6,
                        "macro_nw_continuum": 0.3,
                        "macro_southerly_flow": 0.1,
                    }
                ),
                "component_entropy": 1.4,
                "component_margin": 0.1,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 1.2,
                "distance_to_alternative": 1.3,
                "assignment_confidence": 0.4,
                "low_confidence_flag": True,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 2, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_southerly_disrupted",
                "candidate_regime_label": "macro_southerly_flow",
                "source_candidate_id": "RDC-V1-MONTH-2-C05",
                "component_argmax": "RDC-V1-MONTH-2-C05",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-2-C05": 0.9}),
                "family_probabilities": json.dumps({"macro_southerly_flow": 0.9}),
                "component_entropy": 0.2,
                "component_margin": 0.8,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 0.2,
                "distance_to_alternative": 1.0,
                "assignment_confidence": 0.9,
                "low_confidence_flag": False,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_residual_absorption_reassigns_to_nearest_physical_macro():
    artifacts = build_regime_residual_absorption_artifacts(_v2_assignments())

    assignments = artifacts["regime_candidate_assignments_v2_1"]
    diagnostics = artifacts["regime_residual_absorption_diagnostics"]
    absorbed = assignments.filter(pl.col("absorbed_from_residual")).row(0, named=True)
    kept = assignments.filter(~pl.col("absorbed_from_residual")).row(0, named=True)

    assert assignments.height == 2
    assert absorbed["candidate_version"] == "v2.1"
    assert absorbed["macro_regime_label"] == "macro_nw_continuum"
    assert absorbed["candidate_regime_label"] == "macro_nw_continuum"
    assert absorbed["original_macro_regime_label"] == "macro_light_marine_or_residual"
    assert absorbed["original_subtype_label"] == "subtype_maritime_cloudy"
    assert "nearest physical macro" in absorbed["residual_absorption_reason"]
    assert kept["macro_regime_label"] == "macro_southerly_flow"
    assert kept["original_macro_regime_label"] == "macro_southerly_flow"
    assert set(assignments["production_status"]) == {"NOT_PRODUCTION"}
    assert diagnostics.filter(pl.col("diagnostic_item") == "invalid_absorption_targets").row(
        0,
        named=True,
    )["status"] == "PASS"
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_residual_absorption.py::test_residual_absorption_reassigns_to_nearest_physical_macro -q
```

Expected: fail because `build_regime_residual_absorption_artifacts` is not exported.

- [ ] **Step 3: Implement schemas and builder**

Create `solarstorm/onda2e/_regime_residual_absorption.py` with:

```python
"""Residual absorption artifacts for Regime Ontology v2.1."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

PHYSICAL_MACROS: tuple[str, ...] = ("macro_nw_continuum", "macro_southerly_flow")
RESIDUAL_MACRO = "macro_light_marine_or_residual"

ASSIGNMENT_V21_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "date_local": pl.Date,
    "cp": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "candidate_regime_label": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "component_argmax": pl.Utf8,
    "component_probabilities": pl.Utf8,
    "family_probabilities": pl.Utf8,
    "component_entropy": pl.Float64,
    "component_margin": pl.Float64,
    "nearest_alternative_macro": pl.Utf8,
    "distance_to_candidate": pl.Float64,
    "distance_to_alternative": pl.Float64,
    "assignment_confidence": pl.Float64,
    "low_confidence_flag": pl.Boolean,
    "original_macro_regime_label": pl.Utf8,
    "original_subtype_label": pl.Utf8,
    "absorbed_from_residual": pl.Boolean,
    "residual_absorption_reason": pl.Utf8,
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_V21_SCHEMA: dict[str, pl.DataType] = {
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "absorbed_residual_rows": pl.Int64,
    "production_status": pl.Utf8,
}

DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "diagnostic_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
    "n_rows": pl.Int64,
    "production_status": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _validate_assignments(assignments_v2: pl.DataFrame) -> None:
    required = set(ASSIGNMENT_V21_SCHEMA) - {
        "candidate_version",
        "original_macro_regime_label",
        "original_subtype_label",
        "absorbed_from_residual",
        "residual_absorption_reason",
    }
    missing = required - set(assignments_v2.columns)
    if missing:
        raise ValueError(f"assignments_v2 missing required columns: {', '.join(sorted(missing))}")
    invalid = assignments_v2.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid.height:
        raise ValueError("assignments_v2 production_status must be NOT_PRODUCTION")


def _absorb_row(row: dict[str, object]) -> dict[str, object]:
    original_macro = str(row["macro_regime_label"])
    original_subtype = str(row["subtype_label"])
    nearest = str(row.get("nearest_alternative_macro") or "")
    absorbed = original_macro == RESIDUAL_MACRO and nearest in PHYSICAL_MACROS
    invalid_target = original_macro == RESIDUAL_MACRO and nearest not in PHYSICAL_MACROS
    macro = nearest if absorbed else original_macro
    reason = (
        f"Residual macro absorbed into nearest physical macro {nearest}."
        if absorbed
        else (
            "Residual macro retained for audit because nearest alternative is invalid."
            if invalid_target
            else "Original physical macro retained."
        )
    )
    out = dict(row)
    out.update(
        {
            "candidate_version": "v2.1",
            "macro_regime_label": macro,
            "candidate_regime_label": macro,
            "original_macro_regime_label": original_macro,
            "original_subtype_label": original_subtype,
            "absorbed_from_residual": absorbed,
            "residual_absorption_reason": reason,
        }
    )
    return out


def _diagnostics(assignments: pl.DataFrame) -> pl.DataFrame:
    residual = assignments.filter(pl.col("original_macro_regime_label") == RESIDUAL_MACRO)
    invalid = residual.filter(~pl.col("macro_regime_label").is_in(PHYSICAL_MACROS))
    absorbed = assignments.filter(pl.col("absorbed_from_residual"))
    low_share = (
        float(residual.filter(pl.col("low_confidence_flag")).height / residual.height)
        if residual.height
        else 0.0
    )
    rows = [
        {
            "diagnostic_item": "residual_row_count",
            "status": "WARN" if residual.height else "PASS",
            "detail": f"{residual.height} v2 residual rows were evaluated for absorption.",
            "n_rows": residual.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "residual_low_confidence_share",
            "status": "WARN" if low_share > 0.5 else "PASS",
            "detail": f"{low_share:.6f} residual rows are low confidence.",
            "n_rows": residual.filter(pl.col("low_confidence_flag")).height if residual.height else 0,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "invalid_absorption_targets",
            "status": "PASS" if invalid.height == 0 else "FAIL",
            "detail": f"{invalid.height} residual rows lack a valid physical nearest alternative.",
            "n_rows": invalid.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "absorbed_row_count",
            "status": "PASS",
            "detail": f"{absorbed.height} residual rows were absorbed into physical macros.",
            "n_rows": absorbed.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "v21_macro_count",
            "status": "PASS",
            "detail": f"{assignments['macro_regime_label'].n_unique() if assignments.height else 0} v2.1 macros remain.",
            "n_rows": assignments["macro_regime_label"].n_unique() if assignments.height else 0,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "production_status",
            "status": "PASS" if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height == 0 else "FAIL",
            "detail": "v2.1 assignments remain NOT_PRODUCTION.",
            "n_rows": assignments.height,
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    return pl.DataFrame(rows, schema=DIAGNOSTIC_SCHEMA, strict=False)


def _ontology(assignments: pl.DataFrame) -> pl.DataFrame:
    if assignments.height == 0:
        return _empty_frame(ONTOLOGY_V21_SCHEMA)
    return (
        assignments.group_by("macro_regime_label")
        .agg(
            pl.len().alias("assignment_rows"),
            pl.col("absorbed_from_residual").sum().alias("absorbed_residual_rows"),
        )
        .with_columns(pl.lit("NOT_PRODUCTION").alias("production_status"))
        .select(list(ONTOLOGY_V21_SCHEMA))
    )


def build_regime_residual_absorption_artifacts(
    assignments_v2: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    _validate_assignments(assignments_v2)
    rows = [_absorb_row(row) for row in assignments_v2.iter_rows(named=True)]
    assignments = (
        pl.DataFrame(rows, schema=ASSIGNMENT_V21_SCHEMA, strict=False)
        if rows
        else _empty_frame(ASSIGNMENT_V21_SCHEMA)
    )
    return {
        "regime_candidate_assignments_v2_1": assignments,
        "regime_candidate_ontology_v2_1": _ontology(assignments),
        "regime_residual_absorption_diagnostics": _diagnostics(assignments),
    }
```

- [ ] **Step 4: Export builder**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_residual_absorption import (
    build_regime_residual_absorption_artifacts,
    write_regime_residual_absorption_artifacts,
)
```

Add both names to `__all__` in sorted order.

- [ ] **Step 5: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_residual_absorption.py::test_residual_absorption_reassigns_to_nearest_physical_macro -q
```

Expected: pass.

---

## Task 2: Residual Writer

**Files:**
- Modify: `solarstorm/onda2e/_regime_residual_absorption.py`
- Test: `tests/test_regime_residual_absorption.py`

- [ ] **Step 1: Write failing writer test**

Append to `tests/test_regime_residual_absorption.py`:

```python
def test_write_regime_residual_absorption_artifacts(tmp_path: Path):
    artifacts = build_regime_residual_absorption_artifacts(_v2_assignments())

    paths = write_regime_residual_absorption_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_candidate_assignments_v2_1.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v2_1.csv").exists()
    assert (tmp_path / "regime_residual_absorption_diagnostics_v1.csv").exists()
    assert (tmp_path / "regime_residual_absorption_diagnostics_v1.md").exists()
    report = paths["regime_residual_absorption_diagnostics_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Residual Absorption Diagnostics - 2026-06-08" in report
    assert "not a production classifier" in report
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_regime_residual_absorption.py::test_write_regime_residual_absorption_artifacts -q
```

Expected: fail because the writer is not implemented.

- [ ] **Step 3: Implement writer**

Add to `_regime_residual_absorption.py`:

```python
def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    assignments = artifacts["regime_candidate_assignments_v2_1"]
    diagnostics = artifacts["regime_residual_absorption_diagnostics"]
    absorbed = assignments.filter(pl.col("absorbed_from_residual")).height if assignments.height else 0
    lines = [
        f"# Regime Residual Absorption Diagnostics - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        "Regime v2.1 absorbs residual assignments into nearest physical macros for screening only.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Absorbed residual rows: {absorbed}",
        "",
        "| Diagnostic | Status | Rows | Detail |",
        "|---|---|---:|---|",
    ]
    for row in diagnostics.iter_rows(named=True):
        lines.append(
            f"| {row['diagnostic_item']} | {row['status']} | {row['n_rows']} | {row['detail']} |"
        )
    return lines


def write_regime_residual_absorption_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments_v2_1": "regime_candidate_assignments_v2_1.csv",
        "regime_candidate_ontology_v2_1": "regime_candidate_ontology_v2_1.csv",
        "regime_residual_absorption_diagnostics": "regime_residual_absorption_diagnostics_v1.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    report_path = out_dir / "regime_residual_absorption_diagnostics_v1.md"
    report_path.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")
    paths["regime_residual_absorption_diagnostics_md"] = report_path
    return paths
```

- [ ] **Step 4: Run writer test**

Run:

```powershell
uv run pytest tests/test_regime_residual_absorption.py::test_write_regime_residual_absorption_artifacts -q
```

Expected: pass.

---

## Task 3: v2-v2.1 Comparison And Validation Writer

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing comparison test**

Append to `tests/test_regime_design_validation.py`:

```python
from solarstorm.onda2e import compare_regime_candidate_v2_v21


def test_compare_regime_candidate_v2_v21_reports_absorption_decision():
    v2_r2 = pl.DataFrame(
        [
            {"regime": "macro_light_marine_or_residual", "passes": False, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )
    v21_r2 = pl.DataFrame(
        [
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )
    assignments_v21 = pl.DataFrame(
        [
            {
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "absorbed_from_residual": True,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "macro_regime_label": "macro_southerly_flow",
                "candidate_regime_label": "macro_southerly_flow",
                "absorbed_from_residual": False,
                "production_status": "NOT_PRODUCTION",
            },
        ]
    )
    diagnostics = pl.DataFrame(
        [
            {
                "diagnostic_item": "invalid_absorption_targets",
                "status": "PASS",
                "detail": "0 invalid",
                "n_rows": 0,
                "production_status": "EXPERIMENT_ONLY",
            }
        ]
    )

    artifacts = compare_regime_candidate_v2_v21(
        v2_r2=v2_r2,
        v21_r2=v21_r2,
        v21_assignments=assignments_v21,
        residual_diagnostics=diagnostics,
        v2_regimes=(
            "macro_light_marine_or_residual",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        protected_v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
    )

    comparison = artifacts["regime_candidate_v2_v21_comparison"]
    assert comparison.height == 2
    assert set(comparison["decision_update"]) == {"READY_FOR_FULL_ONDA4_RERUN"}
    assert set(comparison["v2_dead_regimes"]) == {1}
    assert set(comparison["v21_dead_regimes"]) == {0}
    assert set(comparison["production_status"]) == {"EXPERIMENT_ONLY"}
    nw = comparison.filter(pl.col("macro_regime_label") == "macro_nw_continuum").row(0, named=True)
    assert nw["absorbed_residual_rows"] == 1
```

- [ ] **Step 2: Run red comparison test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_compare_regime_candidate_v2_v21_reports_absorption_decision -q
```

Expected: fail because `compare_regime_candidate_v2_v21` is not exported.

- [ ] **Step 3: Implement comparison helper**

Add schema and helper to `_regime_design_validation.py`. Reuse existing
`_as_bool_passes`, `_r2_summary_for_regime`, and `detect_dead_regimes`.

Required public signature:

```python
def compare_regime_candidate_v2_v21(
    *,
    v2_r2: pl.DataFrame,
    v21_r2: pl.DataFrame,
    v21_assignments: pl.DataFrame,
    residual_diagnostics: pl.DataFrame,
    v2_regimes: tuple[str, ...],
    v21_regimes: tuple[str, ...],
    protected_v21_regimes: tuple[str, ...],
) -> dict[str, pl.DataFrame]:
    """Compare v2 and v2.1 macro R2 status after residual absorption."""
```

Decision logic:

```python
v2_dead = detect_dead_regimes(_as_bool_passes(v2_r2), regimes=v2_regimes)
v21_dead = detect_dead_regimes(_as_bool_passes(v21_r2), regimes=v21_regimes)
invalid_targets = residual_diagnostics.filter(
    (pl.col("diagnostic_item") == "invalid_absorption_targets")
    & (pl.col("status") == "FAIL")
).height
regressions = sorted(set(v21_dead) & set(protected_v21_regimes))
decision = (
    "READY_FOR_FULL_ONDA4_RERUN"
    if not v21_dead and not regressions and invalid_targets == 0
    else "KEEP_IN_REGIME_DESIGN_REVIEW"
)
```

Rows are one per v2.1 macro and include the columns specified in the design.

- [ ] **Step 4: Export comparison helper**

Modify `solarstorm/onda2e/__init__.py` to export
`compare_regime_candidate_v2_v21`.

- [ ] **Step 5: Run comparison test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_compare_regime_candidate_v2_v21_reports_absorption_decision -q
```

Expected: pass.

- [ ] **Step 6: Add writer test and implementation**

Add `write_regime_candidate_v21_validation_artifacts` to
`_regime_design_validation.py`. It writes:

- `regime_candidate_r2_validation_v2_1.csv`
- `regime_candidate_v2_v21_comparison.csv`
- `regime_candidate_v21_validation_report.md`

Test with a tmp directory and assert the report contains:

```text
Regime Candidate v2.1 Validation
not a production classifier
```

---

## Task 4: CLI v2.1 Validation

**Files:**
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing CLI test**

Append a test that creates small parquet features/labels and v2 assignments,
then invokes:

```powershell
regime-design-v21-validate
--features-path <features.parquet>
--labels-path <labels.parquet>
--assignments-v2-path <assignments.csv>
--r2-v2-path <v2_r2.csv>
--output-dir <tmp>
--cp-set 20:00
```

Assert:

- exit code 0;
- `regime_candidate_assignments_v2_1.csv` exists;
- `regime_candidate_r2_validation_v2_1.csv` exists;
- `regime_candidate_v2_v21_comparison.csv` exists;
- `features.parquet` is unchanged.

- [ ] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_regime_design_v21_validate_cli_writes_artifacts -q
```

Expected: fail because the command does not exist.

- [ ] **Step 3: Implement CLI command**

Add imports for:

```python
build_regime_residual_absorption_artifacts
write_regime_residual_absorption_artifacts
compare_regime_candidate_v2_v21
write_regime_candidate_v21_validation_artifacts
```

Add:

```python
@app.command("regime-design-v21-validate")
def regime_design_v21_validate(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    assignments_v2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2.csv"
    ),
    r2_v2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2.csv"
    ),
    output_dir: str = typer.Option("./reports/regime-design"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00"),
    test_start: str | None = typer.Option(None, "--test-start"),
):
    """Validate Regime Ontology v2.1 without promoting production labels."""
```

The command reads v2 assignments, builds v2.1 artifacts, runs
`validate_regime_candidate_r2` against `regime_candidate_assignments_v2_1`,
compares v2/v2.1, writes artifacts, and prints counts.

- [ ] **Step 4: Run CLI test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_regime_design_v21_validate_cli_writes_artifacts -q
```

Expected: pass.

---

## Task 5: Foundation Results Accept v2.1 Comparison

**Files:**
- Modify: `solarstorm/onda2e/_foundation_experiment_results.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_foundation_experiment_results.py`

- [ ] **Step 1: Write failing foundation test**

Add a test where `regime_candidate_v21_comparison` has:

```python
pl.DataFrame(
    [
        {
            "v2_dead_regimes": 1,
            "v21_dead_regimes": 0,
            "protected_regression_flag": False,
            "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
            "production_status": "EXPERIMENT_ONLY",
        }
    ]
)
```

Call `build_foundation_experiment_results(catalog=_catalog(), labels=labels,
candidate_assignments=assignments, regime_candidate_v21_comparison=comparison,
cp_set=("20:00",), test_starts=[dt.date(2021, 1, 1)],
test_length_days=20, min_cell_rows=2, n_bootstrap=100, run_id="test-run")`
and assert dead-regime experiment rows are `passed`, with
`decision_update = READY_FOR_FULL_ONDA4_RERUN`.

- [ ] **Step 2: Run red foundation test**

Run:

```powershell
uv run pytest tests/test_foundation_experiment_results.py::test_dead_regime_results_can_use_v21_comparison_pass -q
```

Expected: fail because the function does not accept the new parameter.

- [ ] **Step 3: Implement support**

Add optional parameter:

```python
regime_candidate_v21_comparison: pl.DataFrame | None = None
```

v2.1 comparison has priority over v2 comparison, which has priority over v1 R2.
Require `production_status = EXPERIMENT_ONLY`. A ready v2.1 comparison passes
only when `v21_dead_regimes == 0`, no protected regression is true, and
`decision_update == "READY_FOR_FULL_ONDA4_RERUN"`.

- [ ] **Step 4: Add CLI option**

Add to `foundation-experiment-results`:

```python
regime_candidate_v21_comparison_path: str | None = typer.Option(
    None,
    "--regime-candidate-v21-comparison-path",
)
```

Read the CSV when provided and pass it to `build_foundation_experiment_results`.

- [ ] **Step 5: Run foundation tests**

Run:

```powershell
uv run pytest tests/test_foundation_experiment_results.py -q
```

Expected: pass.

---

## Task 6: Generate Real v2.1 Artifacts

**Files:**
- Generated reports under `reports/regime-design/`
- Generated reports under `reports/foundation-experiments/`

- [ ] **Step 1: Run v2.1 validation command**

Run:

```powershell
uv run python -m solarstorm regime-design-v21-validate --features-path data/features.parquet --labels-path data/labels.parquet --assignments-v2-path reports/regime-design/regime_candidate_assignments_v2.csv --r2-v2-path reports/regime-design/regime_candidate_r2_validation_v2.csv --output-dir reports/regime-design
```

Expected output includes:

```text
v2.1 assignments:
absorbed residual rows:
v2.1 validation report:
```

- [ ] **Step 2: Refresh foundation results**

Run:

```powershell
uv run python -m solarstorm foundation-experiment-results --catalog-path reports/foundation-experiments/foundation_experiment_catalog_v1.csv --labels-path data/labels.parquet --assignments-path reports/regime-design/regime_candidate_assignments_v2_1.csv --regime-candidate-r2-path reports/regime-design/regime_candidate_r2_validation_v2_1.csv --regime-candidate-v21-comparison-path reports/regime-design/regime_candidate_v2_v21_comparison.csv --output-dir reports/foundation-experiments
```

Expected output includes:

```text
Foundation experiment result rows:
Results CSV:
Results Markdown:
```

- [ ] **Step 3: Audit generated artifacts**

Run:

```powershell
@'
from pathlib import Path
import csv
from collections import Counter
required = [
    "reports/regime-design/regime_residual_absorption_diagnostics_v1.csv",
    "reports/regime-design/regime_residual_absorption_diagnostics_v1.md",
    "reports/regime-design/regime_candidate_assignments_v2_1.csv",
    "reports/regime-design/regime_candidate_ontology_v2_1.csv",
    "reports/regime-design/regime_candidate_r2_validation_v2_1.csv",
    "reports/regime-design/regime_candidate_v2_v21_comparison.csv",
    "reports/regime-design/regime_candidate_v21_validation_report.md",
]
missing = [p for p in required if not Path(p).exists()]
print("missing", missing)
if missing:
    raise SystemExit(1)
for p in [
    "reports/regime-design/regime_candidate_assignments_v2_1.csv",
    "reports/regime-design/regime_candidate_v2_v21_comparison.csv",
]:
    with Path(p).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("##", p, len(rows))
    print("production_status", dict(Counter(row["production_status"] for row in rows)))
'@ | uv run python -
```

Expected: no missing files; v2.1 assignments are `NOT_PRODUCTION`; comparison is
`EXPERIMENT_ONLY`.

---

## Task 7: Documentation Updates

**Files:**
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `ROADMAP.md`
- Modify: `docs/regime_model_card.md`

- [ ] **Step 1: Update ADR-012 from generated v2.1 result**

Add a dated section with:

- v2.1 assignment rows;
- absorbed residual rows;
- v2.1 dead macro count;
- observed `decision_update`;
- explicit statement that Onda C remains planned after v2.1.

- [ ] **Step 2: Update ROADMAP**

Update the Onda 2E-Gate section with the generated v2.1 state and whether it
permits a full Onda 4 rerun. Keep Onda 3 blocked unless a full Onda 4 rerun has
already passed.

- [ ] **Step 3: Update model card**

Add the v2.1 artifact list and state that residual/maritime evidence remains an
audit/subtype layer, not a production macro.

---

## Task 8: Final Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
uv run pytest tests/test_regime_residual_absorption.py tests/test_regime_design_validation.py tests/test_foundation_experiment_results.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run full non-network suite**

Run:

```powershell
uv run pytest -q -m "not network"
```

Expected: all tests pass.

- [ ] **Step 3: Run ruff**

Run:

```powershell
uv run ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 4: Final artifact audit**

Run the audit command from Task 6 and confirm `missing []`.

---

## Parallel Execution Guidance

Use agents only with disjoint write sets:

- Agent A may implement Task 1 and Task 2 in
  `solarstorm/onda2e/_regime_residual_absorption.py` and
  `tests/test_regime_residual_absorption.py`.
- Main integrator should implement Task 3 and Task 4 because they touch shared
  validation and CLI wiring.
- Agent B may implement Task 5 in foundation experiment results only if the
  main integrator is not editing that file at the same time.
- Main integrator should execute real artifact generation, docs, and final
  verification.

Do not let multiple agents edit `solarstorm/__main__.py`,
`solarstorm/onda2e/__init__.py`, or
`solarstorm/onda2e/_regime_design_validation.py` at the same time.

## Completion Rule

The sprint is complete only when:

- v2.1 artifacts exist;
- residual rows are either absorbed into physical macros or flagged invalid;
- all artifacts remain non-production;
- foundation experiment results can reflect v2.1;
- ADR-012, ROADMAP, and model card record Onda C as the planned follow-up;
- focused tests, full non-network tests, and ruff pass.
