# Onda 3G Audit Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Onda 3G, an experiment-only audit comparison of persisted Onda 3D, 3E, and 3F local-data model artifacts.

**Architecture:** Add `solarstorm.onda3._audit_comparison` to load and normalize predictions, recompute shared bracket/regime/feature-slice metrics, emit decision artifacts, and write CSV/Markdown reports. Wire it through `solarstorm.onda3.__init__` and a Typer CLI command `onda3-audit-comparison`.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, Ruff.

---

## File Structure

- Create `solarstorm/onda3/_audit_comparison.py`
  - Prediction loaders, common-schema normalization, metric builders, decision
    logic, report renderer, and artifact writer.
- Modify `solarstorm/onda3/__init__.py`
  - Export `build_onda3_audit_comparison` and
    `write_onda3_audit_comparison_artifacts`.
- Modify `solarstorm/__main__.py`
  - Add `onda3-audit-comparison` CLI.
- Create `tests/test_onda3_audit_comparison.py`
  - Unit tests for model summary, pairwise deltas, regime winners, feature
    slices, decision status, and `EXPERIMENT_ONLY`.
- Create `tests/test_onda3_audit_comparison_cli.py`
  - CLI smoke test verifying artifact files and negative Open-Meteo scope.
- Generate `reports/onda3-audit-comparison/`.
- Update `ROADMAP.md` and `CHANGELOG.md`.

---

### Task 1: Common Audit Builder

**Files:**
- Create: `tests/test_onda3_audit_comparison.py`
- Create: `solarstorm/onda3/_audit_comparison.py`

- [x] **Step 1: Write failing builder test**

Create a synthetic set of enriched predictions for Onda 3D, Onda 3E legacy,
Onda 3E continuous, and Onda 3F. Call `build_onda3_audit_comparison` and assert:

- `onda3_audit_model_summary_v1` contains all four canonical model IDs;
- `onda3_audit_pairwise_delta_v1` contains `onda3_f_minus_onda3_d`;
- `onda3_audit_regime_winner_v1` has one winner row per binary macro regime;
- `onda3_audit_feature_slice_v1` contains `top_quartile_foehn_score`;
- every non-empty artifact includes `production_status = EXPERIMENT_ONLY`;
- decision is one of the three approved Onda 3G statuses.

- [x] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_audit_comparison.py::test_build_onda3_audit_comparison_compares_model_surfaces -q
```

Expected: import failure because `_audit_comparison` does not exist.

- [x] **Step 3: Implement minimal builder**

Implement:

- `PRODUCTION_STATUS`
- `CANONICAL_MODEL_LABELS`
- `_ensure_date(frame)`
- `_canonicalize_prediction_frame(frame, iteration_id, iteration_label)`
- `_model_summary(predictions)`
- `_pairwise_delta(summary, reference_id, candidate_ids)`
- `_by_year(predictions)`
- `_by_month(predictions)`
- `_by_month_cp(predictions)`
- `_regime_performance(predictions)`
- `_regime_winner(regime)`
- `_feature_slice_summary(predictions, features)`
- `_decision(summary)`
- `build_onda3_audit_comparison(predictions, features)`

Always recompute half-up bracket columns from `actual` and `prediction` with
`floor(value + 0.5)`, even when upstream artifacts already include persisted
bracket columns. Do not train a model.

- [x] **Step 4: Verify builder**

Run:

```powershell
uv run pytest tests/test_onda3_audit_comparison.py -q
uv run ruff check solarstorm/onda3/_audit_comparison.py tests/test_onda3_audit_comparison.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Artifact Reader, Writer, and CLI

**Files:**
- Create: `tests/test_onda3_audit_comparison_cli.py`
- Modify: `solarstorm/onda3/_audit_comparison.py`
- Modify: `solarstorm/onda3/__init__.py`
- Modify: `solarstorm/__main__.py`

- [x] **Step 1: Write failing CLI test**

Create temporary Onda 3D, Onda 3E, Onda 3F, assignment, and feature artifacts.
Invoke:

```powershell
uv run tmax onda3-audit-comparison --reports-dir <tmp> --features-path <tmp/features.parquet> --output-dir <tmp/out>
```

Assert:

- exit code 0;
- every planned CSV and Markdown artifact exists;
- report and stdout state Open-Meteo is not integrated;
- summary includes all four canonical IDs;
- decision output remains `EXPERIMENT_ONLY`.

- [x] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_onda3_audit_comparison_cli.py -q
```

Expected: command missing or imports missing.

- [x] **Step 3: Implement artifact loader and writer**

Implement:

- `AUDIT_FILENAMES`
- `_read_csv(path)`
- `load_onda3_audit_prediction_inputs(reports_dir)`
- `_markdown_table(df, max_rows=30)`
- `render_onda3_audit_comparison_report(artifacts, today)`
- `write_onda3_audit_comparison_artifacts(artifacts, output_dir, today)`

The loader reads Onda 3D line predictions, binary macro assignments, Onda 3E
train-start predictions, and Onda 3F pooled predictions. Onda 3D predictions
must be enriched with the existing bracket helper before comparison.

- [x] **Step 4: Export functions**

Update `solarstorm/onda3/__init__.py` to export:

- `build_onda3_audit_comparison`
- `load_onda3_audit_prediction_inputs`
- `write_onda3_audit_comparison_artifacts`

- [x] **Step 5: Implement CLI**

Add `@app.command("onda3-audit-comparison")` in `solarstorm/__main__.py` with
options:

- `--reports-dir`, default `./reports`
- `--features-path`, default `./data/features.parquet`
- `--output-dir`, default `./reports/onda3-audit-comparison`

The command loads inputs, builds artifacts, writes them, prints decision and
report path, and prints that Open-Meteo is not integrated.

- [x] **Step 6: Verify CLI**

Run:

```powershell
uv run pytest tests/test_onda3_audit_comparison_cli.py -q
uv run ruff check solarstorm/onda3/_audit_comparison.py solarstorm/onda3/__init__.py solarstorm/__main__.py tests/test_onda3_audit_comparison_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Generate Real Artifacts and Document Result

**Files:**
- Create: `reports/onda3-audit-comparison/`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/plans/2026-06-09-onda3g-audit-comparison.md`

- [x] **Step 1: Run CLI on real local artifacts**

Run:

```powershell
uv run tmax onda3-audit-comparison --reports-dir ./reports --features-path ./data/features.parquet --output-dir ./reports/onda3-audit-comparison
```

Expected: command exits 0 and prints decision plus report path.

- [x] **Step 2: Inspect critical outputs**

Run:

```powershell
Get-Content -Raw reports/onda3-audit-comparison/onda3_audit_model_summary_v1.csv
Get-Content -Raw reports/onda3-audit-comparison/onda3_audit_pairwise_delta_v1.csv
Get-Content -Raw reports/onda3-audit-comparison/onda3_audit_decision_update_v1.csv
```

Expected: all four models appear, Onda 3F versus Onda 3D deltas appear, every
row is `EXPERIMENT_ONLY`, and the decision leads to nested validation rather
than production.

- [x] **Step 3: Update docs**

Record the Onda 3G artifact location, key deltas, decision status, and
`EXPERIMENT_ONLY` scope in `ROADMAP.md` and `CHANGELOG.md`.

---

### Task 4: Final Verification

**Files:**
- No new code files.

- [x] **Step 1: Run focused tests**

```powershell
uv run pytest tests/test_onda3_audit_comparison.py tests/test_onda3_audit_comparison_cli.py -q
```

- [x] **Step 2: Run adjacent Onda 3 tests**

```powershell
uv run pytest tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py tests/test_onda3_train_start_sensitivity.py tests/test_onda3_model_attempt_review.py -q
```

- [x] **Step 3: Run Ruff**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_audit_comparison.py tests/test_onda3_audit_comparison_cli.py
```

- [x] **Step 4: Verify scope language**

```powershell
rg -n "open-meteo|Open-Meteo|production ready|deployment unlocked|live trading|EV unlocked" reports/onda3-audit-comparison ROADMAP.md CHANGELOG.md
```

Expected: Open-Meteo appears only as future work or negative scope; no
production/market promotion language appears.

---

## Completion Evidence

Completed on 2026-06-09.

- Generated command:
  `uv run tmax onda3-audit-comparison --reports-dir ./reports --features-path ./data/features.parquet --output-dir ./reports/onda3-audit-comparison`
- Decision: `CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION`.
- Onda 3F minus Onda 3D MAE delta: `-0.11070566935900139`.
- Onda 3F minus Onda 3D daily any-CP exact delta:
  `-0.729927007299267` percentage points.
- Onda 3F minus Onda 3D final 23:00 exact delta:
  `1.5510948905109423` percentage points.
- Focused tests:
  `uv run pytest tests/test_onda3_audit_comparison.py tests/test_onda3_audit_comparison_cli.py -q`.
- Adjacent tests:
  `uv run pytest tests/test_onda3_pooled_iteration.py tests/test_onda3_pooled_cli.py tests/test_onda3_train_start_sensitivity.py tests/test_onda3_model_attempt_review.py -q`.
- Lint:
  `uv run ruff check solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_audit_comparison.py tests/test_onda3_audit_comparison_cli.py`.
- Scope audit: Open-Meteo appears only as explicit future/negative scope; no
  production-promotion language was found.
- Post-review regressions added and fixed:
  - Bracket columns are always recomputed from `actual` and `prediction`.
  - The CLI blocks if any of the four canonical audit models is missing.
  - Feature joins fail on duplicate `date_local, cp` feature keys.
  - Top-quartile feature slices use top-25% row cardinality in the audited
    prediction universe instead of `>= p75` value thresholds.

## Self-Review

- Spec coverage: every Onda 3G acceptance criterion maps to a task above.
- Placeholder scan: no task contains TBD/TODO placeholders.
- Type consistency: public function names are consistent across tests, exports,
  CLI, and writer.
