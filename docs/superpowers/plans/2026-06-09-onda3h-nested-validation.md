# Onda 3H Nested Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Onda 3H, an experiment-only nested walk-forward validation gate for Onda 3D versus Onda 3F before Open-Meteo integration.

**Architecture:** Add `solarstorm.onda3._nested_validation` to run validation/test folds, reuse existing Onda 3D and Onda 3F builders, recompute shared bracket metrics, select candidates by validation MAE, and write CSV/Markdown artifacts. Wire it through `solarstorm.onda3.__init__` and a Typer CLI command `onda3-nested-validation`.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, Ruff.

---

## File Structure

- Create `solarstorm/onda3/_nested_validation.py`
  - Fold construction, candidate runners, metric summaries, selection logic,
    report renderer, and artifact writer.
- Modify `solarstorm/onda3/__init__.py`
  - Export `build_onda3_nested_validation` and
    `write_onda3_nested_validation_artifacts`.
- Modify `solarstorm/__main__.py`
  - Add `onda3-nested-validation` CLI.
- Create `tests/test_onda3_nested_validation.py`
  - Unit tests for fold scope, validation selection, test refit scope, bracket
    recomputation, and `EXPERIMENT_ONLY`.
- Create `tests/test_onda3_nested_validation_cli.py`
  - CLI smoke test verifying artifact files and negative Open-Meteo scope.
- Generate `reports/onda3-nested-validation/`.
- Update `ROADMAP.md` and `CHANGELOG.md`.

---

### Task 1: Nested Builder Red-Green

**Files:**
- Create: `tests/test_onda3_nested_validation.py`
- Create: `solarstorm/onda3/_nested_validation.py`

- [x] **Step 1: Write the failing builder test**

Create a synthetic matrix with years `2020..2024`, four CPs, numeric features
`k_cp`, `foehn_score`, `cloud_cover_suppression`, categorical feature
`binary_macro_regime_label`, and target `tmax_int`.

Call:

```python
artifacts = build_onda3_nested_validation(
    _nested_matrix(),
    test_years=[2024],
    numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
    categorical_feature_columns=["binary_macro_regime_label"],
    train_start=dt.date(2020, 1, 1),
)
```

Assert:

- `onda3_nested_fold_scope_v1` contains validation train end `2022` and test
  train end `2023`;
- `onda3_nested_metric_summary_v1` includes both candidate IDs for stages
  `validation` and `test`;
- `onda3_nested_selection_v1` contains one selected candidate for outer test
  year `2024`;
- `onda3_nested_predictions_v1` contains recomputed `actual_bracket`,
  `pred_bracket`, and `exact_bracket`;
- every non-empty artifact has `production_status = EXPERIMENT_ONLY`.

- [x] **Step 2: Run red builder test**

Run:

```powershell
uv run pytest tests/test_onda3_nested_validation.py::test_build_onda3_nested_validation_selects_by_validation_and_refits_for_test -q
```

Expected: import failure because `_nested_validation` does not exist.

- [x] **Step 3: Implement minimal builder**

Implement in `solarstorm/onda3/_nested_validation.py`:

```python
PRODUCTION_STATUS = "EXPERIMENT_ONLY"
ONDA3D_ID = "onda3_d_binary_macro_interactions"
ONDA3F_ID = "onda3_f_pooled_temporal_regime"
NESTED_FILENAMES = {...}

def build_onda3_nested_validation(...): ...
```

The builder should:

- normalize `date_local`;
- run Onda 3D via `build_onda3_interaction_iteration`;
- run Onda 3F via `build_onda3_pooled_iteration`;
- use validation fits ending at `Y-2`;
- use test fits ending at `Y-1`;
- recompute bracket columns from `actual` and `prediction`;
- summarize MAE, daily `any_cp_exact_pct`, `cp23_exact_pct`, and CP-specific
  exact percentages;
- select fold winners by validation MAE, then `cp23_exact_pct`, then Onda 3D.

- [x] **Step 4: Verify builder**

Run:

```powershell
uv run pytest tests/test_onda3_nested_validation.py -q
uv run ruff check solarstorm/onda3/_nested_validation.py tests/test_onda3_nested_validation.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Artifact Writer and CLI

**Files:**
- Create: `tests/test_onda3_nested_validation_cli.py`
- Modify: `solarstorm/onda3/_nested_validation.py`
- Modify: `solarstorm/onda3/__init__.py`
- Modify: `solarstorm/__main__.py`

- [x] **Step 1: Write failing CLI test**

Create temporary `features.parquet`, `labels.parquet`, and
`assignments.csv`. Invoke:

```powershell
uv run tmax onda3-nested-validation --features-path <tmp/features.parquet> --labels-path <tmp/labels.parquet> --binary-assignments-path <tmp/assignments.csv> --output-dir <tmp/out> --test-years 2024
```

Assert:

- exit code 0;
- every planned CSV and Markdown artifact exists;
- report and stdout state Open-Meteo is not integrated;
- decision output remains `EXPERIMENT_ONLY`.

- [x] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_onda3_nested_validation_cli.py -q
```

Expected: command missing or imports missing.

- [x] **Step 3: Implement writer**

Add:

```python
def render_onda3_nested_validation_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str: ...

def write_onda3_nested_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]: ...
```

The report must include scope, decision, fold selection, validation/test metric
summary, regime diagnostics, and the sentence
`Open-Meteo forecast data is not integrated.`

- [x] **Step 4: Export functions**

Update `solarstorm/onda3/__init__.py` to export:

- `build_onda3_nested_validation`
- `write_onda3_nested_validation_artifacts`

- [x] **Step 5: Implement CLI**

Add `@app.command("onda3-nested-validation")` in `solarstorm/__main__.py` with
options:

- `--features-path`, default `./data/features.parquet`
- `--labels-path`, default `./data/labels.parquet`
- `--binary-assignments-path`, default
  `./reports/regime-design/regime_binary_macro_assignments_v1.csv`
- `--output-dir`, default `./reports/onda3-nested-validation`
- `--test-years`, default `2023,2024,2025`
- `--train-start`, default `2012-01-01`

The command loads local artifacts, validates and joins labels plus binary macro
assignments, derives numeric/categorical feature lists from the explicit Onda 3H
allowlist, builds artifacts, writes them, prints decision and report path, and
prints that Open-Meteo is not integrated.

- [x] **Step 6: Verify CLI**

Run:

```powershell
uv run pytest tests/test_onda3_nested_validation_cli.py -q
uv run ruff check solarstorm/onda3/_nested_validation.py solarstorm/onda3/__init__.py solarstorm/__main__.py tests/test_onda3_nested_validation_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Real Run and Documentation

**Files:**
- Create: `reports/onda3-nested-validation/`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/plans/2026-06-09-onda3h-nested-validation.md`

- [x] **Step 1: Run CLI on real local artifacts**

Run:

```powershell
uv run tmax onda3-nested-validation --features-path ./data/features.parquet --labels-path ./data/labels.parquet --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir ./reports/onda3-nested-validation --test-years 2023,2024,2025 --train-start 2012-01-01
```

Expected: command exits 0 and prints decision plus report path.

- [x] **Step 2: Inspect critical outputs**

Run:

```powershell
Get-Content -Raw reports/onda3-nested-validation/onda3_nested_selection_v1.csv
Get-Content -Raw reports/onda3-nested-validation/onda3_nested_test_selected_summary_v1.csv
Get-Content -Raw reports/onda3-nested-validation/onda3_nested_decision_update_v1.csv
```

Expected: every row is `EXPERIMENT_ONLY`, selections are by validation stage,
and the decision is a model-selection harness decision rather than production.

- [x] **Step 3: Update docs**

Record the Onda 3H artifact location, selected folds, test selected summary,
decision status, and `EXPERIMENT_ONLY` scope in `ROADMAP.md` and
`CHANGELOG.md`.

---

### Task 4: Final Verification

**Files:**
- No new code files.

- [x] **Step 1: Run focused tests**

```powershell
uv run pytest tests/test_onda3_nested_validation.py tests/test_onda3_nested_validation_cli.py -q
```

- [x] **Step 2: Run adjacent Onda 3 tests**

```powershell
uv run pytest tests/test_onda3_audit_comparison.py tests/test_onda3_audit_comparison_cli.py tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py tests/test_onda3_interactions.py -q
```

- [x] **Step 3: Run Ruff**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_nested_validation.py tests/test_onda3_nested_validation_cli.py
```

- [x] **Step 4: Verify scope language**

```powershell
rg -n "open-meteo|Open-Meteo|production ready|deployment unlocked|live trading|EV unlocked" reports/onda3-nested-validation ROADMAP.md CHANGELOG.md docs/superpowers/specs/2026-06-09-onda3h-nested-validation-design.md
```

Expected: Open-Meteo appears only as future work or negative scope; no
production/market promotion language appears.

---

## Self-Review

- Spec coverage: every Onda 3H acceptance criterion maps to a task above.
- Placeholder scan: no task contains TBD/TODO placeholders.
- Type consistency: public function names are consistent across tests, exports,
  CLI, and writer.

## Completion Evidence

Completed on 2026-06-09.

- Generated command:
  `uv run tmax onda3-nested-validation --features-path ./data/features.parquet --labels-path ./data/labels.parquet --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir ./reports/onda3-nested-validation --test-years 2023,2024,2025 --train-start 2012-01-01`.
- Decision: `PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS`.
- Validation selected Onda 3F in all outer folds: 2023, 2024, and 2025.
- Selected test MAE by year: 2023 `1.0399041923002685`, 2024
  `1.0703720071319096`, 2025 `1.0770312009470235`.
- Selected mean test MAE: `1.0624358001264005`; always-Onda-3D mean test MAE:
  `1.1704716626660236`.
- Post-review regressions added and fixed:
  - CLI exits cleanly when binary macro assignments are missing.
  - Onda 3H feature selection uses an explicit allowlist and excludes
    quarantined regime/timing columns.
  - `cp23` summaries expose `n_days_with_cp23` and `cp23_exact_days`, and
    missing `cp23_exact_pct` sorts behind available `23:00` metrics in
    tie-breaks.
