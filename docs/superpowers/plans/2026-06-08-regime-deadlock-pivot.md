# Regime Deadlock Pivot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Regime Deadlock Pivot: formal pivot artifacts, audit demotion for `macro_calm_radiative`, binary macro experiment, cloud-cover baseline experiment, and documentation updates.

**Architecture:** Add focused Onda 2E modules that read existing reports/features, build experiment-only Polars artifacts, and expose Typer CLI commands. Keep production data immutable and use tests to enforce that the old v2.4-style threshold loop is superseded rather than extended.

**Tech Stack:** Python, Polars, Typer, pytest, Ruff, existing `solarstorm.onda2e` and baseline/report conventions.

---

## File Structure

- Create `solarstorm/onda2e/_regime_deadlock_pivot.py` for the pivot decision,
  superseded-path, and audit-demotion artifacts.
- Create `solarstorm/onda2e/_regime_binary_macro_candidate.py` for
  experiment-only binary macro candidate and assignment artifacts.
- Create `solarstorm/onda2e/_cloud_cover_baseline_experiment.py` for the
  cloud-adjusted baseline experiment.
- Modify `solarstorm/onda2e/__init__.py` to export the new builders/writers.
- Modify `solarstorm/__main__.py` to add CLI commands.
- Create `tests/test_regime_deadlock_pivot.py`.
- Create `tests/test_regime_binary_macro_candidate.py`.
- Create `tests/test_cloud_cover_baseline_experiment.py`.
- Update the docs listed in the spec.

---

### Task 1: Test Pivot Decision and Audit Demotion Contract

**Files:**
- Create: `tests/test_regime_deadlock_pivot.py`

- [ ] **Step 1: Write failing tests**

Add tests for the pivot decision, superseded path, audit demotion, writer, and
CLI.

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_deadlock_pivot import (
    build_regime_deadlock_pivot_artifacts,
    write_regime_deadlock_pivot_artifacts,
)

runner = CliRunner()


def _r2_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"regime": "macro_calm_radiative", "passes": False, "n_days": 27, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "n_days": 210, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "n_days": 110, "cp": "20:00"},
        ],
        strict=False,
    )


def _cloud_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "experiment_id": "CEXP-CALM-RADIATIVE-002B",
                "feature_column": "cloud_cover_suppression",
                "validation_decision": "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN",
                "controlled_slope": -1.75,
                "controlled_slope_retention": 0.605,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )


def test_deadlock_pivot_marks_old_path_superseded_and_calm_audit_only():
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=_cloud_validation(),
        source_report_path="reports/onda2e/regime_deadlock_diagnosis_v1.md",
    )

    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    demotions = artifacts["regime_audit_demotions_v1"]
    superseded = artifacts["regime_deadlock_superseded_path_v1"]

    assert decision["decision_status"] == "PIVOT_ACCEPTED"
    assert decision["active_path"] == "OPTION_C_AUDIT_DEMOTION_PLUS_OPTION_A_BINARY_EXPERIMENT"
    assert decision["production_status"] == "EXPERIMENT_ONLY"
    assert "v2.4" in decision["blocked_next_actions"]
    assert set(demotions["macro_regime_label"].to_list()) == {
        "macro_calm_radiative",
        "macro_nw_continuum",
        "macro_southerly_flow",
    }
    calm = demotions.filter(pl.col("macro_regime_label") == "macro_calm_radiative").row(0, named=True)
    assert calm["gate_role"] == "AUDIT_ONLY"
    assert calm["blocks_production_gate"] is False
    assert calm["known_signal"] == "cloud_cover_suppression"
    assert superseded.filter(pl.col("superseded_status") == "SUPERSEDED_ACTIVE_UNLOCK_PATH").height >= 1


def test_deadlock_pivot_writer_and_cli(tmp_path: Path):
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=_cloud_validation(),
        source_report_path="reports/onda2e/regime_deadlock_diagnosis_v1.md",
    )
    paths = write_regime_deadlock_pivot_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_deadlock_pivot_decision_v1.csv").exists()
    assert (tmp_path / "regime_deadlock_pivot_decision_v1.md").exists()
    assert (tmp_path / "regime_deadlock_superseded_path_v1.csv").exists()
    assert (tmp_path / "regime_audit_demotions_v1.csv").exists()
    assert (tmp_path / "regime_audit_demotions_v1.md").exists()
    assert "not a production classifier" in paths["regime_deadlock_pivot_decision_md"].read_text(encoding="utf-8")

    r2_path = tmp_path / "r2.csv"
    cloud_path = tmp_path / "cloud.csv"
    output_dir = tmp_path / "cli"
    _r2_validation().write_csv(r2_path)
    _cloud_validation().write_csv(cloud_path)

    result = runner.invoke(
        app,
        [
            "regime-deadlock-pivot",
            "--r2-validation-path",
            str(r2_path),
            "--cloud-validation-path",
            str(cloud_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_deadlock_pivot_decision_v1.csv").exists()
    assert "PIVOT_ACCEPTED" in result.output
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_deadlock_pivot.py -q
```

Expected: fail because `solarstorm.onda2e._regime_deadlock_pivot` and the CLI
command do not exist yet.

---

### Task 2: Implement Pivot Decision and Audit Demotion Artifacts

**Files:**
- Create: `solarstorm/onda2e/_regime_deadlock_pivot.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Add the builder/writer module**

Create `solarstorm/onda2e/_regime_deadlock_pivot.py` with these public
functions and schemas:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

PRODUCTION_MACROS = ("macro_nw_continuum", "macro_southerly_flow")
AUDIT_MACROS = ("macro_calm_radiative",)

DECISION_SCHEMA = {
    "decision_id": pl.Utf8,
    "source_report_path": pl.Utf8,
    "decision_status": pl.Utf8,
    "active_path": pl.Utf8,
    "superseded_path": pl.Utf8,
    "key_evidence": pl.Utf8,
    "allowed_next_actions": pl.Utf8,
    "blocked_next_actions": pl.Utf8,
    "production_status": pl.Utf8,
}

DEMOTION_SCHEMA = {
    "macro_regime_label": pl.Utf8,
    "gate_role": pl.Utf8,
    "blocks_production_gate": pl.Boolean,
    "r2_pass_rows": pl.Int64,
    "median_n_days": pl.Float64,
    "known_signal": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "production_status": pl.Utf8,
}

SUPERSEDED_SCHEMA = {
    "path_item": pl.Utf8,
    "superseded_status": pl.Utf8,
    "reason": pl.Utf8,
    "replacement_path": pl.Utf8,
    "production_status": pl.Utf8,
}


def _r2_summary(r2_validation: pl.DataFrame, regime: str) -> tuple[int, float | None]:
    if r2_validation.height == 0 or "regime" not in r2_validation.columns:
        return 0, None
    subset = r2_validation.filter(pl.col("regime") == regime)
    pass_rows = (
        int(subset.filter(pl.col("passes").fill_null(False)).height)
        if "passes" in subset.columns
        else 0
    )
    median_n = (
        float(subset["n_days"].median())
        if subset.height and "n_days" in subset.columns
        else None
    )
    return pass_rows, median_n


def _cloud_signal(cloud_validation: pl.DataFrame) -> str:
    if cloud_validation.height == 0 or "validation_decision" not in cloud_validation.columns:
        return ""
    survived = cloud_validation.filter(
        pl.col("validation_decision") == "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN"
    )
    return "cloud_cover_suppression" if survived.height else ""


def build_regime_deadlock_pivot_artifacts(
    *,
    r2_validation: pl.DataFrame,
    cloud_validation: pl.DataFrame | None = None,
    source_report_path: str = "reports/onda2e/regime_deadlock_diagnosis_v1.md",
) -> dict[str, pl.DataFrame]:
    cloud_validation = cloud_validation if cloud_validation is not None else pl.DataFrame()
    key_evidence = (
        "train_only_gmm stability=0.0799; classifiability=0.0933; "
        "distance_softmax_v22 low_confidence_share=0.8226; "
        "macro_calm_radiative R2 median n_days=27; "
        "cloud_cover_suppression survives CEXP-002B"
    )
    decision = pl.DataFrame(
        [
            {
                "decision_id": "REGIME-DEADLOCK-PIVOT-001",
                "source_report_path": source_report_path,
                "decision_status": "PIVOT_ACCEPTED",
                "active_path": "OPTION_C_AUDIT_DEMOTION_PLUS_OPTION_A_BINARY_EXPERIMENT",
                "superseded_path": "V22_V23_CEXP_THRESHOLD_RESTORATION_LOOP",
                "key_evidence": key_evidence,
                "allowed_next_actions": (
                    "Generate audit-demotion artifacts; generate binary macro candidate; "
                    "run cloud-cover baseline experiment"
                ),
                "blocked_next_actions": (
                    "No v2.4 calm/radiative threshold tuning; no global R2 weakening; "
                    "no cloudy/clear macro split as active unlock path"
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        schema=DECISION_SCHEMA,
    )

    known_signal = _cloud_signal(cloud_validation)
    demotion_rows = []
    for regime in (*PRODUCTION_MACROS, *AUDIT_MACROS):
        pass_rows, median_n = _r2_summary(r2_validation, regime)
        is_audit = regime in AUDIT_MACROS
        demotion_rows.append(
            {
                "macro_regime_label": regime,
                "gate_role": "AUDIT_ONLY" if is_audit else "PRODUCTION_BLOCKING",
                "blocks_production_gate": not is_audit,
                "r2_pass_rows": pass_rows,
                "median_n_days": median_n,
                "known_signal": known_signal if regime == "macro_calm_radiative" else "",
                "decision_rationale": (
                    "Demoted because repeated R2 failure is underpowered and structurally ambiguous."
                    if is_audit
                    else "Retained as production-blocking because existing evidence supports this macro."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    superseded = pl.DataFrame(
        [
            {
                "path_item": "regime_v22_calm_radiative_restoration",
                "superseded_status": "SUPERSEDED_ACTIVE_UNLOCK_PATH",
                "reason": "Restoration did not resolve R2 deadlock.",
                "replacement_path": "OPTION_C_AUDIT_DEMOTION",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "path_item": "regime_v23_calm_failure_diagnostics",
                "superseded_status": "AUDIT_HISTORY_RETAINED",
                "reason": "Diagnostics explain the blocker but are not an unlock path.",
                "replacement_path": "REGIME_DEADLOCK_PIVOT",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "path_item": "v2.4_threshold_tuning",
                "superseded_status": "BLOCKED_BY_DECISION",
                "reason": "Report diagnoses structural information limit, not calibration.",
                "replacement_path": "OPTION_A_BINARY_EXPERIMENT",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        schema=SUPERSEDED_SCHEMA,
    )

    return {
        "regime_deadlock_pivot_decision_v1": decision,
        "regime_audit_demotions_v1": pl.DataFrame(demotion_rows, schema=DEMOTION_SCHEMA, strict=False),
        "regime_deadlock_superseded_path_v1": superseded,
    }


def _markdown_report(artifacts: dict[str, pl.DataFrame], today: dt.date) -> str:
    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    demotions = artifacts["regime_audit_demotions_v1"]
    lines = [
        f"# Regime Deadlock Pivot Decision - {today.isoformat()}",
        "",
        "Status: experiment-only; not a production classifier.",
        "",
        f"- Decision: {decision['decision_status']}",
        f"- Active path: {decision['active_path']}",
        f"- Superseded path: {decision['superseded_path']}",
        "",
        "## Gate Roles",
        "",
        "| macro | role | blocks gate | R2 pass rows | median n_days |",
        "|---|---|---:|---:|---:|",
    ]
    for row in demotions.iter_rows(named=True):
        lines.append(
            f"| {row['macro_regime_label']} | {row['gate_role']} | "
            f"{row['blocks_production_gate']} | {row['r2_pass_rows']} | {row['median_n_days']} |"
        )
    return "\n".join(lines) + "\n"


def write_regime_deadlock_pivot_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    decision_csv = out_dir / "regime_deadlock_pivot_decision_v1.csv"
    decision_md = out_dir / "regime_deadlock_pivot_decision_v1.md"
    demotions_csv = out_dir / "regime_audit_demotions_v1.csv"
    demotions_md = out_dir / "regime_audit_demotions_v1.md"
    superseded_csv = out_dir / "regime_deadlock_superseded_path_v1.csv"
    artifacts["regime_deadlock_pivot_decision_v1"].write_csv(decision_csv)
    artifacts["regime_audit_demotions_v1"].write_csv(demotions_csv)
    artifacts["regime_deadlock_superseded_path_v1"].write_csv(superseded_csv)
    report = _markdown_report(artifacts, today)
    decision_md.write_text(report, encoding="utf-8")
    demotions_md.write_text(report, encoding="utf-8")
    return {
        "regime_deadlock_pivot_decision_csv": decision_csv,
        "regime_deadlock_pivot_decision_md": decision_md,
        "regime_audit_demotions_csv": demotions_csv,
        "regime_audit_demotions_md": demotions_md,
        "regime_deadlock_superseded_path_csv": superseded_csv,
    }
```

- [ ] **Step 2: Export the functions**

Add these imports and names to `solarstorm/onda2e/__init__.py`:

```python
from solarstorm.onda2e._regime_deadlock_pivot import (
    build_regime_deadlock_pivot_artifacts,
    write_regime_deadlock_pivot_artifacts,
)
```

Add the two public names to `__all__`.

- [ ] **Step 3: Add CLI command**

In `solarstorm/__main__.py`, import the new functions and add:

```python
@app.command("regime-deadlock-pivot")
def regime_deadlock_pivot(
    r2_validation_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2_2.csv",
        help="Path to v2.2 R2 validation CSV",
    ),
    cloud_validation_path: str = typer.Option(
        "./reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv",
        help="Path to CEXP-002B cloud validation CSV",
    ),
    source_report_path: str = typer.Option(
        "./reports/onda2e/regime_deadlock_diagnosis_v1.md",
        help="Path to the deadlock diagnosis report",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for pivot artifacts",
    ),
):
    """Write the regime-deadlock pivot decision and audit-demotion artifacts."""
    required = [Path(r2_validation_path), Path(source_report_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    cloud_path = Path(cloud_validation_path)
    r2_validation = pl.read_csv(r2_validation_path)
    cloud_validation = pl.read_csv(cloud_path) if cloud_path.exists() else pl.DataFrame()
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=r2_validation,
        cloud_validation=cloud_validation,
        source_report_path=source_report_path,
    )
    paths = write_regime_deadlock_pivot_artifacts(artifacts, output_dir=output_dir)
    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    print(f"Regime deadlock pivot: {decision['decision_status']}")
    print(f"Active path: {decision['active_path']}")
    print(f"Pivot report: {paths['regime_deadlock_pivot_decision_md']}")
```

- [ ] **Step 4: Run focused test**

Run:

```powershell
uv run pytest tests/test_regime_deadlock_pivot.py -q
```

Expected: pass.

---

### Task 3: Test Binary Macro Candidate

**Files:**
- Create: `tests/test_regime_binary_macro_candidate.py`

- [ ] **Step 1: Write failing tests**

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_binary_macro_candidate import (
    build_regime_binary_macro_candidate_artifacts,
    write_regime_binary_macro_candidate_artifacts,
)

runner = CliRunner()


def _assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "cp": "20:00", "macro_regime_label": "macro_southerly_flow", "production_status": "NOT_PRODUCTION"},
            {"date_local": dt.date(2025, 1, 2), "cp": "20:00", "macro_regime_label": "macro_nw_continuum", "production_status": "NOT_PRODUCTION"},
            {"date_local": dt.date(2025, 1, 3), "cp": "20:00", "macro_regime_label": "macro_calm_radiative", "production_status": "NOT_PRODUCTION"},
        ],
        strict=False,
    )


def test_binary_macro_candidate_collapses_non_southerly_without_production_mutation():
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    candidate = artifacts["regime_binary_macro_candidate_v1"]
    assignments = artifacts["regime_binary_macro_assignments_v1"]
    audit = artifacts["regime_binary_macro_assignment_audit_v1"]

    assert set(candidate["macro_regime_label"].to_list()) == {
        "macro_southerly_flow",
        "macro_non_southerly",
    }
    assert set(assignments["binary_macro_regime_label"].to_list()) == {
        "macro_southerly_flow",
        "macro_non_southerly",
    }
    calm = assignments.filter(pl.col("source_macro_regime_label") == "macro_calm_radiative").row(0, named=True)
    assert calm["binary_macro_regime_label"] == "macro_non_southerly"
    assert set(assignments["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert audit.filter(pl.col("audit_item") == "source_production_status").row(0, named=True)["status"] == "PASS"


def test_binary_macro_writer_and_cli(tmp_path: Path):
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    paths = write_regime_binary_macro_candidate_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )
    assert (tmp_path / "regime_binary_macro_candidate_v1.csv").exists()
    assert (tmp_path / "regime_binary_macro_candidate_v1.md").exists()
    assert (tmp_path / "regime_binary_macro_assignments_v1.csv").exists()
    assert "experiment-only" in paths["regime_binary_macro_candidate_md"].read_text(encoding="utf-8")

    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "cli"
    _assignments().write_csv(assignments_path)
    result = runner.invoke(
        app,
        [
            "regime-binary-macro-candidate",
            "--assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_binary_macro_assignments_v1.csv").exists()
    assert "macro_non_southerly" in result.output
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_binary_macro_candidate.py -q
```

Expected: fail because the module and CLI do not exist.

---

### Task 4: Implement Binary Macro Candidate

**Files:**
- Create: `solarstorm/onda2e/_regime_binary_macro_candidate.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Create the module**

Implement a small deterministic mapper:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

SOUTHERLY = "macro_southerly_flow"
NON_SOUTHERLY = "macro_non_southerly"


def _source_macro_column(assignments: pl.DataFrame) -> str:
    if "macro_regime_label" in assignments.columns:
        return "macro_regime_label"
    if "candidate_regime_label" in assignments.columns:
        return "candidate_regime_label"
    raise ValueError("assignments require macro_regime_label or candidate_regime_label")


def build_regime_binary_macro_candidate_artifacts(assignments: pl.DataFrame) -> dict[str, pl.DataFrame]:
    if "production_status" not in assignments.columns:
        raise ValueError("assignments missing required column: production_status")
    invalid = assignments.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid.height:
        raise ValueError("source assignments must remain NOT_PRODUCTION")

    macro_col = _source_macro_column(assignments)
    mapped = assignments.select(
        [
            "date_local",
            "cp",
            pl.col(macro_col).alias("source_macro_regime_label"),
        ]
    ).with_columns(
        pl.when(pl.col("source_macro_regime_label") == SOUTHERLY)
        .then(pl.lit(SOUTHERLY))
        .otherwise(pl.lit(NON_SOUTHERLY))
        .alias("binary_macro_regime_label"),
        pl.lit("southerly vs non-southerly experiment-only collapse").alias("assignment_rule"),
        pl.lit("EXPERIMENT_ONLY").alias("production_status"),
    )

    counts = (
        mapped.group_by("binary_macro_regime_label")
        .len(name="n_rows")
        .rename({"binary_macro_regime_label": "macro_regime_label"})
    )
    candidate = pl.DataFrame(
        [
            {
                "candidate_version": "binary_v1",
                "macro_regime_label": SOUTHERLY,
                "description": "Southerly/frontal flow retained as the robust directional macro.",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "binary_v1",
                "macro_regime_label": NON_SOUTHERLY,
                "description": "NW, foehn-like, calm/radiative, marine, and transition cases collapsed.",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    ).join(counts, on="macro_regime_label", how="left").with_columns(
        pl.col("n_rows").fill_null(0)
    )

    audit = pl.DataFrame(
        [
            {
                "audit_item": "source_production_status",
                "status": "PASS",
                "detail": "All source assignment rows are NOT_PRODUCTION.",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "audit_item": "binary_label_set",
                "status": "PASS",
                "detail": "Assignments use only macro_southerly_flow and macro_non_southerly.",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )
    return {
        "regime_binary_macro_candidate_v1": candidate,
        "regime_binary_macro_assignments_v1": mapped,
        "regime_binary_macro_assignment_audit_v1": audit,
    }


def write_regime_binary_macro_candidate_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_csv = out_dir / "regime_binary_macro_candidate_v1.csv"
    candidate_md = out_dir / "regime_binary_macro_candidate_v1.md"
    assignments_csv = out_dir / "regime_binary_macro_assignments_v1.csv"
    audit_csv = out_dir / "regime_binary_macro_assignment_audit_v1.csv"
    artifacts["regime_binary_macro_candidate_v1"].write_csv(candidate_csv)
    artifacts["regime_binary_macro_assignments_v1"].write_csv(assignments_csv)
    artifacts["regime_binary_macro_assignment_audit_v1"].write_csv(audit_csv)
    lines = [
        f"# Regime Binary Macro Candidate - {today.isoformat()}",
        "",
        "This is an experiment-only candidate and not a production classifier.",
        "",
        "| macro | rows |",
        "|---|---:|",
    ]
    for row in artifacts["regime_binary_macro_candidate_v1"].iter_rows(named=True):
        lines.append(f"| {row['macro_regime_label']} | {row['n_rows']} |")
    candidate_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "regime_binary_macro_candidate_csv": candidate_csv,
        "regime_binary_macro_candidate_md": candidate_md,
        "regime_binary_macro_assignments_csv": assignments_csv,
        "regime_binary_macro_assignment_audit_csv": audit_csv,
    }
```

- [ ] **Step 2: Export and add CLI**

Export the builder/writer in `solarstorm/onda2e/__init__.py`.

Add to `solarstorm/__main__.py`:

```python
@app.command("regime-binary-macro-candidate")
def regime_binary_macro_candidate(
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to non-production source regime assignments",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for binary macro candidate artifacts",
    ),
):
    """Write experiment-only binary macro regime candidate artifacts."""
    path = Path(assignments_path)
    if not path.exists():
        print(f"ERROR: missing input file: {path}")
        raise typer.Exit(2)
    artifacts = build_regime_binary_macro_candidate_artifacts(pl.read_csv(path))
    paths = write_regime_binary_macro_candidate_artifacts(artifacts, output_dir=output_dir)
    candidate = artifacts["regime_binary_macro_candidate_v1"]
    labels = ", ".join(candidate["macro_regime_label"].to_list())
    print(f"Binary macro labels: {labels}")
    print(f"Binary macro report: {paths['regime_binary_macro_candidate_md']}")
```

- [ ] **Step 3: Run focused test**

Run:

```powershell
uv run pytest tests/test_regime_binary_macro_candidate.py -q
```

Expected: pass.

---

### Task 5: Test Cloud-Cover Baseline Experiment

**Files:**
- Create: `tests/test_cloud_cover_baseline_experiment.py`

- [ ] **Step 1: Write failing tests**

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._cloud_cover_baseline_experiment import (
    build_cloud_cover_baseline_experiment,
    write_cloud_cover_baseline_experiment_artifacts,
)

runner = CliRunner()


def _features() -> pl.DataFrame:
    rows = []
    for year in (2023, 2024, 2025):
        for idx in range(8):
            day = dt.date(year, 1, 1) + dt.timedelta(days=idx)
            cloud = float(idx % 4)
            rows.append(
                {
                    "date_local": day,
                    "cp": "20:00",
                    "cloud_cover_suppression": cloud,
                    "k_cp__cp_2000": 20.0,
                }
            )
    return pl.DataFrame(rows)


def _labels() -> pl.DataFrame:
    rows = []
    for year in (2023, 2024, 2025):
        for idx in range(8):
            day = dt.date(year, 1, 1) + dt.timedelta(days=idx)
            cloud = float(idx % 4)
            rows.append({"date_local": day, "tmax_int": 24.0 - cloud})
    return pl.DataFrame(rows)


def test_cloud_cover_baseline_experiment_is_walk_forward_and_experiment_only():
    artifacts = build_cloud_cover_baseline_experiment(
        features=_features(),
        labels=_labels(),
        test_years=(2024, 2025),
        cp_set=("20:00",),
    )
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    assert results.height == 2
    assert set(results["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert set(results["feature_column"].to_list()) == {"cloud_cover_suppression"}
    assert results["candidate_mae"].mean() < results["baseline_mae"].mean()
    assert results.filter(pl.col("train_rows") > 0).height == 2


def test_cloud_cover_baseline_writer_and_cli(tmp_path: Path):
    artifacts = build_cloud_cover_baseline_experiment(
        features=_features(),
        labels=_labels(),
        test_years=(2024,),
        cp_set=("20:00",),
    )
    paths = write_cloud_cover_baseline_experiment_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )
    assert (tmp_path / "cloud_cover_baseline_experiment_v1.csv").exists()
    assert (tmp_path / "cloud_cover_baseline_experiment_v1.md").exists()
    assert "experiment-only" in paths["cloud_cover_baseline_experiment_md"].read_text(encoding="utf-8")

    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    output_dir = tmp_path / "cli"
    _features().write_parquet(features_path)
    _labels().write_parquet(labels_path)
    result = runner.invoke(
        app,
        [
            "cloud-cover-baseline-experiment",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
            "--cp-set",
            "20:00",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "cloud_cover_baseline_experiment_v1.csv").exists()
    assert "cloud_cover_suppression" in result.output
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_cloud_cover_baseline_experiment.py -q
```

Expected: fail because the module and CLI do not exist.

---

### Task 6: Implement Cloud-Cover Baseline Experiment

**Files:**
- Create: `solarstorm/onda2e/_cloud_cover_baseline_experiment.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Create train-only baseline experiment**

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

RESULT_SCHEMA = {
    "experiment_id": pl.Utf8,
    "test_year": pl.Int64,
    "cp": pl.Utf8,
    "month": pl.Int64,
    "feature_column": pl.Utf8,
    "train_rows": pl.Int64,
    "test_rows": pl.Int64,
    "baseline_mae": pl.Float64,
    "candidate_mae": pl.Float64,
    "mae_delta": pl.Float64,
    "slope": pl.Float64,
    "intercept": pl.Float64,
    "production_status": pl.Utf8,
}


def _cp_temp_column(cp: str) -> str:
    return f"k_cp__cp_{cp.replace(':', '')}"


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    design = np.column_stack([np.ones(len(x)), x])
    intercept, slope = np.linalg.lstsq(design, y, rcond=None)[0]
    return float(intercept), float(slope)


def _mae(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values))) if len(values) else float("nan")


def build_cloud_cover_baseline_experiment(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    test_years: tuple[int, ...] = (2024, 2025),
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    feature_column: str = "cloud_cover_suppression",
    min_train_rows: int = 8,
    min_test_rows: int = 3,
) -> dict[str, pl.DataFrame]:
    required_features = {"date_local", "cp", feature_column}
    missing_features = required_features - set(features.columns)
    if missing_features:
        raise ValueError(f"features missing required columns: {sorted(missing_features)}")
    if {"date_local", "tmax_int"} - set(labels.columns):
        raise ValueError("labels require date_local and tmax_int")

    joined = features.join(labels.select(["date_local", "tmax_int"]), on="date_local", how="inner")
    if joined.schema["date_local"] == pl.Utf8:
        joined = joined.with_columns(pl.col("date_local").str.to_date())
    joined = joined.with_columns(
        pl.col("date_local").dt.year().alias("year"),
        pl.col("date_local").dt.month().alias("month"),
    )

    rows = []
    for test_year in test_years:
        for cp in cp_set:
            cp_col = _cp_temp_column(cp)
            if cp_col not in joined.columns:
                continue
            cp_frame = joined.filter(pl.col("cp").cast(pl.Utf8) == cp)
            for month in sorted(cp_frame["month"].drop_nulls().unique().to_list()):
                train = cp_frame.filter((pl.col("year") < test_year) & (pl.col("month") == month)).drop_nulls([feature_column, "tmax_int", cp_col])
                test = cp_frame.filter((pl.col("year") == test_year) & (pl.col("month") == month)).drop_nulls([feature_column, "tmax_int", cp_col])
                if train.height < min_train_rows or test.height < min_test_rows:
                    continue
                x_train = train[feature_column].to_numpy().astype(float)
                y_train = (train["tmax_int"] - train[cp_col]).to_numpy().astype(float)
                intercept, slope = _ols(x_train, y_train)
                x_test = test[feature_column].to_numpy().astype(float)
                y_test = (test["tmax_int"] - test[cp_col]).to_numpy().astype(float)
                baseline_remaining = float(np.mean(y_train))
                baseline_error = baseline_remaining - y_test
                candidate_error = (intercept + slope * x_test) - y_test
                baseline_mae = _mae(baseline_error)
                candidate_mae = _mae(candidate_error)
                rows.append(
                    {
                        "experiment_id": "BEXP-CLOUD-COVER-SUPPRESSION-001",
                        "test_year": int(test_year),
                        "cp": cp,
                        "month": int(month),
                        "feature_column": feature_column,
                        "train_rows": train.height,
                        "test_rows": test.height,
                        "baseline_mae": baseline_mae,
                        "candidate_mae": candidate_mae,
                        "mae_delta": baseline_mae - candidate_mae,
                        "slope": slope,
                        "intercept": intercept,
                        "production_status": "EXPERIMENT_ONLY",
                    }
                )
    return {"cloud_cover_baseline_experiment_v1": pl.DataFrame(rows, schema=RESULT_SCHEMA, strict=False)}


def write_cloud_cover_baseline_experiment_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "cloud_cover_baseline_experiment_v1.csv"
    md_path = out_dir / "cloud_cover_baseline_experiment_v1.md"
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    results.write_csv(csv_path)
    mean_delta = float(results["mae_delta"].mean()) if results.height else 0.0
    lines = [
        f"# Cloud Cover Baseline Experiment - {today.isoformat()}",
        "",
        "This is an experiment-only baseline comparison and not a production feature promotion.",
        "",
        f"- Rows: {results.height}",
        f"- Mean MAE delta: {mean_delta:.4f}",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "cloud_cover_baseline_experiment_csv": csv_path,
        "cloud_cover_baseline_experiment_md": md_path,
    }
```

- [ ] **Step 2: Export and add CLI**

Export the builder/writer in `solarstorm/onda2e/__init__.py`.

Add to `solarstorm/__main__.py`:

```python
@app.command("cloud-cover-baseline-experiment")
def cloud_cover_baseline_experiment(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    output_dir: str = typer.Option("./reports/regime-design", help="Output directory"),
    test_years: str = typer.Option("2024,2025", help="Comma-separated walk-forward test years"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
):
    """Write experiment-only cloud-cover baseline comparison artifacts."""
    required = [Path(features_path), Path(labels_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    years = tuple(int(value.strip()) for value in test_years.split(",") if value.strip())
    cps = tuple(value.strip() for value in cp_set.split(",") if value.strip())
    artifacts = build_cloud_cover_baseline_experiment(
        features=pl.read_parquet(features_path),
        labels=pl.read_parquet(labels_path),
        test_years=years,
        cp_set=cps,
    )
    paths = write_cloud_cover_baseline_experiment_artifacts(artifacts, output_dir=output_dir)
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    print(f"Cloud-cover experiment rows: {results.height}")
    print("Feature: cloud_cover_suppression")
    print(f"Cloud-cover report: {paths['cloud_cover_baseline_experiment_md']}")
```

- [ ] **Step 3: Run focused test**

Run:

```powershell
uv run pytest tests/test_cloud_cover_baseline_experiment.py -q
```

Expected: pass.

---

### Task 7: Generate Real Artifacts

**Files:**
- Create/overwrite: `reports/regime-design/regime_deadlock_pivot_decision_v1.csv`
- Create/overwrite: `reports/regime-design/regime_deadlock_pivot_decision_v1.md`
- Create/overwrite: `reports/regime-design/regime_deadlock_superseded_path_v1.csv`
- Create/overwrite: `reports/regime-design/regime_audit_demotions_v1.csv`
- Create/overwrite: `reports/regime-design/regime_audit_demotions_v1.md`
- Create/overwrite: `reports/regime-design/regime_binary_macro_candidate_v1.csv`
- Create/overwrite: `reports/regime-design/regime_binary_macro_candidate_v1.md`
- Create/overwrite: `reports/regime-design/regime_binary_macro_assignments_v1.csv`
- Create/overwrite: `reports/regime-design/regime_binary_macro_assignment_audit_v1.csv`
- Create/overwrite: `reports/regime-design/cloud_cover_baseline_experiment_v1.csv`
- Create/overwrite: `reports/regime-design/cloud_cover_baseline_experiment_v1.md`

- [ ] **Step 1: Run pivot CLI**

Run:

```powershell
uv run python -m solarstorm regime-deadlock-pivot
```

Expected:

- Prints `PIVOT_ACCEPTED`.
- Writes the pivot, superseded-path, and audit-demotion artifacts.

- [ ] **Step 2: Run binary macro CLI**

Run:

```powershell
uv run python -m solarstorm regime-binary-macro-candidate
```

Expected:

- Prints `macro_southerly_flow, macro_non_southerly`.
- Writes the binary candidate artifacts.

- [ ] **Step 3: Run cloud baseline CLI**

Run:

```powershell
uv run python -m solarstorm cloud-cover-baseline-experiment
```

Expected:

- Writes `cloud_cover_baseline_experiment_v1.csv/.md`.
- Keeps `production_status = EXPERIMENT_ONLY`.

---

### Task 8: Update Documentation and ADR-012

**Files:**
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/regime_model_card.md`
- Modify: `docs/onda4_robustness_plan.md`
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update ADR-012**

Add a section named `Generated 2026-06-08 Regime Deadlock Pivot State` that
states:

```markdown
## Generated 2026-06-08 Regime Deadlock Pivot State

The active unlock path now follows `reports/onda2e/regime_deadlock_diagnosis_v1.md`.
The v2.2/v2.3 calm/radiative restoration and threshold-calibration loop is
superseded as the active path for Onda 3 unlock.

New experiment-only artifacts:

- `reports/regime-design/regime_deadlock_pivot_decision_v1.csv`
- `reports/regime-design/regime_deadlock_pivot_decision_v1.md`
- `reports/regime-design/regime_deadlock_superseded_path_v1.csv`
- `reports/regime-design/regime_audit_demotions_v1.csv`
- `reports/regime-design/regime_audit_demotions_v1.md`
- `reports/regime-design/regime_binary_macro_candidate_v1.csv`
- `reports/regime-design/regime_binary_macro_candidate_v1.md`
- `reports/regime-design/regime_binary_macro_assignments_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.md`

`macro_calm_radiative` is retained as an audit segment and no longer blocks the
production macro gate by itself. The production-blocking macro set for the
pivot review is `macro_nw_continuum` and `macro_southerly_flow`.

This does not promote Onda 3, does not alter `data/features.parquet`, and does
not promote `cloud_cover_suppression` to production.
```

- [ ] **Step 2: Update model card and robustness plan**

Record that:

- current regime history is audit history;
- `calm_radiative` is audit-only in the pivot;
- Onda 4 must evaluate the binary candidate and cloud baseline separately;
- no full-day target labels are allowed as live features.

- [ ] **Step 3: Update README, ROADMAP, and CHANGELOG**

Add concise entries pointing to the new pivot artifacts and stating that the
next implementation line is binary macro plus baseline comparison, not v2.4
threshold tuning.

---

### Task 9: Verification

**Files:**
- No new implementation files beyond previous tasks.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
uv run pytest tests/test_regime_deadlock_pivot.py tests/test_regime_binary_macro_candidate.py tests/test_cloud_cover_baseline_experiment.py -q
```

Expected: all pass.

- [ ] **Step 2: Run relevant regime tests**

Run:

```powershell
uv run pytest tests/test_regime_design_validation.py tests/test_regime_classifiability.py tests/test_regime_v23_calm_cloud_signal_validation.py tests/test_robustness.py -q
```

Expected: all pass.

- [ ] **Step 3: Run non-network suite**

Run:

```powershell
uv run pytest -q -m "not network"
```

Expected: all non-network tests pass.

- [ ] **Step 4: Run Ruff**

Run:

```powershell
uv run ruff check .
```

Expected: `All checks passed!`

---

## Parallel-Agent Sprint Split

Use parallel agents only for independent work:

- Agent A: Task 1 and Task 2, pivot decision/audit demotion.
- Agent B: Task 3 and Task 4, binary macro candidate.
- Agent C: Task 5 and Task 6, cloud-cover baseline experiment.
- Agent D: Task 8, documentation updates after Agents A-C finish their artifact names.

The integration worker then runs Task 7 and Task 9 in the main workspace,
reviews generated artifacts, and resolves import/CLI conflicts.

## Completion Criteria

The sprint is complete only when the new artifacts exist, docs name the pivot
as the active path, focused tests pass, relevant regime tests pass, the full
non-network suite passes, and Ruff passes.
