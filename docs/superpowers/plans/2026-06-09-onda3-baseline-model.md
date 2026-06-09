# Onda 3 Baseline-First Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Onda 3 experiment surface: causal feature manifest, baseline comparison, simple challenger, uncertainty/abstention diagnostics, and a decision artifact.

**Architecture:** Add a dedicated `solarstorm/onda3/` namespace that reads existing feature, label, and experiment-only binary macro artifacts without mutating production data. The first model layer is deliberately simple: train-only nulls and a regularized linear challenger evaluated by CP, month, binary macro, and lead-time slices. All outputs stay under `reports/onda3/` with `production_status = EXPERIMENT_ONLY`.

**Tech Stack:** Python 3.12, Polars, NumPy, scikit-learn, Typer, pytest, Ruff, existing SolarStorm feature/label/baseline conventions.

---

## File Structure

- Create `solarstorm/onda3/__init__.py`
  - Export Onda 3 builders and writers.
- Create `solarstorm/onda3/_feature_manifest.py`
  - Build causal feature manifest and block leakage-prone columns.
- Create `solarstorm/onda3/_design_matrix.py`
  - Join features, labels, and optional binary macro assignments into a train/test design matrix audit.
- Create `solarstorm/onda3/_baseline_model.py`
  - Fit train-only nulls and a simple regularized challenger.
- Create `solarstorm/onda3/_evaluation.py`
  - Aggregate metrics, uncertainty intervals, abstention flags, and slice diagnostics.
- Create `solarstorm/onda3/_artifacts.py`
  - Write CSV/MD reports under `reports/onda3/`.
- Modify `solarstorm/__main__.py`
  - Add `onda3-baseline-model` CLI.
- Create `tests/test_onda3_feature_manifest.py`
- Create `tests/test_onda3_design_matrix.py`
- Create `tests/test_onda3_baseline_model.py`
- Create `tests/test_onda3_cli.py`
- Update docs only after generated artifacts exist.

---

### Task 1: Feature Manifest Contract

**Files:**
- Create: `tests/test_onda3_feature_manifest.py`
- Create: `solarstorm/onda3/_feature_manifest.py`
- Create: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing leakage tests**

Add:

```python
from __future__ import annotations

import polars as pl

from solarstorm.onda3._feature_manifest import build_onda3_feature_manifest


def test_feature_manifest_allows_only_causal_pre_cp_features():
    features = pl.DataFrame(
        {
            "date_local": ["2025-01-01"],
            "cp": ["20:00"],
            "k_cp": [22],
            "cloud_cover_suppression": [1.5],
            "foehn_score": [72.0],
            "binary_macro_regime_label": ["macro_non_southerly"],
            "remaining_warming": [3.0],
            "tmax_hour": [15],
            "tmax_int": [25],
        }
    )

    manifest = build_onda3_feature_manifest(features)
    by_feature = {row["feature"]: row for row in manifest.iter_rows(named=True)}

    assert by_feature["k_cp"]["included_in_onda3"]
    assert by_feature["cloud_cover_suppression"]["included_in_onda3"]
    assert by_feature["foehn_score"]["included_in_onda3"]
    assert by_feature["binary_macro_regime_label"]["included_in_onda3"]
    assert not by_feature["remaining_warming"]["included_in_onda3"]
    assert by_feature["remaining_warming"]["leakage_class"] == "blocked_target_or_proxy"
    assert not by_feature["tmax_hour"]["included_in_onda3"]
    assert not by_feature["tmax_int"]["included_in_onda3"]
    assert set(manifest["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_feature_manifest.py -q
```

Expected: fail because `solarstorm.onda3` does not exist.

- [ ] **Step 3: Implement minimal manifest builder**

Create:

```python
from __future__ import annotations

import polars as pl

BLOCKED_TARGET_OR_PROXY = {
    "tmax_int",
    "tmax_hour",
    "remaining_warming",
    "tmax_anomaly",
}

IDENTIFIER_COLUMNS = {"date_local", "cp", "month", "season"}

MANIFEST_SCHEMA = {
    "feature": pl.Utf8,
    "included_in_onda3": pl.Boolean,
    "leakage_class": pl.Utf8,
    "feature_role": pl.Utf8,
    "production_status": pl.Utf8,
}


def build_onda3_feature_manifest(features: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for feature in features.columns:
        if feature in IDENTIFIER_COLUMNS:
            included = False
            leakage_class = "identifier"
            role = "join_key"
        elif feature in BLOCKED_TARGET_OR_PROXY:
            included = False
            leakage_class = "blocked_target_or_proxy"
            role = "blocked"
        else:
            included = True
            leakage_class = "causal_pre_cp_or_experiment_only"
            role = "candidate_input"
        rows.append(
            {
                "feature": feature,
                "included_in_onda3": included,
                "leakage_class": leakage_class,
                "feature_role": role,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, schema=MANIFEST_SCHEMA)
```

Create `solarstorm/onda3/__init__.py`:

```python
from solarstorm.onda3._feature_manifest import build_onda3_feature_manifest

__all__ = ["build_onda3_feature_manifest"]
```

- [ ] **Step 4: Verify green**

Run:

```powershell
uv run pytest tests/test_onda3_feature_manifest.py -q
uv run ruff check solarstorm/onda3/_feature_manifest.py tests/test_onda3_feature_manifest.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Design Matrix Audit

**Files:**
- Create: `tests/test_onda3_design_matrix.py`
- Create: `solarstorm/onda3/_design_matrix.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing design matrix test**

Add:

```python
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._design_matrix import build_onda3_design_matrix


def test_design_matrix_joins_labels_and_binary_macro_without_mutating_inputs():
    features = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00"],
            "k_cp": [21, 22],
            "cloud_cover_suppression": [1.0, 2.0],
        }
    )
    labels = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "tmax_int": [24, 25],
        }
    )
    assignments = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00"],
            "binary_macro_regime_label": ["macro_non_southerly", "macro_southerly_flow"],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    )

    matrix, audit = build_onda3_design_matrix(
        features=features,
        labels=labels,
        binary_assignments=assignments,
        train_end=dt.date(2024, 12, 31),
        test_start=dt.date(2025, 1, 1),
    )

    assert matrix.height == 2
    assert "binary_macro_regime_label" in matrix.columns
    assert matrix.filter(pl.col("fold") == "train").height == 1
    assert matrix.filter(pl.col("fold") == "test").height == 1
    assert set(audit["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert audit.row(0, named=True)["joined_rows"] == 2
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_design_matrix.py -q
```

Expected: fail because `build_onda3_design_matrix` does not exist.

- [ ] **Step 3: Implement design matrix builder**

Create:

```python
from __future__ import annotations

import datetime as dt

import polars as pl


def _ensure_date(df: pl.DataFrame) -> pl.DataFrame:
    if "date_local" in df.columns and df.schema["date_local"] == pl.Utf8:
        return df.with_columns(pl.col("date_local").str.to_date())
    return df


def build_onda3_design_matrix(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    binary_assignments: pl.DataFrame | None,
    train_end: dt.date,
    test_start: dt.date,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    features = _ensure_date(features)
    labels = _ensure_date(labels)
    matrix = features.join(labels.select(["date_local", "tmax_int"]), on="date_local", how="inner")
    if binary_assignments is not None and binary_assignments.height > 0:
        assignments = _ensure_date(binary_assignments).select(
            ["date_local", "cp", "binary_macro_regime_label"]
        )
        matrix = matrix.join(assignments, on=["date_local", "cp"], how="left")
    matrix = matrix.with_columns(
        pl.when(pl.col("date_local") <= train_end)
        .then(pl.lit("train"))
        .when(pl.col("date_local") >= test_start)
        .then(pl.lit("test"))
        .otherwise(pl.lit("gap"))
        .alias("fold")
    )
    audit = pl.DataFrame(
        [
            {
                "input_feature_rows": features.height,
                "input_label_rows": labels.height,
                "joined_rows": matrix.height,
                "train_rows": matrix.filter(pl.col("fold") == "train").height,
                "test_rows": matrix.filter(pl.col("fold") == "test").height,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return matrix, audit
```

- [ ] **Step 4: Export and verify**

Add to `solarstorm/onda3/__init__.py`:

```python
from solarstorm.onda3._design_matrix import build_onda3_design_matrix
```

Run:

```powershell
uv run pytest tests/test_onda3_design_matrix.py tests/test_onda3_feature_manifest.py -q
uv run ruff check solarstorm/onda3 tests/test_onda3_design_matrix.py tests/test_onda3_feature_manifest.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Baseline and Challenger Evaluation

**Files:**
- Create: `tests/test_onda3_baseline_model.py`
- Create: `solarstorm/onda3/_baseline_model.py`
- Create: `solarstorm/onda3/_evaluation.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing model comparison test**

Add:

```python
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._baseline_model import run_onda3_baseline_model
from solarstorm.onda3._evaluation import build_onda3_slice_diagnostics


def test_baseline_model_reports_null_challenger_and_slice_diagnostics():
    rows = []
    for i in range(20):
        rows.append(
            {
                "date_local": dt.date(2024 if i < 14 else 2025, 1, (i % 14) + 1),
                "cp": "20:00",
                "k_cp": 20 + (i % 3),
                "cloud_cover_suppression": float(i % 4),
                "tmax_int": 21 + (i % 5),
                "fold": "train" if i < 14 else "test",
                "binary_macro_regime_label": "macro_non_southerly",
            }
        )
    matrix = pl.DataFrame(rows)

    results, uncertainty = run_onda3_baseline_model(
        matrix,
        feature_columns=["k_cp", "cloud_cover_suppression"],
        target_column="tmax_int",
    )

    assert set(results["model_name"].to_list()) == {"train_mean_null", "ridge_challenger"}
    assert results.filter(pl.col("model_name") == "ridge_challenger").height == 1
    assert "mae" in results.columns
    assert "beats_train_mean_null" in results.columns
    assert uncertainty.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"

    diagnostics = build_onda3_slice_diagnostics(
        matrix,
        slice_columns=["cp", "binary_macro_regime_label"],
    )
    assert diagnostics.row(0, named=True)["slice_column"] == "cp"
    assert set(diagnostics["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_baseline_model.py -q
```

Expected: fail because model runner does not exist.

- [ ] **Step 3: Implement minimal baseline/challenger runner**

Create:

```python
from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error


def run_onda3_baseline_model(
    matrix: pl.DataFrame,
    *,
    feature_columns: list[str],
    target_column: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    train = matrix.filter(pl.col("fold") == "train")
    test = matrix.filter(pl.col("fold") == "test")
    train_y = train[target_column].to_numpy()
    test_y = test[target_column].to_numpy()
    null_pred = np.full(test.height, float(np.mean(train_y)))
    null_mae = float(mean_absolute_error(test_y, null_pred))

    train_x = train.select(feature_columns).to_numpy()
    test_x = test.select(feature_columns).to_numpy()
    model = Ridge(alpha=1.0)
    model.fit(train_x, train_y)
    challenger_pred = model.predict(test_x)
    challenger_mae = float(mean_absolute_error(test_y, challenger_pred))

    results = pl.DataFrame(
        [
            {
                "model_name": "train_mean_null",
                "cp": "ALL",
                "mae": null_mae,
                "beats_train_mean_null": False,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "model_name": "ridge_challenger",
                "cp": "ALL",
                "mae": challenger_mae,
                "beats_train_mean_null": challenger_mae < null_mae,
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )
    residuals = test_y - challenger_pred
    uncertainty = pl.DataFrame(
        [
            {
                "model_name": "ridge_challenger",
                "residual_abs_p50": float(np.quantile(np.abs(residuals), 0.5)),
                "residual_abs_p90": float(np.quantile(np.abs(residuals), 0.9)),
                "abstention_rule": "abstain when slice support or interval calibration fails",
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return results, uncertainty
```

Create `solarstorm/onda3/_evaluation.py`:

```python
from __future__ import annotations

import polars as pl


def build_onda3_slice_diagnostics(
    matrix: pl.DataFrame,
    *,
    slice_columns: list[str],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for column in slice_columns:
        if column not in matrix.columns:
            continue
        grouped = (
            matrix.group_by(column)
            .agg(
                pl.len().alias("rows"),
                pl.col("tmax_int").mean().alias("target_mean"),
            )
            .sort(column)
        )
        for row in grouped.iter_rows(named=True):
            rows.append(
                {
                    "slice_column": column,
                    "slice_value": str(row[column]),
                    "rows": row["rows"],
                    "target_mean": row["target_mean"],
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return pl.DataFrame(rows, strict=False)
```

- [ ] **Step 4: Export and verify**

Add to `solarstorm/onda3/__init__.py`:

```python
from solarstorm.onda3._baseline_model import run_onda3_baseline_model
from solarstorm.onda3._evaluation import build_onda3_slice_diagnostics
```

Run:

```powershell
uv run pytest tests/test_onda3_baseline_model.py -q
uv run ruff check solarstorm/onda3 tests/test_onda3_baseline_model.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 4: Artifact Writer and CLI

**Files:**
- Create: `tests/test_onda3_cli.py`
- Create: `solarstorm/onda3/_artifacts.py`
- Modify: `solarstorm/__main__.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing writer/CLI tests**

Add:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda3._artifacts import write_onda3_baseline_artifacts

runner = CliRunner()


def test_onda3_artifact_writer(tmp_path: Path):
    artifacts = {
        "onda3_feature_manifest_v1": pl.DataFrame({"feature": ["k_cp"], "production_status": ["EXPERIMENT_ONLY"]}),
        "onda3_design_matrix_audit_v1": pl.DataFrame({"joined_rows": [2], "production_status": ["EXPERIMENT_ONLY"]}),
        "onda3_baseline_results_v1": pl.DataFrame({"model_name": ["train_mean_null"], "mae": [1.0], "production_status": ["EXPERIMENT_ONLY"]}),
        "onda3_challenger_results_v1": pl.DataFrame({"model_name": ["ridge_challenger"], "mae": [0.9], "production_status": ["EXPERIMENT_ONLY"]}),
        "onda3_uncertainty_abstention_v1": pl.DataFrame({"model_name": ["ridge_challenger"], "production_status": ["EXPERIMENT_ONLY"]}),
        "onda3_decision_update_v1": pl.DataFrame({"decision_status": ["KEEP_IN_ONDA3_EXPERIMENT_REVIEW"], "production_status": ["EXPERIMENT_ONLY"]}),
    }

    paths = write_onda3_baseline_artifacts(artifacts, output_dir=tmp_path, today=dt.date(2026, 6, 9))

    assert paths["onda3_decision_update_csv"].exists()
    assert paths["onda3_report_md"].exists()
    assert "KEEP_IN_ONDA3_EXPERIMENT_REVIEW" in paths["onda3_report_md"].read_text(encoding="utf-8")


def test_onda3_cli_writes_report_from_local_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3"

    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00", "20:00"],
            "k_cp": [20, 21, 22],
            "cloud_cover_suppression": [0.5, 1.0, 1.5],
        }
    ).write_parquet(features_path)
    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "tmax_int": [22, 23, 24],
        }
    ).write_parquet(labels_path)
    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00", "20:00"],
            "binary_macro_regime_label": [
                "macro_non_southerly",
                "macro_non_southerly",
                "macro_southerly_flow",
            ],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-baseline-model",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2024-12-31",
            "--test-start",
            "2025-01-01",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_baseline_model_report_v1.md").exists()
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_cli.py -q
```

Expected: fail because writer does not exist.

- [ ] **Step 3: Implement writer and CLI command**

Create `solarstorm/onda3/_artifacts.py`:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl


ARTIFACT_FILENAMES = {
    "onda3_feature_manifest_v1": "onda3_feature_manifest_v1.csv",
    "onda3_design_matrix_audit_v1": "onda3_design_matrix_audit_v1.csv",
    "onda3_baseline_results_v1": "onda3_baseline_results_v1.csv",
    "onda3_challenger_results_v1": "onda3_challenger_results_v1.csv",
    "onda3_slice_diagnostics_v1": "onda3_slice_diagnostics_v1.csv",
    "onda3_uncertainty_abstention_v1": "onda3_uncertainty_abstention_v1.csv",
    "onda3_decision_update_v1": "onda3_decision_update_v1.csv",
}


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 20) -> str:
    if df.is_empty():
        return "_No rows._"
    rows = df.head(max_rows).iter_rows(named=True)
    columns = df.columns
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def write_onda3_baseline_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in ARTIFACT_FILENAMES.items():
        frame = artifacts[artifact_name]
        path = output_dir / filename
        frame.write_csv(path)
        paths[f"{artifact_name}_csv"] = path

    decision = artifacts["onda3_decision_update_v1"]
    report_path = output_dir / "onda3_baseline_model_report_v1.md"
    report = "\n\n".join(
        [
            "# Onda 3 Baseline Model Report",
            f"Generated: {today.isoformat()}",
            "## Decision",
            _markdown_table(decision),
            "## Baseline Results",
            _markdown_table(artifacts["onda3_baseline_results_v1"]),
            "## Challenger Results",
            _markdown_table(artifacts["onda3_challenger_results_v1"]),
            "## Slice Diagnostics",
            _markdown_table(artifacts["onda3_slice_diagnostics_v1"]),
            "## Uncertainty and Abstention",
            _markdown_table(artifacts["onda3_uncertainty_abstention_v1"]),
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")
    paths["onda3_report_md"] = report_path
    paths["onda3_decision_update_csv"] = paths["onda3_decision_update_v1_csv"]
    return paths
```

Add a Typer command:

```python
@app.command("onda3-baseline-model")
def onda3_baseline_model(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    binary_assignments_path: str = typer.Option("./reports/regime-design/regime_binary_macro_assignments_v1.csv"),
    output_dir: str = typer.Option("./reports/onda3"),
    train_end: str = typer.Option("2025-12-31"),
    test_start: str = typer.Option("2026-01-01"),
):
    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    binary_assignments = (
        pl.read_csv(binary_assignments_path)
        if Path(binary_assignments_path).exists()
        else None
    )
    manifest = build_onda3_feature_manifest(features)
    matrix, audit = build_onda3_design_matrix(
        features=features,
        labels=labels,
        binary_assignments=binary_assignments,
        train_end=dt.date.fromisoformat(train_end),
        test_start=dt.date.fromisoformat(test_start),
    )
    feature_columns = [
        row["feature"]
        for row in manifest.filter(pl.col("included_in_onda3")).iter_rows(named=True)
        if row["feature"] in matrix.columns and matrix.schema[row["feature"]].is_numeric()
    ]
    results, uncertainty = run_onda3_baseline_model(
        matrix,
        feature_columns=feature_columns,
        target_column="tmax_int",
    )
    baseline_results = results.filter(pl.col("model_name") == "train_mean_null")
    challenger_results = results.filter(pl.col("model_name") == "ridge_challenger")
    slice_diagnostics = build_onda3_slice_diagnostics(
        matrix,
        slice_columns=["cp", "binary_macro_regime_label"],
    )
    challenger_beats = bool(
        challenger_results.select(pl.col("beats_train_mean_null").all()).item()
    )
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_ONDA4_MODEL_RERUN"
                    if challenger_beats
                    else "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
                ),
                "decision_rationale": "Baseline-first Onda 3 experiment completed against train-only null.",
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    paths = write_onda3_baseline_artifacts(
        {
            "onda3_feature_manifest_v1": manifest,
            "onda3_design_matrix_audit_v1": audit,
            "onda3_baseline_results_v1": baseline_results,
            "onda3_challenger_results_v1": challenger_results,
            "onda3_slice_diagnostics_v1": slice_diagnostics,
            "onda3_uncertainty_abstention_v1": uncertainty,
            "onda3_decision_update_v1": decision,
        },
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    typer.echo(f"Wrote {paths['onda3_report_md']}")
```

Add these imports near the existing Onda imports in `solarstorm/__main__.py`:

```python
from solarstorm.onda3 import (
    build_onda3_design_matrix,
    build_onda3_feature_manifest,
    build_onda3_slice_diagnostics,
    run_onda3_baseline_model,
    write_onda3_baseline_artifacts,
)
```

Add to `solarstorm/onda3/__init__.py`:

```python
from solarstorm.onda3._artifacts import write_onda3_baseline_artifacts

__all__ = [
    "build_onda3_design_matrix",
    "build_onda3_feature_manifest",
    "build_onda3_slice_diagnostics",
    "run_onda3_baseline_model",
    "write_onda3_baseline_artifacts",
]
```

- [ ] **Step 4: Verify CLI path**

Run:

```powershell
uv run pytest tests/test_onda3_cli.py -q
uv run ruff check solarstorm/onda3 tests/test_onda3_cli.py solarstorm/__main__.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 5: Documentation and Decision Updates

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/regime_model_card.md`
- Modify: `docs/onda4_robustness_plan.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update docs after artifacts exist**

Document:

```text
Onda 3 design review is eligible, not approved for production.
The binary macro candidate is EXPERIMENT_ONLY.
The first Onda 3 implementation is baseline-first and must beat the best null.
macro_non_southerly remains a weak-sensitivity segment requiring continuous features.
No financial execution or deployment work is unlocked.
```

- [ ] **Step 2: Verify documentation references**

Run:

```powershell
rg -n "Onda 3|READY_FOR_ONDA3_DESIGN_REVIEW|macro_non_southerly|EXPERIMENT_ONLY" ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/regime_model_card.md docs/onda4_robustness_plan.md CHANGELOG.md
```

Expected: output includes the new Onda 3 baseline-first state and does not claim production promotion.

---

### Task 6: Final Verification

**Files:**
- All changed Onda 3 files and docs.

- [ ] **Step 1: Run focused tests**

```powershell
uv run pytest tests/test_onda3_feature_manifest.py tests/test_onda3_design_matrix.py tests/test_onda3_baseline_model.py tests/test_onda3_cli.py -q
```

Expected: all Onda 3 tests pass.

- [ ] **Step 2: Run adjacent regime validation tests**

```powershell
uv run pytest tests/test_regime_binary_macro_validation.py tests/test_regime_binary_macro_candidate.py -q
```

Expected: all binary macro tests pass.

- [ ] **Step 3: Run linter**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/onda2e/_regime_binary_macro_validation.py tests/test_onda3_feature_manifest.py tests/test_onda3_design_matrix.py tests/test_onda3_baseline_model.py tests/test_onda3_cli.py tests/test_regime_binary_macro_validation.py solarstorm/__main__.py
```

Expected: `All checks passed!`.

- [ ] **Step 4: Run CLI on real local artifacts**

```powershell
uv run python -m solarstorm onda3-baseline-model
```

Expected: command exits 0 and writes `reports/onda3/onda3_baseline_model_report_v1.md`.

- [ ] **Step 5: Do not claim production readiness**

Before final handoff, confirm:

```powershell
rg -n "production[ -]ready|deployment\s+unlocked|financial\s+execution\s+unlocked" reports/onda3 docs ROADMAP.md
```

Expected: no matches.

---

### Task 7: Milestone Closure and Clean Tree

**Files:**
- Stage: `solarstorm/onda3/`
- Stage: `tests/test_onda3_feature_manifest.py`
- Stage: `tests/test_onda3_design_matrix.py`
- Stage: `tests/test_onda3_baseline_model.py`
- Stage: `tests/test_onda3_cli.py`
- Stage: `reports/onda3/`
- Stage: `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`
- Stage: `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`
- Stage: `ROADMAP.md`
- Stage: `docs/decisions/012-evidence-to-decision-gate.md`
- Stage: `docs/regime_model_card.md`
- Stage: `docs/onda4_robustness_plan.md`
- Stage: `CHANGELOG.md`

- [ ] **Step 1: Inspect the final working tree**

Run:

```powershell
git status --short
```

Expected: only intended Onda 3 baseline milestone files are listed. If unrelated
pre-existing files are still dirty, do not revert them. Record them separately
and ask before folding them into the milestone.

- [ ] **Step 2: Remove generated scratch files only**

Run:

```powershell
Get-ChildItem -Path . -Force -Include '*.tmp','*.stackdump' -Recurse | Select-Object FullName
```

Expected: no Onda 3 scratch files remain. If the command lists unrelated
pre-existing files such as `bash.exe.stackdump`, do not delete them unless the
milestone owner explicitly approves.

- [ ] **Step 3: Stage the Onda 3 milestone**

Run:

```powershell
git add solarstorm/onda3 tests/test_onda3_feature_manifest.py tests/test_onda3_design_matrix.py tests/test_onda3_baseline_model.py tests/test_onda3_cli.py reports/onda3 docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md docs/superpowers/plans/2026-06-09-onda3-baseline-model.md ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/regime_model_card.md docs/onda4_robustness_plan.md CHANGELOG.md
git diff --cached --stat
```

Expected: staged diff contains the Onda 3 baseline implementation, generated
Onda 3 artifacts, and documentation/decision updates for this milestone.

- [ ] **Step 4: Commit the milestone**

Run:

```powershell
git commit -m "milestone: complete onda3 baseline model"
```

Expected: commit succeeds and records the Onda 3 baseline as one coherent
milestone.

- [ ] **Step 5: Verify the milestone tree is clean**

Run:

```powershell
git status --short
```

Expected: no output. If there is output, the milestone is not closed. Either
stage and commit intended Onda 3 files, remove approved scratch files, or leave
unrelated pre-existing work out of scope and explicitly report that the global
tree cannot be clean without a separate cleanup decision.
