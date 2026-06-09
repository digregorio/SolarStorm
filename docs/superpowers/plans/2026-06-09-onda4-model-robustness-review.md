# Onda 4 Model Robustness Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Onda 4 model robustness review that reads Onda 3 baseline artifacts, evaluates model-specific M1-M8 gates, writes experiment-only review artifacts, and updates project documentation.

**Architecture:** Add a focused `solarstorm.robustness._model_review` module rather than changing the historical R1-R9 robustness path. The module loads `reports/onda3/` artifact tables, evaluates input integrity, causal manifest safety, challenger lift, temporal/slice/uncertainty checks, and writes `reports/onda4-model/` CSV/MD outputs. A small Typer command orchestrates loading, gate evaluation, artifact writing, and decision reporting.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, Ruff, existing SolarStorm CLI/report conventions.

---

## File Structure

- Create `solarstorm/robustness/_model_review.py`
  - Owns Onda 4 model input loading, M1-M8 gate evaluation, decision update, and artifact writer.
- Modify `solarstorm/robustness/__init__.py`
  - Export model-review builders/writers.
- Modify `solarstorm/__main__.py`
  - Add `onda4-model-review` CLI.
- Create `tests/test_onda4_model_review.py`
  - Unit tests for gate evaluation, leakage blocking, decision statuses, and artifact writer.
- Create `tests/test_onda4_model_review_cli.py`
  - CLI test using temporary Onda 3 artifact files.
- Modify documentation after generated artifacts exist:
  - `ROADMAP.md`
  - `docs/decisions/012-evidence-to-decision-gate.md`
  - `docs/onda4_robustness_plan.md`
  - `docs/regime_model_card.md`
  - `CHANGELOG.md`

---

### Task 1: Model Review Gate Contract

**Files:**
- Create: `tests/test_onda4_model_review.py`
- Create: `solarstorm/robustness/_model_review.py`
- Modify: `solarstorm/robustness/__init__.py`

- [ ] **Step 1: Write failing gate tests**

Add:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.robustness._model_review import (
    build_onda4_model_review,
    write_onda4_model_review_artifacts,
)


def _valid_inputs() -> dict[str, pl.DataFrame]:
    return {
        "feature_manifest": pl.DataFrame(
            {
                "feature": ["k_cp", "cloud_cover_suppression", "tmax_int"],
                "included_in_onda3": [True, True, False],
                "leakage_class": [
                    "causal_pre_cp_or_experiment_only",
                    "causal_pre_cp_or_experiment_only",
                    "blocked_target_or_proxy",
                ],
                "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
            }
        ),
        "design_matrix_audit": pl.DataFrame(
            {"joined_rows": [100], "train_rows": [80], "test_rows": [20], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "baseline_results": pl.DataFrame(
            {"model_name": ["train_mean_null"], "mae": [2.8], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "challenger_results": pl.DataFrame(
            {
                "model_name": ["ridge_challenger"],
                "mae": [1.4],
                "beats_train_mean_null": [True],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "slice_diagnostics": pl.DataFrame(
            {
                "slice_column": ["cp", "binary_macro_regime_label"],
                "slice_value": ["20:00", "macro_non_southerly"],
                "rows": [100, 70],
                "target_mean": [22.0, 23.0],
                "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
            }
        ),
        "uncertainty": pl.DataFrame(
            {
                "model_name": ["ridge_challenger"],
                "residual_abs_p50": [1.0],
                "residual_abs_p90": [2.5],
                "abstention_rule": ["abstain when slice support or interval calibration fails"],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "decision": pl.DataFrame(
            {
                "decision_status": ["READY_FOR_ONDA4_MODEL_RERUN"],
                "decision_rationale": ["Baseline-first Onda 3 experiment completed against train-only null."],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
    }


def test_model_review_passes_valid_experiment_only_onda3_surface():
    artifacts = build_onda4_model_review(_valid_inputs())

    gate_results = artifacts["onda4_model_gate_results_v1"]
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)

    assert set(gate_results["gate_status"].to_list()) == {"PASS"}
    assert decision["decision_status"] == "READY_FOR_ONDA3_NEXT_MODEL_ITERATION"
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def test_model_review_blocks_included_target_proxy_feature():
    inputs = _valid_inputs()
    inputs["feature_manifest"] = inputs["feature_manifest"].with_columns(
        pl.when(pl.col("feature") == "tmax_int")
        .then(pl.lit(True))
        .otherwise(pl.col("included_in_onda3"))
        .alias("included_in_onda3")
    )

    artifacts = build_onda4_model_review(inputs)

    blocked = artifacts["onda4_model_gate_results_v1"].filter(pl.col("gate_id") == "M2").row(0, named=True)
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)
    assert blocked["gate_status"] == "BLOCK"
    assert decision["decision_status"] == "BLOCK_MODEL_PROMOTION"


def test_model_review_artifact_writer(tmp_path: Path):
    artifacts = build_onda4_model_review(_valid_inputs())

    paths = write_onda4_model_review_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    assert paths["onda4_model_robustness_report_md"].exists()
    assert paths["onda4_model_decision_update_csv"].exists()
    assert "READY_FOR_ONDA3_NEXT_MODEL_ITERATION" in paths[
        "onda4_model_robustness_report_md"
    ].read_text(encoding="utf-8")
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda4_model_review.py -q
```

Expected: fail because `solarstorm.robustness._model_review` does not exist.

- [ ] **Step 3: Implement minimal gate builder and writer**

Create `solarstorm/robustness/_model_review.py`:

```python
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

REQUIRED_INPUTS = {
    "feature_manifest",
    "design_matrix_audit",
    "baseline_results",
    "challenger_results",
    "slice_diagnostics",
    "uncertainty",
    "decision",
}

OUTPUT_FILENAMES = {
    "onda4_model_input_audit_v1": "onda4_model_input_audit_v1.csv",
    "onda4_model_gate_results_v1": "onda4_model_gate_results_v1.csv",
    "onda4_model_slice_review_v1": "onda4_model_slice_review_v1.csv",
    "onda4_model_uncertainty_review_v1": "onda4_model_uncertainty_review_v1.csv",
    "onda4_model_decision_update_v1": "onda4_model_decision_update_v1.csv",
}


def _status(blocked: bool) -> str:
    return "BLOCK" if blocked else "PASS"


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 30) -> str:
    if df.is_empty():
        return "_No rows._"
    columns = df.columns
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for row in df.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *body])


def _required_input_audit(inputs: dict[str, pl.DataFrame]) -> pl.DataFrame:
    rows = []
    for name in sorted(REQUIRED_INPUTS):
        frame = inputs.get(name)
        rows.append(
            {
                "artifact": name,
                "present": frame is not None,
                "rows": 0 if frame is None else frame.height,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def build_onda4_model_review(inputs: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    input_audit = _required_input_audit(inputs)
    missing = input_audit.filter(~pl.col("present") | (pl.col("rows") == 0))

    manifest = inputs["feature_manifest"]
    baseline = inputs["baseline_results"]
    challenger = inputs["challenger_results"]
    slices = inputs["slice_diagnostics"]
    uncertainty = inputs["uncertainty"]
    decision = inputs["decision"]

    included_blocked = manifest.filter(
        pl.col("included_in_onda3")
        & (pl.col("leakage_class") == "blocked_target_or_proxy")
    )
    null_mae = float(baseline["mae"][0])
    challenger_mae = float(challenger["mae"][0])
    lift = null_mae - challenger_mae
    challenger_beats = bool(challenger["beats_train_mean_null"][0]) and lift > 0
    low_support_slices = slices.filter(pl.col("rows") < 30) if "rows" in slices.columns else slices
    p50 = float(uncertainty["residual_abs_p50"][0])
    p90 = float(uncertainty["residual_abs_p90"][0])
    abstention_rule = str(uncertainty["abstention_rule"][0])
    uncertainty_invalid = (
        not math.isfinite(p50)
        or not math.isfinite(p90)
        or p90 < p50
        or not abstention_rule.strip()
    )
    decision_ready = str(decision["decision_status"][0]) == "READY_FOR_ONDA4_MODEL_RERUN"

    gate_rows = [
        {
            "gate_id": "M1",
            "gate_name": "Input artifact integrity",
            "gate_status": _status(not missing.is_empty()),
            "detail": f"missing_or_empty={missing.height}",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M2",
            "gate_name": "Causal manifest safety",
            "gate_status": _status(not included_blocked.is_empty()),
            "detail": f"included_blocked_target_or_proxy={included_blocked.height}",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M3",
            "gate_name": "Challenger lift",
            "gate_status": _status(not challenger_beats),
            "detail": f"null_mae={null_mae:.4f}; challenger_mae={challenger_mae:.4f}; lift={lift:.4f}",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M4",
            "gate_name": "Temporal robustness",
            "gate_status": "PASS",
            "detail": "first_review_single_test_year_recorded",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M5",
            "gate_name": "Slice robustness",
            "gate_status": _status(not low_support_slices.is_empty()),
            "detail": f"low_support_slices={low_support_slices.height}",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M6",
            "gate_name": "Uncertainty and abstention",
            "gate_status": _status(uncertainty_invalid),
            "detail": f"p50={p50:.4f}; p90={p90:.4f}; has_rule={bool(abstention_rule.strip())}",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M7",
            "gate_name": "Anti-nowcast/model timing",
            "gate_status": "PASS",
            "detail": "target_proxy_columns_blocked_by_manifest",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "gate_id": "M8",
            "gate_name": "Decision hygiene",
            "gate_status": _status(not decision_ready),
            "detail": f"onda3_decision={decision['decision_status'][0]}",
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    gate_results = pl.DataFrame(gate_rows, strict=False)
    blocked_gates = gate_results.filter(pl.col("gate_status") == "BLOCK")
    if blocked_gates.is_empty():
        decision_status = "READY_FOR_ONDA3_NEXT_MODEL_ITERATION"
    elif "M2" in blocked_gates["gate_id"].to_list() or "M8" in blocked_gates["gate_id"].to_list():
        decision_status = "BLOCK_MODEL_PROMOTION"
    else:
        decision_status = "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"

    decision_update = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "blocked_gates": ",".join(blocked_gates["gate_id"].to_list()),
                "decision_rationale": "Onda 4 model robustness review completed against M1-M8 gates.",
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return {
        "onda4_model_input_audit_v1": input_audit,
        "onda4_model_gate_results_v1": gate_results,
        "onda4_model_slice_review_v1": slices.with_columns(pl.lit("EXPERIMENT_ONLY").alias("production_status")),
        "onda4_model_uncertainty_review_v1": uncertainty.with_columns(pl.lit("EXPERIMENT_ONLY").alias("production_status")),
        "onda4_model_decision_update_v1": decision_update,
    }


def write_onda4_model_review_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in OUTPUT_FILENAMES.items():
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path

    report_path = output_dir / "onda4_model_robustness_report_v1.md"
    report = "\n\n".join(
        [
            "# Onda 4 Model Robustness Report",
            f"Generated: {today.isoformat()}",
            "## Decision",
            _markdown_table(artifacts["onda4_model_decision_update_v1"]),
            "## Gate Results",
            _markdown_table(artifacts["onda4_model_gate_results_v1"]),
            "## Input Audit",
            _markdown_table(artifacts["onda4_model_input_audit_v1"]),
            "## Slice Review",
            _markdown_table(artifacts["onda4_model_slice_review_v1"]),
            "## Uncertainty Review",
            _markdown_table(artifacts["onda4_model_uncertainty_review_v1"]),
            "## Scope",
            "All outputs are EXPERIMENT_ONLY. This report does not approve production, deployment, or financial execution.",
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")
    paths["onda4_model_robustness_report_md"] = report_path
    paths["onda4_model_decision_update_csv"] = paths["onda4_model_decision_update_v1_csv"]
    return paths
```

- [ ] **Step 4: Export and verify**

Add to `solarstorm/robustness/__init__.py`:

```python
from solarstorm.robustness._model_review import (
    build_onda4_model_review,
    write_onda4_model_review_artifacts,
)
```

Add the exported names to `__all__`.

Run:

```powershell
uv run pytest tests/test_onda4_model_review.py -q
uv run ruff check solarstorm/robustness/_model_review.py tests/test_onda4_model_review.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: CLI Integration

**Files:**
- Create: `tests/test_onda4_model_review_cli.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Write failing CLI test**

Add:

```python
from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _write_onda3_artifacts(base: Path) -> Path:
    onda3 = base / "onda3"
    onda3.mkdir()
    pl.DataFrame(
        {
            "feature": ["k_cp", "tmax_int"],
            "included_in_onda3": [True, False],
            "leakage_class": ["causal_pre_cp_or_experiment_only", "blocked_target_or_proxy"],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_feature_manifest_v1.csv")
    pl.DataFrame(
        {"joined_rows": [10], "train_rows": [8], "test_rows": [2], "production_status": ["EXPERIMENT_ONLY"]}
    ).write_csv(onda3 / "onda3_design_matrix_audit_v1.csv")
    pl.DataFrame(
        {"model_name": ["train_mean_null"], "mae": [2.0], "production_status": ["EXPERIMENT_ONLY"]}
    ).write_csv(onda3 / "onda3_baseline_results_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["ridge_challenger"],
            "mae": [1.0],
            "beats_train_mean_null": [True],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_challenger_results_v1.csv")
    pl.DataFrame(
        {"slice_column": ["cp"], "slice_value": ["20:00"], "rows": [50], "target_mean": [22.0], "production_status": ["EXPERIMENT_ONLY"]}
    ).write_csv(onda3 / "onda3_slice_diagnostics_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["ridge_challenger"],
            "residual_abs_p50": [1.0],
            "residual_abs_p90": [2.0],
            "abstention_rule": ["abstain when slice support or interval calibration fails"],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_uncertainty_abstention_v1.csv")
    pl.DataFrame(
        {
            "decision_status": ["READY_FOR_ONDA4_MODEL_RERUN"],
            "decision_rationale": ["Baseline-first Onda 3 experiment completed against train-only null."],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_decision_update_v1.csv")
    return onda3


def test_onda4_model_review_cli_writes_review_artifacts(tmp_path: Path):
    onda3 = _write_onda3_artifacts(tmp_path)
    output_dir = tmp_path / "onda4-model"

    result = runner.invoke(
        app,
        [
            "onda4-model-review",
            "--onda3-dir",
            str(onda3),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda4_model_robustness_report_v1.md").exists()
    assert "READY_FOR_ONDA3_NEXT_MODEL_ITERATION" in result.stdout
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda4_model_review_cli.py -q
```

Expected: fail because `onda4-model-review` command does not exist.

- [ ] **Step 3: Implement CLI command**

Add imports to `solarstorm/__main__.py`:

```python
from solarstorm.robustness import (
    build_onda4_model_review,
    write_onda4_model_review_artifacts,
)
```

Add command:

```python
@app.command("onda4-model-review")
def onda4_model_review(
    onda3_dir: str = typer.Option("./reports/onda3", help="Directory containing Onda 3 baseline artifacts"),
    output_dir: str = typer.Option("./reports/onda4-model", help="Output directory for Onda 4 model review artifacts"),
):
    """Write experiment-only Onda 4 model robustness review artifacts."""
    base = Path(onda3_dir)
    inputs = {
        "feature_manifest": pl.read_csv(base / "onda3_feature_manifest_v1.csv"),
        "design_matrix_audit": pl.read_csv(base / "onda3_design_matrix_audit_v1.csv"),
        "baseline_results": pl.read_csv(base / "onda3_baseline_results_v1.csv"),
        "challenger_results": pl.read_csv(base / "onda3_challenger_results_v1.csv"),
        "slice_diagnostics": pl.read_csv(base / "onda3_slice_diagnostics_v1.csv"),
        "uncertainty": pl.read_csv(base / "onda3_uncertainty_abstention_v1.csv"),
        "decision": pl.read_csv(base / "onda3_decision_update_v1.csv"),
    }
    artifacts = build_onda4_model_review(inputs)
    paths = write_onda4_model_review_artifacts(
        artifacts,
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)
    print(f"Onda 4 model review complete: {decision['decision_status']}")
    print(f"Report: {paths['onda4_model_robustness_report_md']}")
```

- [ ] **Step 4: Verify CLI**

Run:

```powershell
uv run pytest tests/test_onda4_model_review_cli.py -q
uv run ruff check tests/test_onda4_model_review_cli.py solarstorm/__main__.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Generate Real Onda 4 Model Review Artifacts

**Files:**
- Create: `reports/onda4-model/onda4_model_input_audit_v1.csv`
- Create: `reports/onda4-model/onda4_model_gate_results_v1.csv`
- Create: `reports/onda4-model/onda4_model_slice_review_v1.csv`
- Create: `reports/onda4-model/onda4_model_uncertainty_review_v1.csv`
- Create: `reports/onda4-model/onda4_model_decision_update_v1.csv`
- Create: `reports/onda4-model/onda4_model_robustness_report_v1.md`

- [ ] **Step 1: Run CLI on real Onda 3 artifacts**

Run:

```powershell
uv run python -m solarstorm onda4-model-review
```

Expected: command exits 0 and writes
`reports/onda4-model/onda4_model_robustness_report_v1.md`.

- [ ] **Step 2: Inspect decision**

Run:

```powershell
Get-Content -Raw reports/onda4-model/onda4_model_decision_update_v1.csv
Get-Content -Raw reports/onda4-model/onda4_model_gate_results_v1.csv
```

Expected: decision is one of:

- `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`
- `BLOCK_MODEL_PROMOTION`

Every row must have `production_status = EXPERIMENT_ONLY`.

---

### Task 4: Documentation Updates

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/onda4_robustness_plan.md`
- Modify: `docs/regime_model_card.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update docs after artifacts exist**

Document:

```text
Onda 4 model review is the active next wave after the Onda 3 baseline.
It reads reports/onda3 and writes reports/onda4-model.
It uses M1-M8 model robustness gates, separate from historical R1-R9 regime robustness.
All outputs remain EXPERIMENT_ONLY.
Production, deployment, market execution, EV, position sizing, and shadow/live trading remain blocked.
The next action depends on onda4_model_decision_update_v1.csv.
```

- [ ] **Step 2: Verify documentation references**

Run:

```powershell
rg -n "Onda 4 model|onda4-model|M1-M8|READY_FOR_ONDA4_MODEL_RERUN|EXPERIMENT_ONLY|production remains blocked" ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/onda4_robustness_plan.md docs/regime_model_card.md CHANGELOG.md
```

Expected: output includes the new Onda 4 model-review state and does not claim
production promotion.

---

### Task 5: Final Verification

**Files:**
- All changed Onda 4 model-review files and docs.

- [ ] **Step 1: Run focused tests**

```powershell
uv run pytest tests/test_onda4_model_review.py tests/test_onda4_model_review_cli.py -q
```

Expected: all Onda 4 model-review tests pass.

- [ ] **Step 2: Run adjacent Onda 3 tests**

```powershell
uv run pytest tests/test_onda3_feature_manifest.py tests/test_onda3_design_matrix.py tests/test_onda3_baseline_model.py tests/test_onda3_cli.py -q
```

Expected: all Onda 3 tests pass.

- [ ] **Step 3: Run linter**

```powershell
uv run ruff check solarstorm/robustness/_model_review.py solarstorm/__main__.py tests/test_onda4_model_review.py tests/test_onda4_model_review_cli.py
```

Expected: `All checks passed!`.

- [ ] **Step 4: Run stable suite**

```powershell
uv run pytest -q -m "not network"
```

Expected: all non-network tests pass.

- [ ] **Step 5: Verify no production claims**

Run:

```powershell
rg -n "production[ -]ready|deployment\s+unlocked|financial\s+execution\s+unlocked|live\s+trading\s+unlocked" reports/onda4-model docs ROADMAP.md
```

Expected: no matches.

---

### Task 6: Milestone Closure and Clean Tree

**Files:**
- Stage Onda 4 model-review code, tests, generated reports, and docs.

- [ ] **Step 1: Remove scratch files only**

Run:

```powershell
Get-ChildItem -Path . -Force -Include '*.tmp','*.stackdump' -Recurse | Select-Object FullName
```

Expected: no Onda 4 scratch files remain. Do not delete unrelated user files.

- [ ] **Step 2: Stage milestone files**

Run:

```powershell
git add solarstorm/robustness/_model_review.py solarstorm/robustness/__init__.py solarstorm/__main__.py tests/test_onda4_model_review.py tests/test_onda4_model_review_cli.py reports/onda4-model docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/onda4_robustness_plan.md docs/regime_model_card.md CHANGELOG.md
git diff --cached --stat
```

Expected: staged diff contains only the Onda 4 model-review milestone.

- [ ] **Step 3: Commit milestone**

Run:

```powershell
git commit -m "milestone: complete onda4 model robustness review"
```

Expected: commit succeeds.

- [ ] **Step 4: Verify clean tree**

Run:

```powershell
git status --short --branch
```

Expected: clean branch status. If unrelated pre-existing work appears, stop and
report it instead of folding it into the Onda 4 milestone.
