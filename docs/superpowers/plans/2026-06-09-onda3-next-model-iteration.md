# Onda 3B Next Model Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Onda 3B, a CP-specific next model iteration with train-only categorical encoding, richer prediction/slice diagnostics, and experiment-only artifacts under `reports/onda3-next/`.

**Architecture:** Reuse the existing Onda 3 feature manifest and design matrix, then add `solarstorm.onda3._next_iteration` for CP-specific ridge evaluation and `solarstorm.onda3._next_artifacts` for CSV/MD reports. Add a Typer command `onda3-next-model-iteration` that orchestrates loading inputs, running the model, writing artifacts, and printing the decision.

**Tech Stack:** Python 3.12, NumPy, Polars, Typer, pytest, Ruff.

---

## File Structure

- Create `solarstorm/onda3/_next_iteration.py`
  - CP-specific train-mean null, categorical encoder, ridge challenger,
    predictions, slice diagnostics, uncertainty, and decision builder.
- Create `solarstorm/onda3/_next_artifacts.py`
  - Writer for `reports/onda3-next/` CSV/MD artifacts.
- Modify `solarstorm/onda3/__init__.py`
  - Export Onda 3B builder and writer.
- Modify `solarstorm/__main__.py`
  - Add `onda3-next-model-iteration` CLI.
- Create `tests/test_onda3_next_iteration.py`
- Create `tests/test_onda3_next_cli.py`
- Update docs after reports are generated:
  - `ROADMAP.md`
  - `docs/decisions/012-evidence-to-decision-gate.md`
  - `docs/regime_model_card.md`
  - `CHANGELOG.md`

---

### Task 1: CP-Specific Next Iteration Runner

**Files:**
- Create: `tests/test_onda3_next_iteration.py`
- Create: `solarstorm/onda3/_next_iteration.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing tests**

Add tests that build a small matrix with two CPs and a categorical
`binary_macro_regime_label`. Verify:

- results include `train_mean_null` and `ridge_challenger` for each CP;
- predictions are emitted for challenger test rows;
- slice diagnostics include CP and binary macro MAE rows;
- uncertainty rows are finite and experiment-only;
- decision is `READY_FOR_ONDA4_MODEL_RERUN` when every challenger beats its CP
  null.

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_next_iteration.py -q
```

Expected: fail because `solarstorm.onda3._next_iteration` does not exist.

- [ ] **Step 3: Implement minimal runner**

Create:

```python
build_onda3_next_iteration(
    matrix: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]
```

The function must:

- loop by `cp`;
- fit train-mean null per CP;
- one-hot encode categorical columns using train categories only;
- fit ridge using NumPy;
- emit model results, challenger predictions, slice diagnostics,
  uncertainty/abstention, and decision update.

- [ ] **Step 4: Export and verify**

Run:

```powershell
uv run pytest tests/test_onda3_next_iteration.py -q
uv run ruff check solarstorm/onda3/_next_iteration.py tests/test_onda3_next_iteration.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Artifact Writer and CLI

**Files:**
- Create: `tests/test_onda3_next_cli.py`
- Create: `solarstorm/onda3/_next_artifacts.py`
- Modify: `solarstorm/__main__.py`
- Modify: `solarstorm/onda3/__init__.py`

- [ ] **Step 1: Write failing writer/CLI tests**

Add tests that:

- write temporary feature, label, and binary assignment artifacts;
- invoke `onda3-next-model-iteration`;
- assert `onda3_next_model_report_v1.md` exists;
- assert stdout contains the decision.

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_onda3_next_cli.py -q
```

Expected: fail because writer/CLI do not exist.

- [ ] **Step 3: Implement writer and CLI**

Writer outputs:

- `onda3_next_feature_manifest_v1.csv/.md`
- `onda3_next_model_results_v1.csv/.md`
- `onda3_next_predictions_v1.csv/.md`
- `onda3_next_slice_diagnostics_v1.csv/.md`
- `onda3_next_uncertainty_abstention_v1.csv/.md`
- `onda3_next_decision_update_v1.csv/.md`
- `onda3_next_model_report_v1.md`

CLI defaults:

```powershell
python -m solarstorm onda3-next-model-iteration `
  --features-path ./data/features.parquet `
  --labels-path ./data/labels.parquet `
  --binary-assignments-path ./reports/regime-design/regime_binary_macro_assignments_v1.csv `
  --output-dir ./reports/onda3-next `
  --train-end 2024-12-31 `
  --test-start 2025-01-01
```

- [ ] **Step 4: Verify writer/CLI**

Run:

```powershell
uv run pytest tests/test_onda3_next_cli.py -q
uv run ruff check solarstorm/onda3/_next_artifacts.py tests/test_onda3_next_cli.py solarstorm/__main__.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Generate Real Onda 3B Artifacts

**Files:**
- Create: `reports/onda3-next/`

- [ ] **Step 1: Run CLI on real local artifacts**

Run:

```powershell
uv run python -m solarstorm onda3-next-model-iteration
```

Expected: command exits 0 and writes `reports/onda3-next/`.

- [ ] **Step 2: Inspect outputs**

Run:

```powershell
Get-Content -Raw reports/onda3-next/onda3_next_decision_update_v1.csv
Get-Content -Raw reports/onda3-next/onda3_next_model_results_v1.csv
```

Expected: all rows are `EXPERIMENT_ONLY`; decision is either
`READY_FOR_ONDA4_MODEL_RERUN` or `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`.

---

### Task 4: Documentation Updates

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/regime_model_card.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update docs after artifacts exist**

Document:

```text
Onda 3B is the next experimental model iteration after Onda 4M.
It writes reports/onda3-next.
It evaluates by CP and uses train-only categorical encoding for experiment-only binary macro context.
All outputs remain EXPERIMENT_ONLY.
The next action depends on onda3_next_decision_update_v1.csv.
```

- [ ] **Step 2: Verify docs**

Run:

```powershell
rg -n "Onda 3B|onda3-next|READY_FOR_ONDA4_MODEL_RERUN|EXPERIMENT_ONLY" ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/regime_model_card.md CHANGELOG.md
```

Expected: docs reflect Onda 3B and do not claim production promotion.

---

### Task 5: Final Verification and Clean Milestone

- [ ] **Step 1: Run focused tests**

```powershell
uv run pytest tests/test_onda3_next_iteration.py tests/test_onda3_next_cli.py -q
```

- [ ] **Step 2: Run adjacent Onda 3/Onda 4M tests**

```powershell
uv run pytest tests/test_onda3_feature_manifest.py tests/test_onda3_design_matrix.py tests/test_onda3_baseline_model.py tests/test_onda3_cli.py tests/test_onda4_model_review.py tests/test_onda4_model_review_cli.py -q
```

- [ ] **Step 3: Run Ruff**

```powershell
uv run ruff check solarstorm/onda3 solarstorm/robustness/_model_review.py tests/test_onda3_next_iteration.py tests/test_onda3_next_cli.py
```

- [ ] **Step 4: Run stable suite**

```powershell
uv run pytest -q -m "not network"
```

- [ ] **Step 5: Verify no production claims**

```powershell
rg -n "production[ -]ready|deployment\s+unlocked|financial\s+execution\s+unlocked|live\s+trading\s+unlocked" reports/onda3-next docs ROADMAP.md
```

- [ ] **Step 6: Commit and confirm clean tree**

```powershell
git add solarstorm/onda3 solarstorm/__main__.py tests/test_onda3_next_iteration.py tests/test_onda3_next_cli.py reports/onda3-next docs/superpowers/specs/2026-06-09-onda3-next-model-iteration-design.md docs/superpowers/plans/2026-06-09-onda3-next-model-iteration.md ROADMAP.md docs/decisions/012-evidence-to-decision-gate.md docs/regime_model_card.md CHANGELOG.md
git commit -m "milestone: complete onda3 next model iteration"
git status --short --branch
```
