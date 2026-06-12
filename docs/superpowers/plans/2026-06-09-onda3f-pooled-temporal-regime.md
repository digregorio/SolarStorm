# Onda 3F Pooled Temporal/Regime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Onda 3F, an experiment-only pooled temporal/regime model that shares data across CP and season using cyclic features before any Open-Meteo integration.

**Architecture:** Add `solarstorm.onda3._pooled_iteration` for cyclic feature preparation, pooled annual ridge fitting, bracket/regime summaries, decision output, and report writing. Wire it through `solarstorm.onda3.__init__` and a Typer CLI command `onda3-pooled-model-iteration`, then generate artifacts under `reports/onda3-pooled/`.

**Tech Stack:** Python 3.12, Polars, NumPy ridge helpers from Onda 3, Typer, pytest, Ruff.

---

## File Structure

- Create `solarstorm/onda3/_pooled_iteration.py`
  - Temporal cyclic feature generation, pooled rolling model, artifact builder,
    CSV/Markdown writer, and report renderer.
- Modify `solarstorm/onda3/__init__.py`
  - Export `add_pooled_temporal_features`,
    `build_onda3_pooled_iteration`, and `write_onda3_pooled_artifacts`.
- Modify `solarstorm/__main__.py`
  - Add `onda3-pooled-model-iteration` CLI.
- Create `tests/test_onda3_pooled_iteration.py`
  - Unit tests for cyclic features, pooled results, bracket summaries, and
    `EXPERIMENT_ONLY`.
- Create `tests/test_onda3_pooled_cli.py`
  - CLI smoke test verifying all planned CSV/Markdown artifacts and negative
    Open-Meteo scope.
- Generate `reports/onda3-pooled/`.
- Update `ROADMAP.md` and `CHANGELOG.md`.

---

### Task 1: Cyclic Temporal Features

**Files:**
- Create: `tests/test_onda3_pooled_iteration.py`
- Create: `solarstorm/onda3/_pooled_iteration.py`

- [x] **Step 1: Write failing test for cyclic columns**

Create `tests/test_onda3_pooled_iteration.py` with a matrix helper and a test
that imports `add_pooled_temporal_features`, calls it, and asserts that
`cp_sin`, `cp_cos`, `month_sin`, `month_cos`, `doy_sin`, and `doy_cos` exist,
are numeric, and stay between -1 and 1.

- [x] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py::test_add_pooled_temporal_features_adds_cyclic_columns -q
```

Expected: import failure because `_pooled_iteration` does not exist.

- [x] **Step 3: Implement minimal cyclic feature helper**

Create `solarstorm/onda3/_pooled_iteration.py` with:

- `PRODUCTION_STATUS = "EXPERIMENT_ONLY"`
- `_ensure_date(frame)`
- `add_pooled_temporal_features(matrix)`

Use CP order `20:00,21:00,22:00,23:00`, month period 12, and day-of-year period
365.25.

- [x] **Step 4: Verify helper**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py::test_add_pooled_temporal_features_adds_cyclic_columns -q
uv run ruff check solarstorm/onda3/_pooled_iteration.py tests/test_onda3_pooled_iteration.py
```

Expected: test passes and Ruff reports `All checks passed!`.

---

### Task 2: Pooled Rolling Model Builder

**Files:**
- Modify: `tests/test_onda3_pooled_iteration.py`
- Modify: `solarstorm/onda3/_pooled_iteration.py`

- [x] **Step 1: Write failing pooled-builder test**

Add a test that imports `build_onda3_pooled_iteration`, runs it on synthetic
2022-2025 data for all four CPs, and asserts:

- model results contain `cp = ALL`;
- result rows include test years 2024 and 2025;
- predictions retain original CP values including `23:00`;
- bracket overall contains `cp_2300_exact_pct`;
- every non-empty artifact has `production_status = EXPERIMENT_ONLY`;
- decision is one of `READY_FOR_ONDA3_AUDIT_COMPARISON` or
  `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`.

- [x] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py::test_build_onda3_pooled_iteration_trains_one_model_per_year -q
```

Expected: import failure because `build_onda3_pooled_iteration` does not exist.

- [x] **Step 3: Implement pooled builder**

In `_pooled_iteration.py`, implement:

- `_encode_features(train, test, numeric_feature_columns, categorical_feature_columns)`
- `_prediction_rows(test, predictions, target_column)`
- `_slice_diagnostics(predictions, matrix)`
- `_run_pooled_fold(split, ...)`
- `build_onda3_pooled_iteration(matrix, test_years, numeric_feature_columns, categorical_feature_columns, target_column="tmax_int")`

Reuse:

- `solarstorm.onda3._baseline_model._mae`
- `solarstorm.onda3._baseline_model._ridge_predict`
- `solarstorm.onda3._interactions.add_binary_macro_interaction_features`
- bracket/regime helpers from `solarstorm.onda3._model_attempt_review`

The builder must add cyclic features, add binary-macro interactions, fit one
pooled model per test year, enrich predictions with half-up brackets, and emit
all Onda 3F artifact frames.

- [x] **Step 4: Verify builder**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py -q
uv run ruff check solarstorm/onda3/_pooled_iteration.py tests/test_onda3_pooled_iteration.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Writer and CLI

**Files:**
- Create: `tests/test_onda3_pooled_cli.py`
- Modify: `solarstorm/onda3/_pooled_iteration.py`
- Modify: `solarstorm/onda3/__init__.py`
- Modify: `solarstorm/__main__.py`

- [x] **Step 1: Write failing CLI test**

Create `tests/test_onda3_pooled_cli.py` that writes temporary feature, label,
and assignment artifacts, invokes `onda3-pooled-model-iteration`, and asserts:

- exit code 0;
- all planned CSV and Markdown artifacts exist;
- both report and stdout state Open-Meteo is not integrated;
- model results have `cp = ALL`;
- predictions retain `20:00,21:00,22:00,23:00`.

- [x] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_cli.py -q
```

Expected: command missing.

- [x] **Step 3: Implement writer**

Add `POOLED_FILENAMES`, `_markdown_table`,
`render_onda3_pooled_report`, and `write_onda3_pooled_artifacts`.

- [x] **Step 4: Export functions**

Update `solarstorm/onda3/__init__.py` to export:

- `add_pooled_temporal_features`
- `build_onda3_pooled_iteration`
- `write_onda3_pooled_artifacts`

- [x] **Step 5: Implement CLI**

Add `@app.command("onda3-pooled-model-iteration")` in `solarstorm/__main__.py`.
The command must load features/labels/assignments, join labels on
`date_local`, join assignments on `date_local, cp`, select numeric features
from the Onda 3 manifest, select categorical features from
`binary_macro_regime_label`, `regime_label`, `regime_score_argmax`, and
`day_sequence_pattern` when present, run the builder, write artifacts, and
print decision plus report path.

- [x] **Step 6: Verify CLI**

Run:

```powershell
uv run pytest tests/test_onda3_pooled_cli.py -q
uv run ruff check solarstorm/onda3/_pooled_iteration.py solarstorm/onda3/__init__.py solarstorm/__main__.py tests/test_onda3_pooled_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 4: Generate Real Onda 3F Artifacts

**Files:**
- Create: `reports/onda3-pooled/`

- [x] **Step 1: Run CLI on local artifacts**

Run:

```powershell
uv run tmax onda3-pooled-model-iteration --features-path ./data/features.parquet --labels-path ./data/labels.parquet --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir ./reports/onda3-pooled --test-years 2023,2024,2025
```

Expected: command exits 0 and prints the Onda 3F decision plus report path.

- [x] **Step 2: Inspect critical outputs**

Run:

```powershell
Get-Content -Raw reports/onda3-pooled/onda3_pooled_decision_update_v1.csv
Get-Content -Raw reports/onda3-pooled/onda3_pooled_model_results_v1.csv
Get-Content -Raw reports/onda3-pooled/onda3_pooled_bracket_overall_v1.csv
```

Expected: `cp = ALL` in model results, predictions retain CPs in bracket
summaries, every row is `EXPERIMENT_ONLY`, and Open-Meteo is not integrated.

---

### Task 5: Documentation and Final Verification

**Files:**
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Update docs with generated result**

Record Onda 3F artifact location, weighted MAE, exact-bracket rates, decision
status, and `EXPERIMENT_ONLY` scope in `ROADMAP.md` and `CHANGELOG.md`.

- [x] **Step 2: Run focused tests**

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py -q
```

- [x] **Step 3: Run adjacent Onda 3 tests**

```powershell
uv run pytest tests/test_onda3_interactions.py tests/test_onda3_train_start_sensitivity.py tests/test_onda3_model_attempt_review.py -q
```

- [x] **Step 4: Run Ruff**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py
```

- [x] **Step 5: Verify scope language**

```powershell
rg -n "open-meteo|Open-Meteo|production ready|deployment unlocked|live trading|EV unlocked" reports/onda3-pooled ROADMAP.md CHANGELOG.md
```

Expected: Open-Meteo appears only as future work or negative scope; no
production/market promotion language appears.

---

## Completion Evidence

Completed on 2026-06-09.

- Generated command:
  `uv run tmax onda3-pooled-model-iteration --features-path ./data/features.parquet --labels-path ./data/labels.parquet --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv --output-dir ./reports/onda3-pooled --test-years 2023,2024,2025`
- Decision: `READY_FOR_ONDA3_AUDIT_COMPARISON`.
- Overall MAE: `1.0619083280873316`.
- Daily any-CP exact bracket: `44.43430656934307%`.
- Final 23:00 exact bracket: `31.47810218978102%`.
- Focused tests: `uv run pytest tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py -q`.
- Adjacent tests: `uv run pytest tests/test_onda3_interactions.py tests/test_onda3_train_start_sensitivity.py tests/test_onda3_model_attempt_review.py -q`.
- Lint: `uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py`.
- Scope audit: Open-Meteo appears only as explicit future/negative scope; no
  production-promotion language was found.
- Post-review regressions added and fixed:
  - CP values typed as `Time`/`datetime.time` are normalized to canonical
    `HH:MM` before cyclic encoding and CLI assignment joins.
  - Requested test years with no valid pooled fold now return
    `KEEP_IN_ONDA3_EXPERIMENT_REVIEW` with a controlled rationale instead of a
    schema error.

## Self-Review

- Spec coverage: this plan implements only step 2 of the pre-Open-Meteo model
  sequence, Onda 3F pooled temporal/regime modeling.
- Placeholder scan: no task contains TBD/TODO placeholders.
- Type consistency: public function names are consistent across tests, exports,
  CLI, and writer.
