# Regime Ontology v2 Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a non-production hierarchical `Regime Ontology v2` candidate that preserves Onda 2E k=6 subtype structure, validates macro-regimes against Onda 4 R2, and records whether the redesign removes the dead-regime blocker.

**Architecture:** Add focused Onda 2E modules for dead-family diagnostics and v2 candidate revision, extend the existing regime-design validation path to write v2 assignment/comparison artifacts, and extend foundation experiment results to consume v2 R2 outputs. The redesign uses a discrete macro-regime label for R2, subtype/latent-component labels for local weather-state structure, and probability/entropy/margin fields for transition evidence. All artifacts remain `NOT_PRODUCTION` or `EXPERIMENT_ONLY`.

**Tech Stack:** Python, Polars, Typer, existing Onda2e/robustness validation helpers, pytest, ruff.

---

## File Structure

- Create `solarstorm/onda2e/_regime_repair_diagnostics.py`
  - Responsibility: diagnose v1 dead families, assignment support, confidence, nearest-neighbor structure, and power warnings.
- Create `tests/test_regime_repair_diagnostics.py`
  - Responsibility: unit tests for diagnostics and writers.
- Create `solarstorm/onda2e/_regime_candidate_revision.py`
  - Responsibility: generate v2 hierarchical candidate rows from v1 candidates and diagnostics.
- Create `tests/test_regime_candidate_revision.py`
  - Responsibility: unit tests for v2 candidate generation and guardrails.
- Modify `solarstorm/onda2e/_regime_design_validation.py`
  - Responsibility: support v2 macro/subtype assignment and v1-v2 R2 comparison without mutating source features.
- Modify `tests/test_regime_design_validation.py`
  - Responsibility: tests for v2 assignment, comparison, CLI wiring, and non-production guarantees.
- Modify `solarstorm/onda2e/_foundation_experiment_results.py`
  - Responsibility: allow dead-regime foundation results to read v2 comparison/R2 artifacts.
- Modify `tests/test_foundation_experiment_results.py`
  - Responsibility: tests for v2 experiment result status and regression protection.
- Modify `solarstorm/onda2e/__init__.py`
  - Responsibility: export new public helpers.
- Modify `solarstorm/__main__.py`
  - Responsibility: add CLI entry points and options for diagnostics, candidate v2 generation, and comparative validation.
- Modify `docs/decisions/012-evidence-to-decision-gate.md`
  - Responsibility: record v2 result only after real artifacts exist.
- Modify `ROADMAP.md`
  - Responsibility: record whether Onda 4 can rerun and keep Onda 3 blocked until full Onda 4 passes.

---

## Task 1: Dead-Family Diagnostics

**Files:**
- Create: `solarstorm/onda2e/_regime_repair_diagnostics.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_repair_diagnostics.py`

- [ ] **Step 1: Write failing diagnostic test**

Create `tests/test_regime_repair_diagnostics.py` with this test:

```python
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda2e import build_regime_repair_diagnostics


def _assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "candidate_regime_label": "candidate_maritime_cloudy",
                "candidate_regime_family": "candidate_maritime_cloudy",
                "source_candidate_id": "RDC-V1-MONTH-1-C04",
                "stratum_type": "month",
                "stratum_value": "1",
                "distance_to_candidate": 1.2,
                "assignment_confidence": 0.20,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "candidate_regime_label": "candidate_nw_or_foehn",
                "candidate_regime_family": "candidate_nw_or_foehn",
                "source_candidate_id": "RDC-V1-MONTH-1-C02",
                "stratum_type": "month",
                "stratum_value": "1",
                "distance_to_candidate": 0.4,
                "assignment_confidence": 0.65,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
        ]
    )


def _r2() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H_TEST",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_nw_or_foehn",
                "hypothesis_id": "H_TEST",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "passes": True,
                "n_days": 10,
                "status": "validated",
            },
        ]
    )


def _candidate() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_id": "RDC-V1-MONTH-1-C04",
                "candidate_regime_family": "maritime_cloudy_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 40,
                "interpretability_score": 0.3,
                "physical_signature": "cloudy;light_flow",
                "wind_dir_deg_mean": 130.0,
                "wind_speed_mean": 5.0,
                "qnh_hpa_mean": 1014.0,
                "relh_mean": 90.0,
                "dewpoint_depression_mean": 1.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 4.0,
                "temp_slope_pre_cp_mean": -0.1,
                "production_status": "NOT_PRODUCTION",
            }
        ]
    )


def test_dead_family_diagnostics_report_support_confidence_and_dead_status():
    artifacts = build_regime_repair_diagnostics(
        candidate=_candidate(),
        assignments=_assignments(),
        r2_validation=_r2(),
        dead_families=("candidate_maritime_cloudy",),
        cp_set=("20:00",),
        min_support_rows=30,
    )

    diagnostics = artifacts["regime_repair_diagnostics"]
    row = diagnostics.row(0, named=True)

    assert row["candidate_regime_family"] == "candidate_maritime_cloudy"
    assert row["assignment_rows"] == 1
    assert row["r2_pass_rows"] == 0
    assert row["r2_dead_status"] == "DEAD"
    assert row["power_status"] == "UNDERPOWERED"
    assert row["production_status"] == "NOT_PRODUCTION"
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_repair_diagnostics.py::test_dead_family_diagnostics_report_support_confidence_and_dead_status -q
```

Expected: fail because `build_regime_repair_diagnostics` is not exported.

- [ ] **Step 3: Implement diagnostics schemas and helper**

Create `solarstorm/onda2e/_regime_repair_diagnostics.py` with:

```python
"""Diagnostics for Regime Ontology v2 repair candidates."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "candidate_regime_family": pl.Utf8,
    "assignment_rows": pl.Int64,
    "cp_count": pl.Int64,
    "month_count": pl.Int64,
    "mean_assignment_confidence": pl.Float64,
    "min_assignment_confidence": pl.Float64,
    "mean_distance_to_candidate": pl.Float64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "power_status": pl.Utf8,
    "recommended_repair": pl.Utf8,
    "production_status": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _recommended_repair(family: str) -> str:
    if family == "candidate_maritime_cloudy":
        return "Demote to subtype under macro_light_marine_or_residual unless support improves."
    if family == "candidate_mixed_or_transition":
        return "Replace macro family with low-confidence subtype or nearest physical macro."
    return "Retain as candidate macro only if R2 and support gates pass."


def build_regime_repair_diagnostics(
    *,
    candidate: pl.DataFrame,
    assignments: pl.DataFrame,
    r2_validation: pl.DataFrame,
    dead_families: tuple[str, ...] = (
        "candidate_maritime_cloudy",
        "candidate_mixed_or_transition",
    ),
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    min_support_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    if not dead_families:
        return {"regime_repair_diagnostics": _empty_frame(DIAGNOSTIC_SCHEMA)}
    required_assignment = {
        "date_local",
        "cp",
        "candidate_regime_family",
        "assignment_confidence",
        "distance_to_candidate",
        "production_status",
    }
    missing_assignment = required_assignment - set(assignments.columns)
    if missing_assignment:
        raise ValueError(
            "assignments missing required columns: "
            f"{', '.join(sorted(missing_assignment))}"
        )
    required_r2 = {"regime", "passes", "cp"}
    missing_r2 = required_r2 - set(r2_validation.columns)
    if missing_r2:
        raise ValueError(
            "r2_validation missing required columns: "
            f"{', '.join(sorted(missing_r2))}"
        )
    if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("assignments must remain NOT_PRODUCTION")

    scoped_assignments = assignments.filter(pl.col("cp").is_in(cp_set))
    rows: list[dict[str, object]] = []
    for family in dead_families:
        fam_assignments = scoped_assignments.filter(
            pl.col("candidate_regime_family") == family
        )
        fam_r2 = r2_validation.filter(pl.col("regime") == family)
        assignment_rows = fam_assignments.height
        r2_pass_rows = (
            fam_r2.filter(pl.col("passes").cast(pl.Boolean, strict=False)).height
            if fam_r2.height
            else 0
        )
        rows.append(
            {
                "candidate_regime_family": family,
                "assignment_rows": assignment_rows,
                "cp_count": (
                    fam_assignments.get_column("cp").n_unique()
                    if assignment_rows
                    else 0
                ),
                "month_count": (
                    fam_assignments.get_column("date_local").dt.month().n_unique()
                    if assignment_rows
                    else 0
                ),
                "mean_assignment_confidence": (
                    float(fam_assignments["assignment_confidence"].mean())
                    if assignment_rows
                    else None
                ),
                "min_assignment_confidence": (
                    float(fam_assignments["assignment_confidence"].min())
                    if assignment_rows
                    else None
                ),
                "mean_distance_to_candidate": (
                    float(fam_assignments["distance_to_candidate"].mean())
                    if assignment_rows
                    else None
                ),
                "r2_rows": fam_r2.height,
                "r2_pass_rows": r2_pass_rows,
                "r2_dead_status": "PASS" if r2_pass_rows > 0 else "DEAD",
                "power_status": (
                    "PASS" if assignment_rows >= min_support_rows else "UNDERPOWERED"
                ),
                "recommended_repair": _recommended_repair(family),
                "production_status": "NOT_PRODUCTION",
            }
        )
    return {
        "regime_repair_diagnostics": pl.DataFrame(
            rows,
            schema=DIAGNOSTIC_SCHEMA,
            strict=False,
        )
    }
```

- [ ] **Step 4: Export helper**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_repair_diagnostics import (
    build_regime_repair_diagnostics,
)
```

Add `"build_regime_repair_diagnostics"` to `__all__`.

- [ ] **Step 5: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_repair_diagnostics.py -q
```

Expected: pass.

---

## Task 2: Diagnostics Writers And CLI

**Files:**
- Modify: `solarstorm/onda2e/_regime_repair_diagnostics.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_repair_diagnostics.py`

- [ ] **Step 1: Write failing writer test**

Append to `tests/test_regime_repair_diagnostics.py`:

```python
from pathlib import Path

from solarstorm.onda2e import write_regime_repair_diagnostics_artifacts


def test_write_regime_repair_diagnostics_artifacts(tmp_path: Path):
    artifacts = build_regime_repair_diagnostics(
        candidate=_candidate(),
        assignments=_assignments(),
        r2_validation=_r2(),
        dead_families=("candidate_maritime_cloudy",),
        cp_set=("20:00",),
        min_support_rows=30,
    )

    paths = write_regime_repair_diagnostics_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "regime_repair_diagnostics_v1.csv").exists()
    assert (tmp_path / "regime_repair_diagnostics_v1.md").exists()
    report = paths["regime_repair_diagnostics_md"].read_text(encoding="utf-8")
    assert "Regime Repair Diagnostics - 2026-06-07" in report
    assert "candidate_maritime_cloudy" in report
    assert "NOT_PRODUCTION" in report
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_regime_repair_diagnostics.py::test_write_regime_repair_diagnostics_artifacts -q
```

Expected: fail because writer is not exported.

- [ ] **Step 3: Implement writer**

Add to `solarstorm/onda2e/_regime_repair_diagnostics.py`:

```python
def _md(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "/")


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    diagnostics = artifacts["regime_repair_diagnostics"]
    lines = [
        f"# Regime Repair Diagnostics - {today.isoformat()}",
        "",
        "Diagnostic artifact only. This does not promote a regime classifier.",
        "",
        f"- Diagnostic rows: {diagnostics.height}",
        "",
        "| Family | R2 | Assignments | Power | Mean confidence | Production | Recommendation |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for row in diagnostics.sort("candidate_regime_family").iter_rows(named=True):
        lines.append(
            "| "
            f"{_md(row['candidate_regime_family'])} | "
            f"{_md(row['r2_dead_status'])} | "
            f"{row['assignment_rows']} | "
            f"{_md(row['power_status'])} | "
            f"{row['mean_assignment_confidence'] if row['mean_assignment_confidence'] is not None else ''} | "
            f"{_md(row['production_status'])} | "
            f"{_md(row['recommended_repair'])} |"
        )
    return lines


def write_regime_repair_diagnostics_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    csv_path = out_dir / "regime_repair_diagnostics_v1.csv"
    md_path = out_dir / "regime_repair_diagnostics_v1.md"
    artifacts["regime_repair_diagnostics"].write_csv(csv_path)
    md_path.write_text(
        "\n".join(_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    return {
        "regime_repair_diagnostics_csv": csv_path,
        "regime_repair_diagnostics_md": md_path,
    }
```

- [ ] **Step 4: Export writer**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_repair_diagnostics import (
    build_regime_repair_diagnostics,
    write_regime_repair_diagnostics_artifacts,
)
```

Add `"write_regime_repair_diagnostics_artifacts"` to `__all__`.

- [ ] **Step 5: Add CLI command**

Modify `solarstorm/__main__.py` imports:

```python
from solarstorm.onda2e import (
    build_regime_repair_diagnostics,
    write_regime_repair_diagnostics_artifacts,
)
```

Add command:

```python
@app.command("regime-repair-diagnostics")
def regime_repair_diagnostics(
    candidate_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v1.csv",
        help="Path to regime design candidate CSV",
    ),
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v1.csv",
        help="Path to regime candidate assignments CSV",
    ),
    r2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation.csv",
        help="Path to candidate R2 validation CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for diagnostics artifacts",
    ),
):
    """Diagnose dead candidate regime families before v2 redesign."""
    candidate_file = Path(candidate_path)
    assignments_file = Path(assignments_path)
    r2_file = Path(r2_path)
    for path, label in (
        (candidate_file, "candidate"),
        (assignments_file, "assignments"),
        (r2_file, "candidate R2 validation"),
    ):
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            raise typer.Exit(2)

    artifacts = build_regime_repair_diagnostics(
        candidate=pl.read_csv(candidate_file),
        assignments=pl.read_csv(assignments_file),
        r2_validation=pl.read_csv(r2_file),
    )
    paths = write_regime_repair_diagnostics_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    diagnostics = artifacts["regime_repair_diagnostics"]
    print(f"Regime repair diagnostic rows: {diagnostics.height}")
    print(f"Diagnostics CSV: {paths['regime_repair_diagnostics_csv']}")
    print(f"Diagnostics Markdown: {paths['regime_repair_diagnostics_md']}")
```

- [ ] **Step 6: Run diagnostics tests**

Run:

```powershell
uv run pytest tests/test_regime_repair_diagnostics.py -q
```

Expected: pass.

---

## Task 3: Candidate v2 Revision Builder

**Files:**
- Create: `solarstorm/onda2e/_regime_candidate_revision.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_candidate_revision.py`

- [ ] **Step 1: Write failing v2 candidate test**

Create `tests/test_regime_candidate_revision.py`:

```python
from __future__ import annotations

import polars as pl

from solarstorm.onda2e import build_regime_design_candidate_v2


def _candidate_v1() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v1",
                "candidate_id": "RDC-V1-MONTH-1-C00",
                "candidate_regime_family": "nw_or_foehn_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 100,
                "interpretability_score": 0.6,
                "physical_signature": "northerly_nw_flow;dry_air",
                "wind_dir_deg_mean": 310.0,
                "wind_speed_mean": 12.0,
                "qnh_hpa_mean": 1008.0,
                "relh_mean": 55.0,
                "dewpoint_depression_mean": 7.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp_mean": 0.2,
                "dominant_current_regime": "standard_nw",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v1",
                "candidate_id": "RDC-V1-MONTH-1-C01",
                "candidate_regime_family": "mixed_or_transition",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 12,
                "interpretability_score": 0.2,
                "physical_signature": "mixed_transition",
                "wind_dir_deg_mean": 180.0,
                "wind_speed_mean": 3.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 75.0,
                "dewpoint_depression_mean": 3.0,
                "precip_pre_cp_sum_mean": 0.2,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp_mean": -0.1,
                "dominant_current_regime": "southerly_disrupted",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v1",
                "candidate_id": "RDC-V1-MONTH-1-C02",
                "candidate_regime_family": "maritime_cloudy_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 10,
                "interpretability_score": 0.3,
                "physical_signature": "cloudy;light_flow",
                "wind_dir_deg_mean": 130.0,
                "wind_speed_mean": 5.0,
                "qnh_hpa_mean": 1014.0,
                "relh_mean": 90.0,
                "dewpoint_depression_mean": 1.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 4.0,
                "temp_slope_pre_cp_mean": -0.1,
                "dominant_current_regime": "calm_radiative",
                "production_status": "NOT_PRODUCTION",
            },
        ]
    )


def test_candidate_v2_maps_dead_families_to_subtypes_not_macro_regimes():
    artifacts = build_regime_design_candidate_v2(_candidate_v1())

    candidate_v2 = artifacts["regime_design_candidate_v2"]
    macros = set(candidate_v2.get_column("macro_regime_label"))
    subtypes = set(candidate_v2.get_column("subtype_label"))

    assert "macro_nw_continuum" in macros
    assert "candidate_mixed_or_transition" not in macros
    assert "candidate_maritime_cloudy" not in macros
    assert "subtype_transition_low_confidence" in subtypes
    assert "subtype_maritime_cloudy" in subtypes
    assert candidate_v2.filter(pl.col("candidate_id") == "RDC-V2-0001").row(
        0,
        named=True,
    )["wind_speed_mean"] == 12.0
    assert set(candidate_v2.get_column("production_status")) == {"NOT_PRODUCTION"}
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_candidate_revision.py::test_candidate_v2_maps_dead_families_to_subtypes_not_macro_regimes -q
```

Expected: fail because `build_regime_design_candidate_v2` is not exported.

- [ ] **Step 3: Implement v2 candidate builder**

Create `solarstorm/onda2e/_regime_candidate_revision.py`:

```python
"""Build non-production Regime Ontology v2 candidates."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

V2_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "candidate_id": pl.Utf8,
    "source_candidate_ids": pl.Utf8,
    "source_strategy": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "latent_component_id": pl.Utf8,
    "component_family_prior": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "n_source_rows": pl.Int64,
    "mean_interpretability_score": pl.Float64,
    "physical_signature": pl.Utf8,
    "wind_dir_deg_mean": pl.Float64,
    "wind_speed_mean": pl.Float64,
    "qnh_hpa_mean": pl.Float64,
    "relh_mean": pl.Float64,
    "dewpoint_depression_mean": pl.Float64,
    "precip_pre_cp_sum_mean": pl.Float64,
    "cloud_cover_score_mean": pl.Float64,
    "temp_slope_pre_cp_mean": pl.Float64,
    "dominant_current_regime": pl.Utf8,
    "design_rationale": pl.Utf8,
    "causal_inputs": pl.Utf8,
    "production_status": pl.Utf8,
    "next_gate_action": pl.Utf8,
}

CAUSAL_INPUTS = (
    "wind_dir_sin_mean;wind_dir_cos_mean;wind_speed_mean;qnh_hpa_mean;"
    "relh_mean;dewpoint_depression_mean;precip_pre_cp_sum_mean;"
    "cloud_cover_score_mean;temp_slope_pre_cp_mean"
)


def _optional_float(row: dict[str, object], column: str) -> float | None:
    value = row.get(column)
    if value is None:
        return None
    return float(value)


def _macro_and_subtype(family: str, signature: str) -> tuple[str, str, str, str]:
    family_text = family.removesuffix("_candidate")
    signature_text = signature.lower()
    if family_text in {"nw_or_foehn", "strong_nw_foehn"}:
        subtype = "subtype_foehn_nw" if "dry" in signature_text else "subtype_standard_nw"
        return (
            "macro_nw_continuum",
            subtype,
            "subtype_preserve",
            "NW and foehn evidence is retained as a supported macro with local subtypes.",
        )
    if family_text in {"southerly_disrupted", "cooling_disruption"}:
        subtype = (
            "subtype_frontal_southerly"
            if "southerly" in signature_text
            else "subtype_postfrontal_southerly"
        )
        return (
            "macro_southerly_flow",
            subtype,
            "subtype_preserve",
            "Southerly evidence is retained as a supported macro with local subtypes.",
        )
    if family_text == "maritime_cloudy":
        return (
            "macro_light_marine_or_residual",
            "subtype_maritime_cloudy",
            "dead_family_absorb",
            "Maritime/cloudy is too sparse as a macro in v1 and is demoted to subtype.",
        )
    if family_text == "mixed_or_transition":
        return (
            "macro_light_marine_or_residual",
            "subtype_transition_low_confidence",
            "low_confidence_subtype",
            "Mixed/transition is boundary evidence and cannot be a macro regime.",
        )
    return (
        "macro_light_marine_or_residual",
        "subtype_calm_radiative",
        "macro_merge",
        "Residual light-flow evidence is grouped under the light/marine macro.",
    )


def build_regime_design_candidate_v2(candidate_v1: pl.DataFrame) -> dict[str, pl.DataFrame]:
    required = {
        "candidate_id",
        "candidate_regime_family",
        "stratum_type",
        "stratum_value",
        "n_rows",
        "interpretability_score",
        "physical_signature",
        "wind_dir_deg_mean",
        "wind_speed_mean",
        "qnh_hpa_mean",
        "relh_mean",
        "dewpoint_depression_mean",
        "precip_pre_cp_sum_mean",
        "cloud_cover_score_mean",
        "temp_slope_pre_cp_mean",
        "dominant_current_regime",
        "production_status",
    }
    missing = required - set(candidate_v1.columns)
    if missing:
        raise ValueError(
            "candidate_v1 missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    if candidate_v1.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("candidate_v1 must remain NOT_PRODUCTION")

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(candidate_v1.iter_rows(named=True), start=1):
        macro, subtype, strategy, rationale = _macro_and_subtype(
            str(row["candidate_regime_family"]),
            str(row.get("physical_signature") or ""),
        )
        rows.append(
            {
                "candidate_version": "v2",
                "candidate_id": f"RDC-V2-{idx:04d}",
                "source_candidate_ids": str(row["candidate_id"]),
                "source_strategy": strategy,
                "macro_regime_label": macro,
                "subtype_label": subtype,
                "latent_component_id": f"{macro}:{subtype}:{row['stratum_type']}:{row['stratum_value']}",
                "component_family_prior": macro,
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "n_source_rows": int(row.get("n_rows") or 0),
                "mean_interpretability_score": float(row.get("interpretability_score") or 0.0),
                "physical_signature": str(row.get("physical_signature") or ""),
                "wind_dir_deg_mean": _optional_float(row, "wind_dir_deg_mean"),
                "wind_speed_mean": _optional_float(row, "wind_speed_mean"),
                "qnh_hpa_mean": _optional_float(row, "qnh_hpa_mean"),
                "relh_mean": _optional_float(row, "relh_mean"),
                "dewpoint_depression_mean": _optional_float(row, "dewpoint_depression_mean"),
                "precip_pre_cp_sum_mean": _optional_float(row, "precip_pre_cp_sum_mean"),
                "cloud_cover_score_mean": _optional_float(row, "cloud_cover_score_mean"),
                "temp_slope_pre_cp_mean": _optional_float(row, "temp_slope_pre_cp_mean"),
                "dominant_current_regime": str(row.get("dominant_current_regime") or ""),
                "design_rationale": rationale,
                "causal_inputs": CAUSAL_INPUTS,
                "production_status": "NOT_PRODUCTION",
                "next_gate_action": "Validate v2 macro regimes with candidate R2 screening.",
            }
        )
    return {
        "regime_design_candidate_v2": pl.DataFrame(
            rows,
            schema=V2_SCHEMA,
            strict=False,
        )
    }
```

- [ ] **Step 4: Export builder**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_candidate_revision import (
    build_regime_design_candidate_v2,
)
```

Add `"build_regime_design_candidate_v2"` to `__all__`.

- [ ] **Step 5: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_candidate_revision.py -q
```

Expected: pass.

---

## Task 4: Candidate v2 Writers And CLI

**Files:**
- Modify: `solarstorm/onda2e/_regime_candidate_revision.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_candidate_revision.py`

- [ ] **Step 1: Write failing writer test**

Append:

```python
from pathlib import Path

from solarstorm.onda2e import write_regime_design_candidate_v2_artifacts


def test_write_regime_design_candidate_v2_artifacts(tmp_path: Path):
    artifacts = build_regime_design_candidate_v2(_candidate_v1())

    paths = write_regime_design_candidate_v2_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "regime_design_candidate_v2.csv").exists()
    assert (tmp_path / "regime_design_candidate_v2.md").exists()
    report = paths["regime_design_candidate_v2_md"].read_text(encoding="utf-8")
    assert "Regime Design Candidate v2 - 2026-06-07" in report
    assert "macro_nw_continuum" in report
    assert "NOT_PRODUCTION" in report
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_regime_candidate_revision.py::test_write_regime_design_candidate_v2_artifacts -q
```

Expected: fail because writer is not exported.

- [ ] **Step 3: Implement writer**

Add to `_regime_candidate_revision.py`:

```python
def _md(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "/")


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    candidate = artifacts["regime_design_candidate_v2"]
    lines = [
        f"# Regime Design Candidate v2 - {today.isoformat()}",
        "",
        "This is a non-production hierarchical regime ontology candidate.",
        "",
        f"- Candidate rows: {candidate.height}",
        f"- Macro regimes: {candidate['macro_regime_label'].n_unique() if candidate.height else 0}",
        "",
        "| Macro | Subtype | Rows | Strategy | Production |",
        "|---|---|---:|---|---|",
    ]
    for row in candidate.sort(["macro_regime_label", "subtype_label"]).iter_rows(named=True):
        lines.append(
            "| "
            f"{_md(row['macro_regime_label'])} | "
            f"{_md(row['subtype_label'])} | "
            f"{row['n_source_rows']} | "
            f"{_md(row['source_strategy'])} | "
            f"{_md(row['production_status'])} |"
        )
    return lines


def write_regime_design_candidate_v2_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    csv_path = out_dir / "regime_design_candidate_v2.csv"
    md_path = out_dir / "regime_design_candidate_v2.md"
    artifacts["regime_design_candidate_v2"].write_csv(csv_path)
    md_path.write_text(
        "\n".join(_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    return {
        "regime_design_candidate_v2_csv": csv_path,
        "regime_design_candidate_v2_md": md_path,
    }
```

- [ ] **Step 4: Export writer**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_candidate_revision import (
    build_regime_design_candidate_v2,
    write_regime_design_candidate_v2_artifacts,
)
```

Add `"write_regime_design_candidate_v2_artifacts"` to `__all__`.

- [ ] **Step 5: Add CLI command**

Modify `solarstorm/__main__.py` imports:

```python
from solarstorm.onda2e import (
    build_regime_design_candidate_v2,
    write_regime_design_candidate_v2_artifacts,
)
```

Add command:

```python
@app.command("regime-candidate-v2")
def regime_candidate_v2(
    candidate_v1_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v1.csv",
        help="Path to regime design candidate v1 CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/onda2e",
        help="Output directory for candidate v2 artifacts",
    ),
):
    """Build non-production Regime Ontology v2 candidate artifacts."""
    candidate_file = Path(candidate_v1_path)
    if not candidate_file.exists():
        print(f"ERROR: candidate v1 file not found: {candidate_file}")
        raise typer.Exit(2)
    artifacts = build_regime_design_candidate_v2(pl.read_csv(candidate_file))
    paths = write_regime_design_candidate_v2_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    candidate = artifacts["regime_design_candidate_v2"]
    print(f"Regime candidate v2 rows: {candidate.height}")
    print(f"Candidate v2 CSV: {paths['regime_design_candidate_v2_csv']}")
    print(f"Candidate v2 Markdown: {paths['regime_design_candidate_v2_md']}")
```

- [ ] **Step 6: Run tests**

Run:

```powershell
uv run pytest tests/test_regime_candidate_revision.py -q
```

Expected: pass.

---

## Task 5: v1-v2 R2 Comparison

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing per-macro comparison test**

Append to `tests/test_regime_design_validation.py`:

```python
from solarstorm.onda2e import compare_regime_candidate_r2


def test_compare_regime_candidate_r2_reports_per_macro_gate_metrics():
    v1 = pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_nw_or_foehn",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 10,
                "status": "validated",
            },
        ]
    )
    v2 = pl.DataFrame(
        [
            {
                "regime": "macro_light_marine_or_residual",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 20,
                "status": "validated",
            },
            {
                "regime": "macro_nw_continuum",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 10,
                "status": "validated",
            },
        ]
    )
    assignments_v2 = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "low_confidence_flag": False,
                "component_entropy": 0.10,
                "component_margin": 0.80,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "low_confidence_flag": True,
                "component_entropy": 0.40,
                "component_margin": 0.20,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "low_confidence_flag": False,
                "component_entropy": 0.20,
                "component_margin": 0.70,
            },
            {
                "date_local": dt.date(2025, 1, 4),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "low_confidence_flag": False,
                "component_entropy": 0.30,
                "component_margin": 0.60,
            },
        ]
    )

    artifacts = compare_regime_candidate_r2(
        v1_r2=v1,
        v2_r2=v2,
        v2_assignments=assignments_v2,
        v1_regimes=("candidate_maritime_cloudy", "candidate_nw_or_foehn"),
        v2_regimes=("macro_light_marine_or_residual", "macro_nw_continuum"),
        protected_v2_regimes=("macro_nw_continuum",),
        min_assignment_rows=2,
    )

    comparison = artifacts["regime_candidate_v1_v2_comparison"]
    light = comparison.filter(
        pl.col("macro_regime_label") == "macro_light_marine_or_residual"
    ).row(0, named=True)

    assert comparison.height == 2
    assert light["candidate_version"] == "v2"
    assert light["assignment_rows"] == 2
    assert light["r2_pass_rows"] == 1
    assert light["r2_dead_status"] == "PASS"
    assert light["protected_regression_flag"] is False
    assert light["low_confidence_share"] == 0.5
    assert light["smallest_cp_support"] == 2
    assert light["v1_dead_regimes"] == 1
    assert light["v2_dead_regimes"] == 0
    assert light["decision_update"] == "READY_FOR_FULL_ONDA4_RERUN"
    assert light["production_status"] == "EXPERIMENT_ONLY"
```

- [ ] **Step 2: Run red per-macro comparison test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_compare_regime_candidate_r2_reports_per_macro_gate_metrics -q
```

Expected: fail because `compare_regime_candidate_r2` is not exported.

- [ ] **Step 3: Implement comparison helper**

Add to `_regime_design_validation.py`:

```python
COMPARISON_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "protected_regression_flag": pl.Boolean,
    "low_confidence_share": pl.Float64,
    "mean_component_entropy": pl.Float64,
    "mean_component_margin": pl.Float64,
    "smallest_cp_support": pl.Int64,
    "v1_dead_regimes": pl.Int64,
    "v2_dead_regimes": pl.Int64,
    "protected_regressions": pl.Utf8,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
}


def _as_bool_passes(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.schema.get("passes") == pl.Boolean:
        return frame
    return frame.with_columns(
        pl.col("passes")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .is_in(["true", "1", "yes"])
        .alias("passes")
    )


def _r2_summary_for_regime(r2: pl.DataFrame, regime: str) -> tuple[int, int]:
    subset = r2.filter(pl.col("regime") == regime)
    if subset.height == 0:
        return 0, 0
    return subset.height, subset.filter(pl.col("passes")).height


def _assignment_summary_for_macro(
    assignments: pl.DataFrame,
    macro: str,
) -> tuple[int, float | None, float | None, float | None, int]:
    label_col = (
        "macro_regime_label"
        if "macro_regime_label" in assignments.columns
        else "candidate_regime_label"
    )
    subset = assignments.filter(pl.col(label_col) == macro)
    if subset.height == 0:
        return 0, None, None, None, 0
    low_confidence = (
        float(subset.filter(pl.col("low_confidence_flag")).height / subset.height)
        if "low_confidence_flag" in subset.columns
        else None
    )
    mean_entropy = (
        float(subset["component_entropy"].mean())
        if "component_entropy" in subset.columns
        else None
    )
    mean_margin = (
        float(subset["component_margin"].mean())
        if "component_margin" in subset.columns
        else None
    )
    smallest_cp_support = (
        int(subset.group_by("cp").len(name="n")["n"].min())
        if "cp" in subset.columns
        else subset.height
    )
    return subset.height, low_confidence, mean_entropy, mean_margin, smallest_cp_support


def compare_regime_candidate_r2(
    *,
    v1_r2: pl.DataFrame,
    v2_r2: pl.DataFrame,
    v2_assignments: pl.DataFrame,
    v1_regimes: tuple[str, ...],
    v2_regimes: tuple[str, ...],
    protected_v2_regimes: tuple[str, ...],
    min_assignment_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    v1_norm = _as_bool_passes(v1_r2)
    v2_norm = _as_bool_passes(v2_r2)
    v1_dead = detect_dead_regimes(v1_norm, regimes=v1_regimes)
    v2_dead = detect_dead_regimes(v2_norm, regimes=v2_regimes)
    regressions = sorted(set(v2_dead) & set(protected_v2_regimes))
    support_by_macro: dict[str, int] = {}
    rows: list[dict[str, object]] = []
    for macro in v2_regimes:
        assignment_rows, low_share, mean_entropy, mean_margin, smallest_cp = (
            _assignment_summary_for_macro(v2_assignments, macro)
        )
        support_by_macro[macro] = assignment_rows
        r2_rows, r2_pass_rows = _r2_summary_for_regime(v2_norm, macro)
        rows.append(
            {
                "candidate_version": "v2",
                "macro_regime_label": macro,
                "assignment_rows": assignment_rows,
                "r2_rows": r2_rows,
                "r2_pass_rows": r2_pass_rows,
                "r2_dead_status": "DEAD" if macro in v2_dead else "PASS",
                "protected_regression_flag": macro in regressions,
                "low_confidence_share": low_share,
                "mean_component_entropy": mean_entropy,
                "mean_component_margin": mean_margin,
                "smallest_cp_support": smallest_cp,
                "v1_dead_regimes": len(v1_dead),
                "v2_dead_regimes": len(v2_dead),
                "protected_regressions": ";".join(regressions),
                "decision_update": "",
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    underpowered = [
        macro for macro, support in support_by_macro.items() if support < min_assignment_rows
    ]
    decision = (
        "READY_FOR_FULL_ONDA4_RERUN"
        if not v2_dead and not regressions and not underpowered
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    rows = [{**row, "decision_update": decision} for row in rows]
    return {
        "regime_candidate_v1_v2_comparison": pl.DataFrame(
            rows,
            schema=COMPARISON_SCHEMA,
            strict=False,
        )
    }
```

- [ ] **Step 4: Export helper**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_design_validation import (
    compare_regime_candidate_r2,
)
```

Add `"compare_regime_candidate_r2"` to `__all__`.

- [ ] **Step 5: Run comparison tests**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_compare_regime_candidate_r2_reports_per_macro_gate_metrics -q
```

Expected: pass.

---

## Task 6: v2 Assignment Artifacts

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing v2 soft-assignment test**

Modify the imports at the top of `tests/test_regime_design_validation.py`:

```python
import json
```

Append:

```python
from solarstorm.onda2e import build_regime_candidate_v2_assignment_artifacts


def _candidate_v2_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2",
                "candidate_id": "RDC-V2-0001",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "latent_component_id": "macro_nw_continuum:subtype_standard_nw:month:1",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_source_rows": 100,
                "mean_interpretability_score": 0.6,
                "physical_signature": "northerly_nw_flow",
                "wind_dir_deg_mean": 350.0,
                "wind_speed_mean": 17.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp_mean": 0.5,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v2",
                "candidate_id": "RDC-V2-0002",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "latent_component_id": "macro_southerly_flow:subtype_frontal_southerly:month:1",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_source_rows": 80,
                "mean_interpretability_score": 0.7,
                "physical_signature": "southerly_flow;windy",
                "wind_dir_deg_mean": 180.0,
                "wind_speed_mean": 15.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp_mean": -0.4,
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_v2_assignment_artifacts_use_distance_softmax_probabilities():
    artifacts = build_regime_candidate_v2_assignment_artifacts(
        _candidate_v2_rows(),
        _feature_rows(n_days=4),
        _label_rows(n_days=4),
        _obs_rows(n_days=4),
        tz_name="UTC",
    )

    assignments = artifacts["regime_candidate_assignments_v2"]
    ontology = artifacts["regime_candidate_ontology_v2"]
    audit = artifacts["regime_candidate_assignment_audit_v2"]
    row = assignments.row(0, named=True)
    component_probs = json.loads(row["component_probabilities"])
    family_probs = json.loads(row["family_probabilities"])

    assert assignments.height == 4
    assert ontology.height == 2
    assert row["component_argmax"] in component_probs
    assert abs(sum(component_probs.values()) - 1.0) < 1e-9
    assert abs(sum(family_probs.values()) - 1.0) < 1e-9
    assert row["candidate_regime_label"] == row["macro_regime_label"]
    assert row["component_entropy"] >= 0.0
    assert 0.0 <= row["component_margin"] <= 1.0
    assert 0.0 <= row["assignment_confidence"] <= 1.0
    assert row["causal_window"] == "valid < CP"
    assert row["production_status"] == "NOT_PRODUCTION"
    assert audit.filter(pl.col("audit_item") == "soft_assignment_probabilities").row(
        0,
        named=True,
    )["status"] == "PASS"
```

- [ ] **Step 2: Run red v2 assignment test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_v2_assignment_artifacts_use_distance_softmax_probabilities -q
```

Expected: fail because helper is not exported.

- [ ] **Step 3: Implement v2 assignment schemas**

Add to `_regime_design_validation.py`:

```python
import json

ASSIGNMENT_V2_SCHEMA: dict[str, pl.DataType] = {
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
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_V2_SCHEMA: dict[str, pl.DataType] = {
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "latent_component_id": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "n_source_rows": pl.Int64,
    "production_status": pl.Utf8,
}

AUDIT_V2_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}
```

- [ ] **Step 4: Implement v2 distance-softmax helpers**

Add to `_regime_design_validation.py`:

```python
V2_CENTROID_COLUMNS: tuple[str, ...] = (
    "wind_dir_deg_mean",
    "wind_speed_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum_mean",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp_mean",
)


def _candidate_v2_vector(row: dict[str, object]) -> list[float | None]:
    wind_dir = _safe_float(row.get("wind_dir_deg_mean"))
    sin_mean = math.sin(math.radians(wind_dir)) if wind_dir is not None else None
    cos_mean = math.cos(math.radians(wind_dir)) if wind_dir is not None else None
    return [
        sin_mean,
        cos_mean,
        _safe_float(row.get("wind_speed_mean")),
        _safe_float(row.get("qnh_hpa_mean")),
        _safe_float(row.get("relh_mean")),
        _safe_float(row.get("dewpoint_depression_mean")),
        _safe_float(row.get("precip_pre_cp_sum_mean")),
        _safe_float(row.get("cloud_cover_score_mean")),
        _safe_float(row.get("temp_slope_pre_cp_mean")),
    ]


def _candidate_v2_centroids(candidate_v2: pl.DataFrame) -> list[dict[str, object]]:
    centroids: list[dict[str, object]] = []
    for row in candidate_v2.iter_rows(named=True):
        vector = _candidate_v2_vector(row)
        if any(value is None for value in vector):
            continue
        centroids.append(
            {
                "candidate_id": str(row["candidate_id"]),
                "macro_regime_label": str(row["macro_regime_label"]),
                "subtype_label": str(row["subtype_label"]),
                "latent_component_id": str(
                    row.get("latent_component_id") or row["candidate_id"]
                ),
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "n_source_rows": int(row.get("n_source_rows") or 0),
                "production_status": "NOT_PRODUCTION",
                "vector": [float(value) for value in vector if value is not None],
            }
        )
    return centroids


def _softmax_from_distances(distances: list[float]) -> list[float]:
    if not distances:
        return []
    scores = np.array([-float(distance) for distance in distances], dtype=float)
    scores = scores - np.max(scores)
    exp_scores = np.exp(scores)
    total = float(exp_scores.sum())
    return [float(value / total) for value in exp_scores]


def _entropy(probabilities: list[float]) -> float:
    return float(
        -sum(prob * math.log(prob) for prob in probabilities if prob > 0.0)
    )


def _probability_json(pairs: list[tuple[str, float]]) -> str:
    return json.dumps(
        {key: round(float(value), 12) for key, value in pairs},
        sort_keys=True,
    )
```

- [ ] **Step 5: Implement v2 artifact builder**

Add to `_regime_design_validation.py`:

```python
def _ontology_v2(centroids: list[dict[str, object]]) -> pl.DataFrame:
    rows = [
        {
            "macro_regime_label": row["macro_regime_label"],
            "subtype_label": row["subtype_label"],
            "latent_component_id": row["latent_component_id"],
            "source_candidate_id": row["candidate_id"],
            "stratum_type": row["stratum_type"],
            "stratum_value": row["stratum_value"],
            "n_source_rows": row["n_source_rows"],
            "production_status": "NOT_PRODUCTION",
        }
        for row in centroids
    ]
    return pl.DataFrame(rows, schema=ONTOLOGY_V2_SCHEMA, strict=False)


def _audit_v2(
    assignments: pl.DataFrame,
    matrix: pl.DataFrame,
    *,
    used_fallback: int,
    imputed_values: int,
) -> pl.DataFrame:
    probability_status = "PASS"
    if assignments.height:
        for row in assignments.iter_rows(named=True):
            total = sum(json.loads(str(row["component_probabilities"])).values())
            if abs(float(total) - 1.0) > 1e-6:
                probability_status = "FAIL"
                break
    rows = [
        {
            "audit_item": "assignment_coverage",
            "status": "PASS" if assignments.height == matrix.height else "FAIL",
            "detail": f"{assignments.height}/{matrix.height} feature rows received v2 labels.",
        },
        {
            "audit_item": "soft_assignment_probabilities",
            "status": probability_status,
            "detail": "Component probabilities are distance-softmax normalized.",
        },
        {
            "audit_item": "season_fallback",
            "status": "PASS" if used_fallback == 0 else "WARN",
            "detail": f"{used_fallback} rows used season-level fallback centroids.",
        },
        {
            "audit_item": "missing_input_imputation",
            "status": "PASS" if imputed_values == 0 else "WARN",
            "detail": f"{imputed_values} missing assignment inputs were imputed from training means.",
        },
        {
            "audit_item": "production_status",
            "status": (
                "PASS"
                if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height == 0
                else "FAIL"
            ),
            "detail": "v2 assignment artifacts remain NOT_PRODUCTION.",
        },
    ]
    return pl.DataFrame(rows, schema=AUDIT_V2_SCHEMA, strict=False)


def build_regime_candidate_v2_assignment_artifacts(
    candidate_v2: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    required = {
        "candidate_id",
        "macro_regime_label",
        "subtype_label",
        "stratum_type",
        "stratum_value",
        "production_status",
        *V2_CENTROID_COLUMNS,
    }
    missing = required - set(candidate_v2.columns)
    if missing:
        raise ValueError(
            "candidate_v2 missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    if candidate_v2.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("candidate_v2 must remain NOT_PRODUCTION")

    centroids = _candidate_v2_centroids(candidate_v2)
    ontology = _ontology_v2(centroids)
    matrix = _build_cluster_matrix(features, labels, obs, tz_name=tz_name)
    if matrix.height == 0 or not centroids:
        assignments = _empty_frame(ASSIGNMENT_V2_SCHEMA)
        return {
            "regime_candidate_assignments_v2": assignments,
            "regime_candidate_ontology_v2": ontology,
            "regime_candidate_assignment_audit_v2": _audit_v2(
                assignments,
                matrix,
                used_fallback=0,
                imputed_values=0,
            ),
        }

    means, stds = _standardization(matrix, centroids)
    centroid_vectors = {
        str(row["candidate_id"]): _standardize_vector(row["vector"], means, stds)[0]  # type: ignore[arg-type]
        for row in centroids
    }
    rows: list[dict[str, object]] = []
    used_fallback = 0
    imputed_values = 0
    for row in matrix.iter_rows(named=True):
        choices, fallback = _pick_candidates(centroids, month=int(row["month"]))
        if not choices:
            choices = centroids
        if fallback:
            used_fallback += 1
        row_vector, row_imputed = _standardize_vector(_assignment_vector(row), means, stds)
        imputed_values += row_imputed
        distances: list[float] = [
            float(np.linalg.norm(row_vector - centroid_vectors[str(choice["candidate_id"])]))
            for choice in choices
        ]
        probabilities = _softmax_from_distances(distances)
        ranked = sorted(
            zip(choices, distances, probabilities, strict=False),
            key=lambda item: item[2],
            reverse=True,
        )
        best, best_distance, best_probability = ranked[0]
        alternative = ranked[1] if len(ranked) > 1 else None
        margin = (
            float(best_probability - alternative[2])
            if alternative is not None
            else 1.0
        )
        family_totals: dict[str, float] = {}
        for choice, _distance, probability in ranked:
            macro = str(choice["macro_regime_label"])
            family_totals[macro] = family_totals.get(macro, 0.0) + float(probability)
        nearest_alternative_macro = (
            str(alternative[0]["macro_regime_label"]) if alternative is not None else ""
        )
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": str(row["cp"]),
                "macro_regime_label": str(best["macro_regime_label"]),
                "subtype_label": str(best["subtype_label"]),
                "candidate_regime_label": str(best["macro_regime_label"]),
                "source_candidate_id": str(best["candidate_id"]),
                "component_argmax": str(best["latent_component_id"]),
                "component_probabilities": _probability_json(
                    [
                        (str(choice["latent_component_id"]), probability)
                        for choice, _distance, probability in ranked
                    ]
                ),
                "family_probabilities": _probability_json(
                    sorted(family_totals.items())
                ),
                "component_entropy": _entropy(probabilities),
                "component_margin": margin,
                "nearest_alternative_macro": nearest_alternative_macro,
                "distance_to_candidate": float(best_distance),
                "distance_to_alternative": (
                    float(alternative[1]) if alternative is not None else None
                ),
                "assignment_confidence": float(best_probability),
                "low_confidence_flag": bool(margin < 0.15 or _entropy(probabilities) > 1.0),
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )
    assignments = pl.DataFrame(rows, schema=ASSIGNMENT_V2_SCHEMA, strict=False)
    return {
        "regime_candidate_assignments_v2": assignments,
        "regime_candidate_ontology_v2": ontology,
        "regime_candidate_assignment_audit_v2": _audit_v2(
            assignments,
            matrix,
            used_fallback=used_fallback,
            imputed_values=imputed_values,
        ),
    }
```

- [ ] **Step 6: Export helper**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_design_validation import (
    build_regime_candidate_v2_assignment_artifacts,
)
```

Add `"build_regime_candidate_v2_assignment_artifacts"` to `__all__`.

- [ ] **Step 7: Run tests**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_v2_assignment_artifacts_use_distance_softmax_probabilities -q
```

Expected: pass.

---

## Task 7: Foundation Experiment Results Accept v2 Comparison

**Files:**
- Modify: `solarstorm/onda2e/_foundation_experiment_results.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_foundation_experiment_results.py`

- [ ] **Step 1: Write failing foundation result test**

Append to `tests/test_foundation_experiment_results.py`:

```python
def test_dead_regime_results_can_use_v2_comparison_pass():
    labels, assignments = _labels_and_assignments()
    comparison = pl.DataFrame(
        [
            {
                "v1_dead_regimes": 2,
                "v2_dead_regimes": 0,
                "protected_regressions": "",
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            }
        ]
    )

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=_dead_r2_rows(),
        regime_candidate_v2_comparison=comparison,
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    maritime = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id") == "REXP-DEAD-MARITIME-001"
    ).row(0, named=True)

    assert maritime["status"] == "passed"
    assert maritime["r2_dead_regimes"] == 0
    assert "v2 comparison ready for full Onda 4 rerun" in maritime["notes"]
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_foundation_experiment_results.py::test_dead_regime_results_can_use_v2_comparison_pass -q
```

Expected: fail because `regime_candidate_v2_comparison` is not accepted.

- [ ] **Step 3: Extend result builder signature**

Modify `build_foundation_experiment_results`:

```python
def build_foundation_experiment_results(
    *,
    catalog: pl.DataFrame,
    labels: pl.DataFrame,
    candidate_assignments: pl.DataFrame,
    regime_candidate_r2_validation: pl.DataFrame | None = None,
    regime_candidate_v2_comparison: pl.DataFrame | None = None,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    test_starts: list[dt.date] | None = None,
    test_length_days: int = 365,
    min_cell_rows: int = 30,
    n_bootstrap: int = 1000,
    run_id: str | None = None,
) -> dict[str, pl.DataFrame]:
```

- [ ] **Step 4: Add comparison override helper**

Add:

```python
def _v2_comparison_result_row(
    *,
    experiment_id: str,
    comparison: pl.DataFrame,
    run_id: str,
) -> dict[str, object] | None:
    if comparison is None or comparison.height == 0:
        return None
    row = comparison.row(0, named=True)
    if row.get("production_status") != "EXPERIMENT_ONLY":
        raise ValueError("v2 comparison must remain EXPERIMENT_ONLY")
    v2_dead = int(row.get("v2_dead_regimes") or 0)
    regressions = str(row.get("protected_regressions") or "")
    passed = (
        v2_dead == 0
        and not regressions
        and row.get("decision_update") == "READY_FOR_FULL_ONDA4_RERUN"
    )
    return _result_row(
        experiment_id=experiment_id,
        run_id=run_id,
        status="passed" if passed else "failed",
        r2_dead_regimes=v2_dead,
        notes=(
            "v2 comparison ready for full Onda 4 rerun."
            if passed
            else "v2 comparison remains in regime-design review."
        ),
    )
```

Before calling `_run_dead_regime_experiment`, check this override for
`REXP-DEAD-MARITIME-001` and `REXP-DEAD-MIXED-001`.

- [ ] **Step 5: Wire v2 comparison into the result loop**

Replace the dead-regime loop body in `build_foundation_experiment_results` with:

```python
    if regime_candidate_r2_validation is not None:
        catalog_ids = set(catalog.get_column("experiment_id"))
        for experiment_id in sorted(_DEAD_REGIME_EXPERIMENT_TARGETS):
            if experiment_id not in catalog_ids:
                continue
            v2_override = _v2_comparison_result_row(
                experiment_id=experiment_id,
                comparison=regime_candidate_v2_comparison,
                run_id=resolved_run_id,
            )
            if v2_override is not None:
                result_by_id[experiment_id] = v2_override
                continue
            result_by_id[experiment_id] = _run_dead_regime_experiment(
                experiment_id=experiment_id,
                regime_candidate_r2_validation=regime_candidate_r2_validation,
                candidate_assignments=candidate_assignments,
                cp_set=cp_set,
                run_id=resolved_run_id,
            )
```

- [ ] **Step 6: Add CLI comparison option**

Modify `foundation_experiment_results` in `solarstorm/__main__.py`:

```python
    regime_candidate_v2_comparison_path: str | None = typer.Option(
        None,
        "--regime-candidate-v2-comparison-path",
        help="Optional path to regime_candidate_v1_v2_comparison.csv.",
    ),
```

After loading `regime_candidate_r2`, add:

```python
    regime_candidate_v2_comparison = None
    if regime_candidate_v2_comparison_path is not None:
        comparison_file = Path(regime_candidate_v2_comparison_path)
        if not comparison_file.exists():
            print(f"ERROR: v2 comparison file not found: {comparison_file}")
            raise typer.Exit(2)
        regime_candidate_v2_comparison = pl.read_csv(comparison_file)
```

Pass it to `build_foundation_experiment_results`:

```python
            regime_candidate_v2_comparison=regime_candidate_v2_comparison,
```

- [ ] **Step 7: Run focused test**

Run:

```powershell
uv run pytest tests/test_foundation_experiment_results.py::test_dead_regime_results_can_use_v2_comparison_pass -q
```

Expected: pass.

---

## Task 8: v2 Validation Writers And CLI

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing v2 writer test**

Append to `tests/test_regime_design_validation.py`:

```python
from solarstorm.onda2e import write_regime_candidate_v2_validation_artifacts


def test_write_regime_candidate_v2_validation_artifacts(tmp_path: Path):
    artifacts = {
        "regime_candidate_assignments_v2": pl.DataFrame(
            [
                {
                    "date_local": dt.date(2025, 1, 1),
                    "cp": "20:00",
                    "macro_regime_label": "macro_nw_continuum",
                    "subtype_label": "subtype_standard_nw",
                    "candidate_regime_label": "macro_nw_continuum",
                    "source_candidate_id": "RDC-V2-0001",
                    "component_argmax": "macro_nw_continuum:subtype_standard_nw:month:1",
                    "component_probabilities": "{\"macro_nw_continuum:subtype_standard_nw:month:1\": 1.0}",
                    "family_probabilities": "{\"macro_nw_continuum\": 1.0}",
                    "component_entropy": 0.0,
                    "component_margin": 1.0,
                    "nearest_alternative_macro": "",
                    "distance_to_candidate": 0.0,
                    "distance_to_alternative": None,
                    "assignment_confidence": 1.0,
                    "low_confidence_flag": False,
                    "causal_window": "valid < CP",
                    "production_status": "NOT_PRODUCTION",
                }
            ],
            strict=False,
        ),
        "regime_candidate_ontology_v2": pl.DataFrame(
            [
                {
                    "macro_regime_label": "macro_nw_continuum",
                    "subtype_label": "subtype_standard_nw",
                    "latent_component_id": "macro_nw_continuum:subtype_standard_nw:month:1",
                    "source_candidate_id": "RDC-V2-0001",
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "n_source_rows": 100,
                    "production_status": "NOT_PRODUCTION",
                }
            ]
        ),
        "regime_candidate_assignment_audit_v2": pl.DataFrame(
            [{"audit_item": "soft_assignment_probabilities", "status": "PASS", "detail": "ok"}]
        ),
        "regime_candidate_r2_validation": pl.DataFrame(
            [
                {
                    "regime": "macro_nw_continuum",
                    "hypothesis_id": "H",
                    "feature_column": "feat",
                    "cp": "20:00",
                    "passes": True,
                    "n_days": 10,
                    "status": "validated",
                }
            ]
        ),
        "regime_candidate_v1_v2_comparison": pl.DataFrame(
            [
                {
                    "candidate_version": "v2",
                    "macro_regime_label": "macro_nw_continuum",
                    "assignment_rows": 1,
                    "r2_rows": 1,
                    "r2_pass_rows": 1,
                    "r2_dead_status": "PASS",
                    "protected_regression_flag": False,
                    "low_confidence_share": 0.0,
                    "mean_component_entropy": 0.0,
                    "mean_component_margin": 1.0,
                    "smallest_cp_support": 1,
                    "v1_dead_regimes": 1,
                    "v2_dead_regimes": 0,
                    "protected_regressions": "",
                    "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                    "production_status": "EXPERIMENT_ONLY",
                }
            ]
        ),
    }

    paths = write_regime_candidate_v2_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "regime_candidate_assignments_v2.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v2.csv").exists()
    assert (tmp_path / "regime_candidate_assignment_audit_v2.csv").exists()
    assert (tmp_path / "regime_candidate_r2_validation_v2.csv").exists()
    assert (tmp_path / "regime_candidate_v1_v2_comparison.csv").exists()
    report = paths["regime_candidate_v2_validation_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Candidate v2 Validation - 2026-06-07" in report
    assert "not a production classifier" in report
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_write_regime_candidate_v2_validation_artifacts -q
```

Expected: fail because `write_regime_candidate_v2_validation_artifacts` is not exported.

- [ ] **Step 3: Implement v2 validation writer**

Add to `_regime_design_validation.py`:

```python
def _v2_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    assignments = artifacts["regime_candidate_assignments_v2"]
    comparison = artifacts["regime_candidate_v1_v2_comparison"]
    decision = (
        str(comparison["decision_update"][0])
        if comparison.height and "decision_update" in comparison.columns
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    lines = [
        f"# Regime Candidate v2 Validation - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        "Regime Ontology v2 is an offline candidate for Onda 4 R2 validation only.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Macro regimes: {assignments['macro_regime_label'].n_unique() if assignments.height else 0}",
        f"- Decision update: {decision}",
        "",
        "## v1-v2 Comparison",
        "",
        "| Macro regime | Assignments | R2 pass rows | Dead status | Low confidence | Decision |",
        "|---|---:|---:|---|---:|---|",
    ]
    for row in comparison.sort("macro_regime_label").iter_rows(named=True):
        lines.append(
            "| "
            f"{row['macro_regime_label']} | "
            f"{row['assignment_rows']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_dead_status']} | "
            f"{row['low_confidence_share']} | "
            f"{row['decision_update']} |"
        )
    lines += [
        "",
        "## Next Action",
        "",
        (
            "Run a full Onda 4 robustness rerun with a candidate feature copy."
            if decision == "READY_FOR_FULL_ONDA4_RERUN"
            else "Keep Onda 3 blocked and revise v2 regime design before a full Onda 4 rerun."
        ),
    ]
    return lines


def write_regime_candidate_v2_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments_v2": "regime_candidate_assignments_v2.csv",
        "regime_candidate_ontology_v2": "regime_candidate_ontology_v2.csv",
        "regime_candidate_assignment_audit_v2": "regime_candidate_assignment_audit_v2.csv",
        "regime_candidate_r2_validation": "regime_candidate_r2_validation_v2.csv",
        "regime_candidate_v1_v2_comparison": "regime_candidate_v1_v2_comparison.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    report_path = out_dir / "regime_candidate_v2_validation_report.md"
    report_path.write_text(
        "\n".join(_v2_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_candidate_v2_validation_report_md"] = report_path
    return paths
```

- [ ] **Step 4: Export writer**

Modify `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_design_validation import (
    write_regime_candidate_v2_validation_artifacts,
)
```

Add `"write_regime_candidate_v2_validation_artifacts"` to `__all__`.

- [ ] **Step 5: Add v2 validation CLI**

Modify `solarstorm/__main__.py` imports:

```python
from solarstorm.onda2e import (
    build_regime_candidate_v2_assignment_artifacts,
    compare_regime_candidate_r2,
    write_regime_candidate_v2_validation_artifacts,
)
```

Add command:

```python
@app.command("regime-design-v2-validate")
def regime_design_v2_validate(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    obs_path: str = typer.Option("./data/obs.parquet"),
    candidate_v2_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v2.csv"
    ),
    v1_r2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation.csv"
    ),
    output_dir: str = typer.Option("./reports/regime-design"),
    tz_name: str = typer.Option(TZ_NAME),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00"),
    test_start: str | None = typer.Option(None, "--test-start"),
    min_assignment_rows: int = typer.Option(30),
):
    """Validate Regime Ontology v2 without promoting production labels."""
    required_paths = [
        Path(features_path),
        Path(labels_path),
        Path(obs_path),
        Path(candidate_v2_path),
        Path(v1_r2_path),
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [
            dt.date.fromisoformat(value.strip())
            for value in test_start.split(",")
            if value.strip()
        ]
        if test_start
        else None
    )
    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    obs = pl.read_parquet(obs_path)
    candidate_v2 = pl.read_csv(candidate_v2_path)
    assignments = build_regime_candidate_v2_assignment_artifacts(
        candidate_v2,
        features,
        labels,
        obs,
        tz_name=tz_name,
    )
    validation = validate_regime_candidate_r2(
        features,
        labels,
        assignments["regime_candidate_assignments_v2"],
        SEED_HYPOTHESES,
        cp_set=parsed_cp_set,
        test_starts=test_starts,
    )
    comparison = compare_regime_candidate_r2(
        v1_r2=pl.read_csv(v1_r2_path),
        v2_r2=validation["regime_candidate_r2_validation"],
        v2_assignments=assignments["regime_candidate_assignments_v2"],
        v1_regimes=tuple(sorted(pl.read_csv(v1_r2_path)["regime"].unique().to_list())),
        v2_regimes=tuple(
            sorted(
                assignments["regime_candidate_assignments_v2"][
                    "candidate_regime_label"
                ].drop_nulls().unique().to_list()
            )
        ),
        protected_v2_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        min_assignment_rows=min_assignment_rows,
    )
    paths = write_regime_candidate_v2_validation_artifacts(
        {**assignments, **validation, **comparison},
        output_dir=output_dir,
    )
    print(f"v2 assignments: {assignments['regime_candidate_assignments_v2'].height}")
    print(f"v2 validation report: {paths['regime_candidate_v2_validation_report_md']}")
```

- [ ] **Step 6: Run writer test**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py::test_write_regime_candidate_v2_validation_artifacts -q
```

Expected: pass.

---

## Task 9: Real Artifact Generation Commands

**Files:**
- Generated: `reports/regime-design/regime_repair_diagnostics_v1.csv`
- Generated: `reports/regime-design/regime_repair_diagnostics_v1.md`
- Generated: `reports/onda2e/regime_design_candidate_v2.csv`
- Generated: `reports/onda2e/regime_design_candidate_v2.md`
- Generated: `reports/regime-design/regime_candidate_assignments_v2.csv`
- Generated: `reports/regime-design/regime_candidate_ontology_v2.csv`
- Generated: `reports/regime-design/regime_candidate_assignment_audit_v2.csv`
- Generated: `reports/regime-design/regime_candidate_r2_validation_v2.csv`
- Generated: `reports/regime-design/regime_candidate_v1_v2_comparison.csv`
- Generated: `reports/regime-design/regime_candidate_v2_validation_report.md`
- Generated: `reports/foundation-experiments/foundation_experiment_results_v1.csv`
- Generated: `reports/foundation-experiments/foundation_experiment_results_v1.md`

- [ ] **Step 1: Run repair diagnostics**

Run:

```powershell
uv run python -m solarstorm regime-repair-diagnostics --candidate-path reports/onda2e/regime_design_candidate_v1.csv --assignments-path reports/regime-design/regime_candidate_assignments_v1.csv --r2-path reports/regime-design/regime_candidate_r2_validation.csv --output-dir reports/regime-design
```

Expected output includes:

```text
Regime repair diagnostic rows:
Diagnostics CSV:
Diagnostics Markdown:
```

- [ ] **Step 2: Run candidate v2 generation**

Run:

```powershell
uv run python -m solarstorm regime-candidate-v2 --candidate-v1-path reports/onda2e/regime_design_candidate_v1.csv --output-dir reports/onda2e
```

Expected output includes:

```text
Regime candidate v2 rows:
Candidate v2 CSV:
Candidate v2 Markdown:
```

- [ ] **Step 3: Run v2 assignment, R2, and comparison validation**

Run:

```powershell
uv run python -m solarstorm regime-design-v2-validate --features-path data/features.parquet --labels-path data/labels.parquet --obs-path data/obs.parquet --candidate-v2-path reports/onda2e/regime_design_candidate_v2.csv --v1-r2-path reports/regime-design/regime_candidate_r2_validation.csv --output-dir reports/regime-design
```

Expected output includes:

```text
v2 assignments:
v2 validation report:
```

- [ ] **Step 4: Refresh foundation experiment results with v2 comparison**

Run:

```powershell
uv run python -m solarstorm foundation-experiment-results --catalog-path reports/foundation-experiments/foundation_experiment_catalog_v1.csv --labels-path data/labels.parquet --assignments-path reports/regime-design/regime_candidate_assignments_v2.csv --regime-candidate-r2-path reports/regime-design/regime_candidate_r2_validation_v2.csv --regime-candidate-v2-comparison-path reports/regime-design/regime_candidate_v1_v2_comparison.csv --output-dir reports/foundation-experiments
```

Expected output includes:

```text
Foundation experiment result rows:
Results CSV:
Results Markdown:
```

- [ ] **Step 5: Audit generated artifacts**

Run:

```powershell
@'
from pathlib import Path
import csv
from collections import Counter
for p in [
    "reports/regime-design/regime_repair_diagnostics_v1.csv",
    "reports/onda2e/regime_design_candidate_v2.csv",
    "reports/regime-design/regime_candidate_assignments_v2.csv",
    "reports/regime-design/regime_candidate_v1_v2_comparison.csv",
]:
    path = Path(p)
    print("##", p, "exists=", path.exists())
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("rows", len(rows))
    if rows and "production_status" in rows[0]:
        print("production_status", dict(Counter(r["production_status"] for r in rows)))
    if rows and "macro_regime_label" in rows[0]:
        print("macro_regime_label", dict(Counter(r["macro_regime_label"] for r in rows)))
'@ | uv run python -
```

Expected:

```text
exists= True
production_status contains only NOT_PRODUCTION for candidate artifacts
production_status contains only EXPERIMENT_ONLY for comparison artifacts
```

---

## Task 10: Documentation Updates

**Files:**
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `ROADMAP.md`
- Modify: `docs/regime_model_card.md`

- [ ] **Step 1: Update ADR-012**

Add a short section under the Foundation Experiment or Regime Policy area:

```markdown
Regime Ontology v2 is a non-production redesign candidate. It introduces a
hierarchical macro/subtype assignment surface to repair the v1 flat-family
failure. It does not promote `mixed_or_transition`, `maritime_cloudy`, or
`late_warming` as production macro regimes. The next allowed action is full
candidate validation and, only if candidate R2 has no dead macro regimes, a
full Onda 4 rerun.
```

- [ ] **Step 2: Update ROADMAP**

In the Onda 2E-Gate or Onda 4 section, add:

```markdown
Regime Ontology v2 redesign is the active repair path for the candidate-family
R2 blocker. Onda 3 remains blocked. Passing v2 screening can only unblock a
full Onda 4 rerun, not model training directly.
```

- [ ] **Step 3: Update model card**

Add a non-production note:

```markdown
## Regime Ontology v2 Candidate

The v2 redesign is a non-production candidate that separates macro regimes,
local subtypes, and assignment confidence. The current production-facing
`regime_label` remains the quarantined Onda 2R baseline until ADR-012 and Onda 4
approve a replacement.
```

---

## Task 11: Final Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
uv run pytest tests/test_regime_repair_diagnostics.py tests/test_regime_candidate_revision.py tests/test_regime_design_validation.py tests/test_foundation_experiment_results.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run full non-network suite**

Run:

```powershell
uv run pytest -q -m "not network"
```

Expected: all tests pass, with network tests deselected if present.

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

Run:

```powershell
@'
from pathlib import Path
required = [
    "reports/regime-design/regime_repair_diagnostics_v1.csv",
    "reports/regime-design/regime_repair_diagnostics_v1.md",
    "reports/onda2e/regime_design_candidate_v2.csv",
    "reports/onda2e/regime_design_candidate_v2.md",
    "reports/regime-design/regime_candidate_assignments_v2.csv",
    "reports/regime-design/regime_candidate_ontology_v2.csv",
    "reports/regime-design/regime_candidate_assignment_audit_v2.csv",
    "reports/regime-design/regime_candidate_r2_validation_v2.csv",
    "reports/regime-design/regime_candidate_v1_v2_comparison.csv",
    "reports/regime-design/regime_candidate_v2_validation_report.md",
    "reports/foundation-experiments/foundation_experiment_results_v1.csv",
    "reports/foundation-experiments/foundation_experiment_results_v1.md",
]
missing = [p for p in required if not Path(p).exists()]
print("missing", missing)
if missing:
    raise SystemExit(1)
'@ | uv run python -
```

Expected:

```text
missing []
```

---

## Parallel Execution Guidance

Use subagents only with disjoint write sets:

- Agent A may execute Task 1 and Task 2.
- Agent B may execute Task 3 and Task 4.
- Agent C may execute Task 7.
- Main integrator should execute Task 5, Task 6, Task 8, Task 9, Task 10,
  and Task 11
  because those tasks touch shared validation and CLI wiring.

Do not let multiple agents edit `solarstorm/__main__.py`,
`solarstorm/onda2e/__init__.py`, or `solarstorm/onda2e/_regime_design_validation.py`
at the same time. Integrate those changes sequentially.

## Completion Rule

The sprint is complete only when:

- v2 design artifacts exist;
- all v2 rows remain non-production;
- foundation experiment results can reflect v2 comparison;
- ADR-012 and ROADMAP state that Onda 3 is still blocked until full Onda 4
  passes;
- focused tests, full non-network tests, and ruff all pass.
