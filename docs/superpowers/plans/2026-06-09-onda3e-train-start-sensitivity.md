# Onda 3E Train-Start Sensitivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Onda 3E, an experiment-only train-start sensitivity runner that compares the current 2009-start Onda 3D interaction surface against a 2012-start surface before any Open-Meteo integration.

**Architecture:** Add a focused `solarstorm.onda3._train_start_sensitivity` module that reuses the existing Onda 3D interaction builder, enriches predictions with exact-bracket and regime summaries, and writes a separate report surface under `reports/onda3-train-start-sensitivity/`. Add a Typer CLI command to load local artifacts, run both train-start variants, write CSV/Markdown outputs, and print the decision status.

**Tech Stack:** Python 3.12, Polars, NumPy through the existing Onda 3 ridge helpers, Typer, pytest, Ruff.

---

## File Structure

- Create `solarstorm/onda3/_train_start_sensitivity.py`
  - Train-start variant config, matrix preparation, Onda 3D runner orchestration,
    exact-bracket metrics, regime summaries, comparison table, decision update,
    Markdown/CSV writer.
- Modify `solarstorm/onda3/__init__.py`
  - Export `build_onda3_train_start_sensitivity` and
    `write_onda3_train_start_sensitivity_artifacts`.
- Modify `solarstorm/__main__.py`
  - Add `onda3-train-start-sensitivity` CLI.
- Create `tests/test_onda3_train_start_sensitivity.py`
  - Unit tests for variant filtering, bracket metrics, comparison decision, and writer.
- Create `tests/test_onda3_train_start_sensitivity_cli.py`
  - CLI smoke test with temporary local artifacts.
- Generate `reports/onda3-train-start-sensitivity/`
  - Real experiment artifacts after tests pass.
- Update docs after generation:
  - `ROADMAP.md`
  - `CHANGELOG.md`

---

### Task 1: Train-Start Variant Runner

**Files:**
- Create: `tests/test_onda3_train_start_sensitivity.py`
- Create: `solarstorm/onda3/_train_start_sensitivity.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing tests for variant filtering and model rows**

Create `tests/test_onda3_train_start_sensitivity.py` with:

```python
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._train_start_sensitivity import (
    TrainStartVariant,
    build_train_start_scope,
    filter_matrix_for_train_start,
)


def _matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00"):
        for year in (2010, 2011, 2012, 2013, 2022, 2023):
            for day in range(1, 4):
                rows.append(
                    {
                        "date_local": dt.date(year, 1, day),
                        "cp": cp,
                        "k_cp": float(day + year - 2000),
                        "foehn_score": float(day * 10),
                        "cloud_cover_suppression": float(4 - day),
                        "binary_macro_regime_label": (
                            "macro_non_southerly"
                            if day % 2
                            else "macro_southerly_flow"
                        ),
                        "tmax_int": float(day + year - 1999),
                    }
                )
    return pl.DataFrame(rows)


def test_filter_matrix_for_train_start_removes_sparse_early_years():
    variant = TrainStartVariant(
        variant_id="continuous_2012_start",
        train_start=dt.date(2012, 1, 1),
    )

    filtered = filter_matrix_for_train_start(_matrix(), variant)

    assert filtered["date_local"].min() == dt.date(2012, 1, 1)
    assert 2010 not in filtered["date_local"].dt.year().unique().to_list()
    assert 2011 not in filtered["date_local"].dt.year().unique().to_list()


def test_build_train_start_scope_reports_train_and_test_periods():
    scope = build_train_start_scope(
        _matrix(),
        variants=[
            TrainStartVariant(
                variant_id="continuous_2012_start",
                train_start=dt.date(2012, 1, 1),
            )
        ],
        test_years=[2023],
    )

    row = scope.row(0, named=True)
    assert row["variant_id"] == "continuous_2012_start"
    assert row["test_year"] == 2023
    assert row["train_period"] == "2012-01-01 to 2022-12-31"
    assert row["test_period"] == "2023-01-01 to 2023-01-03"
    assert row["production_status"] == "EXPERIMENT_ONLY"
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity.py -q
```

Expected: fail because `solarstorm.onda3._train_start_sensitivity` does not exist.

- [ ] **Step 3: Implement variant helpers**

Create `solarstorm/onda3/_train_start_sensitivity.py` with:

```python
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class TrainStartVariant:
    variant_id: str
    train_start: dt.date


DEFAULT_TRAIN_START_VARIANTS = (
    TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
    TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
)


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    if "date_local" in frame.columns and frame.schema["date_local"] == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    return frame


def filter_matrix_for_train_start(
    matrix: pl.DataFrame,
    variant: TrainStartVariant,
) -> pl.DataFrame:
    matrix = _ensure_date(matrix)
    return matrix.filter(pl.col("date_local") >= variant.train_start)


def _period_text(frame: pl.DataFrame) -> str:
    if frame.is_empty():
        return "not_available"
    return f"{frame['date_local'].min().isoformat()} to {frame['date_local'].max().isoformat()}"


def build_train_start_scope(
    matrix: pl.DataFrame,
    *,
    variants: list[TrainStartVariant],
    test_years: list[int],
) -> pl.DataFrame:
    matrix = _ensure_date(matrix)
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    rows: list[dict[str, object]] = []
    for variant in variants:
        filtered = filter_matrix_for_train_start(dated, variant)
        for test_year in test_years:
            train = filtered.filter(pl.col("_year") < test_year)
            test = filtered.filter(pl.col("_year") == test_year)
            rows.append(
                {
                    "variant_id": variant.variant_id,
                    "train_start": variant.train_start.isoformat(),
                    "test_year": test_year,
                    "train_period": _period_text(train),
                    "test_period": _period_text(test),
                    "n_train_rows": train.height,
                    "n_test_rows": test.height,
                    "n_train_days": train.select("date_local").n_unique(),
                    "n_test_days": test.select("date_local").n_unique(),
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return pl.DataFrame(rows, strict=False)
```

- [ ] **Step 4: Verify helper tests**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity.py -q
uv run ruff check solarstorm/onda3/_train_start_sensitivity.py tests/test_onda3_train_start_sensitivity.py
```

Expected: helper tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Build Full Experiment Artifacts

**Files:**
- Modify: `tests/test_onda3_train_start_sensitivity.py`
- Modify: `solarstorm/onda3/_train_start_sensitivity.py`

- [ ] **Step 1: Extend tests for full artifact builder**

Append tests:

```python
from solarstorm.onda3._train_start_sensitivity import (
    build_onda3_train_start_sensitivity,
)


def test_build_onda3_train_start_sensitivity_emits_two_variants():
    artifacts = build_onda3_train_start_sensitivity(
        _matrix(),
        test_years=[2023],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        variants=[
            TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
            TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
        ],
    )

    results = artifacts["onda3_train_start_model_results_v1"]
    predictions = artifacts["onda3_train_start_predictions_v1"]
    decision = artifacts["onda3_train_start_decision_update_v1"].row(0, named=True)

    assert set(results["variant_id"].to_list()) == {
        "legacy_2009_start",
        "continuous_2012_start",
    }
    assert set(predictions["variant_id"].to_list()) == {
        "legacy_2009_start",
        "continuous_2012_start",
    }
    assert decision["decision_status"] in {
        "CARRY_2012_START_TO_ONDA3F",
        "KEEP_2009_START_FOR_ONDA3F",
        "KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION",
    }
    assert decision["production_status"] == "EXPERIMENT_ONLY"
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity.py::test_build_onda3_train_start_sensitivity_emits_two_variants -q
```

Expected: fail because `build_onda3_train_start_sensitivity` does not exist.

- [ ] **Step 3: Implement artifact builder**

In `solarstorm/onda3/_train_start_sensitivity.py`, import and reuse:

```python
from solarstorm.onda3._interactions import build_onda3_interaction_iteration
from solarstorm.onda3._model_attempt_review import (
    build_month_cp_bracket_summary,
    build_month_day_bracket_summary,
    build_overall_bracket_summary,
    build_regime_cp_performance_summary,
    build_regime_performance_summary,
    enrich_predictions_with_brackets,
)
```

Implement:

```python
def build_onda3_train_start_sensitivity(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    variants: list[TrainStartVariant] | None = None,
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    ...
```

Behavior:

- default variants are `DEFAULT_TRAIN_START_VARIANTS`;
- filter matrix by variant train start;
- call `build_onda3_interaction_iteration` for each variant;
- add `variant_id` and `train_start` columns to model results and predictions;
- enrich predictions with half-up bracket fields;
- produce:
  - `onda3_train_start_scope_v1`
  - `onda3_train_start_model_results_v1`
  - `onda3_train_start_predictions_v1`
  - `onda3_train_start_bracket_overall_v1`
  - `onda3_train_start_bracket_by_month_day_v1`
  - `onda3_train_start_bracket_by_month_cp_v1`
  - `onda3_train_start_regime_performance_v1`
  - `onda3_train_start_regime_by_cp_v1`
  - `onda3_train_start_comparison_v1`
  - `onda3_train_start_decision_update_v1`

Comparison logic:

- compute weighted challenger MAE by variant from `n_test` weights;
- compute `any_cp_exact_pct` and `cp23_exact_pct` from bracket overall;
- set decision:
  - `CARRY_2012_START_TO_ONDA3F` if 2012-start improves weighted MAE by at least
    `0.01` and does not reduce `any_cp_exact_pct` by more than `0.25` percentage
    points;
  - `KEEP_2009_START_FOR_ONDA3F` if legacy-start improves weighted MAE by at
    least `0.01` under the same bracket guard;
  - otherwise `KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION`.

- [ ] **Step 4: Verify full builder**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity.py -q
uv run ruff check solarstorm/onda3/_train_start_sensitivity.py tests/test_onda3_train_start_sensitivity.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Artifact Writer and CLI

**Files:**
- Create: `tests/test_onda3_train_start_sensitivity_cli.py`
- Modify: `solarstorm/onda3/_train_start_sensitivity.py`
- Modify: `solarstorm/onda3/__init__.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_onda3_train_start_sensitivity_cli.py`:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_onda3_train_start_sensitivity_cli_writes_report(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-train-start-sensitivity"

    features = []
    labels = []
    assignments = []
    for cp in ("20:00", "21:00"):
        for year in (2010, 2011, 2012, 2013, 2022, 2023):
            for day in range(1, 5):
                date = dt.date(year, 1, day)
                macro = "macro_non_southerly" if day % 2 else "macro_southerly_flow"
                features.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "k_cp": float(day + year - 2000),
                        "foehn_score": float(day * 10),
                        "cloud_cover_suppression": float(5 - day),
                    }
                )
                labels.append({"date_local": date, "tmax_int": float(day + year - 1999)})
                assignments.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "binary_macro_regime_label": macro,
                    }
                )

    pl.DataFrame(features).write_parquet(features_path)
    pl.DataFrame(labels).unique("date_local").write_parquet(labels_path)
    pl.DataFrame(assignments).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-train-start-sensitivity",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2023",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_train_start_sensitivity_report_v1.md").exists()
    assert (output_dir / "onda3_train_start_decision_update_v1.csv").exists()
    assert "Onda 3E train-start sensitivity complete" in result.stdout
```

- [ ] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity_cli.py -q
```

Expected: fail because CLI/writer do not exist.

- [ ] **Step 3: Implement writer**

In `solarstorm/onda3/_train_start_sensitivity.py`, add:

```python
TRAIN_START_FILENAMES = {
    "onda3_train_start_scope_v1": "onda3_train_start_scope_v1.csv",
    "onda3_train_start_model_results_v1": "onda3_train_start_model_results_v1.csv",
    "onda3_train_start_predictions_v1": "onda3_train_start_predictions_v1.csv",
    "onda3_train_start_bracket_overall_v1": "onda3_train_start_bracket_overall_v1.csv",
    "onda3_train_start_bracket_by_month_day_v1": "onda3_train_start_bracket_by_month_day_v1.csv",
    "onda3_train_start_bracket_by_month_cp_v1": "onda3_train_start_bracket_by_month_cp_v1.csv",
    "onda3_train_start_regime_performance_v1": "onda3_train_start_regime_performance_v1.csv",
    "onda3_train_start_regime_by_cp_v1": "onda3_train_start_regime_by_cp_v1.csv",
    "onda3_train_start_comparison_v1": "onda3_train_start_comparison_v1.csv",
    "onda3_train_start_decision_update_v1": "onda3_train_start_decision_update_v1.csv",
}
```

Add `write_onda3_train_start_sensitivity_artifacts(...)` that:

- creates output directory;
- writes each CSV;
- writes matching small Markdown tables;
- writes `onda3_train_start_sensitivity_report_v1.md`;
- includes the statement: `Open-Meteo forecast data is not integrated.`

- [ ] **Step 4: Export functions**

Update `solarstorm/onda3/__init__.py`:

```python
from solarstorm.onda3._train_start_sensitivity import (
    build_onda3_train_start_sensitivity,
    write_onda3_train_start_sensitivity_artifacts,
)
```

Add both names to `__all__`.

- [ ] **Step 5: Implement CLI**

In `solarstorm/__main__.py`, import the two functions and add:

```python
@app.command("onda3-train-start-sensitivity")
def onda3_train_start_sensitivity(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    binary_assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv"
    ),
    output_dir: str = typer.Option("./reports/onda3-train-start-sensitivity"),
    test_years: str = typer.Option("2023,2024,2025"),
):
    ...
```

The CLI must:

- load features and labels;
- join labels on `date_local`;
- join binary assignments on `date_local, cp` when present;
- build the Onda 3 feature manifest and select included numeric features;
- add `binary_macro_regime_label` as categorical when present;
- parse `test_years`;
- build and write artifacts;
- print decision status and report path.

- [ ] **Step 6: Verify CLI**

Run:

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity_cli.py -q
uv run ruff check solarstorm/onda3/_train_start_sensitivity.py solarstorm/onda3/__init__.py solarstorm/__main__.py tests/test_onda3_train_start_sensitivity_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 4: Generate Real Onda 3E Artifacts

**Files:**
- Create: `reports/onda3-train-start-sensitivity/`

- [ ] **Step 1: Run CLI on local project artifacts**

Run:

```powershell
uv run tmax onda3-train-start-sensitivity --features-path ./data/features.parquet --labels-path ./data/labels.parquet --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir ./reports/onda3-train-start-sensitivity --test-years 2023,2024,2025
```

Expected: command exits 0 and prints:

```text
Onda 3E train-start sensitivity complete: <decision_status>
Open-Meteo forecast data is not integrated in this experiment.
Report: reports\onda3-train-start-sensitivity\onda3_train_start_sensitivity_report_v1.md
```

- [ ] **Step 2: Inspect critical outputs**

Run:

```powershell
Get-Content -Raw reports/onda3-train-start-sensitivity/onda3_train_start_decision_update_v1.csv
Get-Content -Raw reports/onda3-train-start-sensitivity/onda3_train_start_comparison_v1.csv
Get-Content -Raw reports/onda3-train-start-sensitivity/onda3_train_start_bracket_overall_v1.csv
```

Expected:

- both variants are present;
- every row has `production_status = EXPERIMENT_ONLY`;
- decision status is one of the three accepted statuses.

---

### Task 5: Documentation Update After Generation

**Files:**
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update roadmap generated-state subsection**

After real artifacts exist, update `ROADMAP.md` under Onda 3 with:

```text
Generated 2026-06-09 Onda 3E train-start sensitivity state:

- CLI: `uv run tmax onda3-train-start-sensitivity --test-years 2023,2024,2025`.
- Artifacts live under `reports/onda3-train-start-sensitivity/`.
- The experiment compares `legacy_2009_start` and `continuous_2012_start`.
- Open-Meteo/NWP is not integrated.
- Decision status is `<read from decision artifact>`.
- Production status remains `EXPERIMENT_ONLY`.
```

- [ ] **Step 2: Update changelog**

Add a short entry to `CHANGELOG.md`:

```text
- Added Onda 3E train-start sensitivity experiment artifacts comparing sparse 2009-start versus continuous 2012-start local-data training windows.
```

- [ ] **Step 3: Verify docs**

Run:

```powershell
rg -n "Onda 3E|train-start|2012-01-01|Open-Meteo|EXPERIMENT_ONLY" ROADMAP.md CHANGELOG.md reports/onda3-train-start-sensitivity
```

Expected: docs and report mention Onda 3E, the 2012 start, and no Open-Meteo integration.

---

### Task 6: Final Verification

- [ ] **Step 1: Run focused Onda 3E tests**

```powershell
uv run pytest tests/test_onda3_train_start_sensitivity.py tests/test_onda3_train_start_sensitivity_cli.py -q
```

- [ ] **Step 2: Run adjacent Onda 3 model tests**

```powershell
uv run pytest tests/test_onda3_interactions.py tests/test_onda3_interactions_cli.py tests/test_onda3_model_attempt_review.py -q
```

- [ ] **Step 3: Run Ruff on touched files**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_train_start_sensitivity.py tests/test_onda3_train_start_sensitivity_cli.py
```

- [ ] **Step 4: Verify no Open-Meteo or production promotion leak**

```powershell
rg -n "open-meteo|Open-Meteo|production ready|deployment unlocked|live trading|EV unlocked" reports/onda3-train-start-sensitivity ROADMAP.md CHANGELOG.md
```

Expected: Open-Meteo appears only as a negative scope statement; no production/market promotion language appears.

- [ ] **Step 5: Optional stable suite**

Run when time budget allows:

```powershell
uv run pytest -q -m "not network"
```

Expected: stable non-network suite passes.

---

## Self-Review

- Spec coverage: this plan implements only step 1 of the pre-Open-Meteo
  sequence: Onda 3E train-start sensitivity. Steps 2, 3, and 4 remain future
  specs/plans.
- Placeholder scan: no task contains TBD/TODO placeholders; all file paths,
  commands, and expected outputs are concrete.
- Type consistency: function names are consistent across tests, module exports,
  CLI, and writer:
  `build_onda3_train_start_sensitivity` and
  `write_onda3_train_start_sensitivity_artifacts`.
