# Regime v2.3 Calm/Radiative Failure Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build experiment-only diagnostics explaining why v2.2 calm/radiative fails R2.

**Architecture:** Add one focused Onda 2E module for v2.3 diagnostics, export it through `solarstorm.onda2e`, and expose one CLI command that reads existing artifacts and writes CSV/Markdown outputs.

**Tech Stack:** Python, Polars, Typer, pytest, Ruff.

---

### Task 1: Test the Diagnostic Contract

**Files:**
- Create: `tests/test_regime_v23_calm_failure_diagnostics.py`

- [x] **Step 1: Write a failing test**

Test that sufficient calm/radiative support plus 0 R2 pass rows produces
`CALM_RADIATIVE_VALIDATION_TARGET_GAP`, writes CSV/Markdown artifacts, and
exposes a CLI command.

- [x] **Step 2: Run the focused test**

Run: `uv run pytest tests/test_regime_v23_calm_failure_diagnostics.py -q`

Expected before implementation: fails because
`solarstorm.onda2e._regime_v23_calm_failure_diagnostics` does not exist.

### Task 2: Implement v2.3 Diagnostics

**Files:**
- Create: `solarstorm/onda2e/_regime_v23_calm_failure_diagnostics.py`

- [x] **Step 1: Add schemas and validation**

Define diagnostic and next-experiment schemas. Reject assignment inputs whose
`production_status` is not `NOT_PRODUCTION`.

- [x] **Step 2: Add macro summaries**

Compute assignment rows, unique days, CP support, reassigned rows, R2 pass
rows, R2 median/min/max `n_days`, feature coverage, target medians, diagnosis,
and recommended next action.

- [x] **Step 3: Add artifact writer**

Write `regime_calm_radiative_failure_diagnostics_v1.csv`,
`regime_calm_radiative_failure_diagnostics_v1.md`, and
`regime_v23_next_experiments.csv`.

### Task 3: Wire Exports and CLI

**Files:**
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`

- [x] **Step 1: Export builder and writer**

Expose `build_regime_v23_calm_failure_diagnostics` and
`write_regime_v23_calm_failure_diagnostics_artifacts`.

- [x] **Step 2: Add CLI command**

Add `python -m solarstorm regime-design-v23-calm-diagnostics` with input paths
for v2.2 assignments, v2.2 R2 validation, features, labels, and output dir.

### Task 4: Generate Real Artifacts and Document Result

**Files:**
- Create/overwrite: `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.csv`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.md`
- Create/overwrite: `reports/regime-design/regime_v23_next_experiments.csv`
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/regime_model_card.md`
- Modify: `docs/onda4_robustness_plan.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Run the CLI**

Run: `uv run python -m solarstorm regime-design-v23-calm-diagnostics`

Expected: writes v2.3 diagnostics and reports
`CALM_RADIATIVE_VALIDATION_TARGET_GAP`.

- [x] **Step 2: Update docs**

Record that v2.3 explains the blocker but does not clear Onda C or Onda 3.

### Task 5: Verify

**Files:**
- No new files beyond implementation and docs.

- [x] **Step 1: Run focused tests**

Run: `uv run pytest tests/test_regime_v23_calm_failure_diagnostics.py -q`

- [x] **Step 2: Run relevant regime tests**

Run: `uv run pytest tests/test_regime_v23_calm_failure_diagnostics.py tests/test_regime_v22_calm_radiative.py tests/test_regime_classifiability.py tests/test_regime_design_validation.py -q`

- [x] **Step 3: Run non-network suite**

Run: `uv run pytest -q -m "not network"`

- [x] **Step 4: Run Ruff**

Run: `uv run ruff check .`

### Task 6: Execute CEXP-CALM-RADIATIVE-001 Target Diagnostics

**Files:**
- Create: `tests/test_regime_v23_calm_target_diagnostics.py`
- Create: `solarstorm/onda2e/_regime_v23_calm_target_diagnostics.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.md`

- [x] **Step 1: Write failing test**

Test that CEXP-001 computes train-window `remaining_warming = tmax_int -
k_cp__cp_XXXX` by `macro x month x CP`, writes CSV/Markdown, and exposes a CLI.

- [x] **Step 2: Run red test**

Run: `uv run pytest tests/test_regime_v23_calm_target_diagnostics.py -q`

Expected before implementation: fails because
`solarstorm.onda2e._regime_v23_calm_target_diagnostics` does not exist.

- [x] **Step 3: Implement target diagnostics**

Add target-only quantiles for remaining warming and Tmax hour, target bucket
shares, underpowered flags, and `production_status = EXPERIMENT_ONLY`.

- [x] **Step 4: Generate real artifact**

Run: `uv run python -m solarstorm regime-design-v23-calm-target-diagnostics --train-end 2025-12-31`

Expected: writes `regime_calm_radiative_target_diagnostics_v1.csv/.md` and
reports `CEXP-CALM-RADIATIVE-001`.

- [x] **Step 5: Verify CEXP-001**

Run focused tests, relevant regime tests, non-network tests, and Ruff before
closing this sprint.

### Task 7: Execute CEXP-CALM-RADIATIVE-002 Feature Hypotheses

**Files:**
- Create: `tests/test_regime_v23_calm_feature_hypotheses.py`
- Create: `solarstorm/onda2e/_regime_v23_calm_feature_hypotheses.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.csv`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.md`

- [x] **Step 1: Write failing test**

Test that CEXP-002 screens train-window `macro_calm_radiative` feature
hypotheses, excludes rows after `train_end`, blocks `remaining_warming` and
any `tmax_*` target proxy, writes CSV/Markdown, and exposes a CLI.

- [x] **Step 2: Run red tests**

Run: `uv run pytest tests/test_regime_v23_calm_feature_hypotheses.py -q`

Expected before implementation: fails because
`solarstorm.onda2e._regime_v23_calm_feature_hypotheses` does not exist; later
RED checks fail until `causal_role`, `tmax_*` blocking, and valid-row target
means are implemented.

- [x] **Step 3: Implement feature-hypothesis diagnostics**

Add an experiment-only builder and writer. The builder joins assignments,
features, and labels in the train window, computes `remaining_warming` only as
an audit target, records `causal_role`, and writes all rows with
`production_status = EXPERIMENT_ONLY`.

- [x] **Step 4: Generate real artifact**

Run: `uv run python -m solarstorm regime-design-v23-calm-feature-hypotheses --train-end 2025-12-31`

Observed: 8 features screened; 1 preliminary `CANDIDATE_SIGNAL`
(`cloud_cover_suppression`, Pearson corr -0.318, slope -2.89); 4
`WEAK_SIGNAL`; 2 `CONSTANT_FEATURE`; 1 `UNDERPOWERED_FEATURE`.

- [x] **Step 5: Record decision**

CEXP-002 remains `EXPERIMENT_ONLY`. It does not promote a feature, regime,
Onda C, or Onda 3. It hands `cloud_cover_suppression` to the CEXP-002B causal
robustness screen before any CEXP-003 demote/split decision.

### Task 8: Execute CEXP-CALM-RADIATIVE-002B Cloud Signal Validation

**Files:**
- Create: `tests/test_regime_v23_calm_cloud_signal_validation.py`
- Create: `solarstorm/onda2e/_regime_v23_calm_cloud_signal_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv`
- Create/overwrite: `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.md`
- Conditional: `reports/regime-design/regime_calm_radiative_demote_split_v1.csv`
  only if CEXP-002B fails.

- [x] **Step 1: Write failing tests**

Test that a stable negative cloud-cover signal survives the robustness screen,
and that a proxy-like or wrong-sign signal triggers the CEXP-003 demote/split
matrix.

- [x] **Step 2: Run red test**

Run: `uv run pytest tests/test_regime_v23_calm_cloud_signal_validation.py -q`

Expected before implementation: fails because
`solarstorm.onda2e._regime_v23_calm_cloud_signal_validation` does not exist.

- [x] **Step 3: Implement CEXP-002B**

Add a train-only validation builder/writer and CLI. The validation checks
pre-CP cloud lineage, expected negative slope, CP stability, month x CP
stability, controlled-slope retention after physical controls, and correlation
against known target/proxy columns.

- [x] **Step 4: Generate real artifact**

Run: `uv run python -m solarstorm regime-design-v23-calm-cloud-validation --train-end 2025-12-31`

Observed: `SURVIVES_CAUSAL_ROBUSTNESS_SCREEN` with 1,725 rows, overall slope
-2.89, controlled slope -1.75, controlled retention 0.605, 4/4 CP cells and
25/25 supported month x CP cells with negative slopes, and max proxy
correlation 0.340.

- [x] **Step 5: Conditional CEXP-003 decision**

CEXP-003 demote/split is not triggered in the real run because the signal
survives. The failure path is implemented and tested with a synthetic
proxy/artifact case, but no real CEXP-003 artifact is written unless CEXP-002B
fails.
