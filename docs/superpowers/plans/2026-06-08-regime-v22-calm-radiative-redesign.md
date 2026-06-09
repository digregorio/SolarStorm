# Regime v2.2 Calm/Radiative Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a non-production v2.2 regime candidate that restores calm/radiative as a protected macro and reruns physical Onda C against it.

**Architecture:** Add a focused v2.2 builder module that overlays a quantile-based physical calm/radiative rule on v2.1 assignments. Extend the existing validation and classifiability paths with candidate-under-review parameters so v2.1 remains backward compatible while v2.2 can be evaluated.

**Tech Stack:** Python, Polars, Typer CLI, pytest, Ruff, existing Onda 2E physical cluster matrix.

---

### Task 1: v2.2 Builder

**Files:**
- Create: `solarstorm/onda2e/_regime_v22_calm_radiative.py`
- Test: `tests/test_regime_v22_calm_radiative.py`

- [ ] Write failing tests for calm/radiative reassignment, ontology counts, audit rows, writer outputs, and v21-v22 comparison.
- [ ] Implement a quantile-threshold rule requiring low wind plus at least two supporting physical signals.
- [ ] Preserve original v2.1 labels in audit columns and keep all assignment rows `NOT_PRODUCTION`.
- [ ] Add a writer for v2.2 assignment, ontology, audit, comparison, and validation report artifacts.

### Task 2: CLI and Exports

**Files:**
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_v22_calm_radiative.py`

- [ ] Export the v2.2 builder, comparison, and writer functions.
- [ ] Add `regime-design-v22-validate`.
- [ ] The CLI must rebuild the physical matrix from features, labels, and obs; generate v2.2; run R2; compare v2.1-v2.2; and write artifacts.

### Task 3: Onda C Generalization

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] Write a failing test showing Onda C accepts `v2.2` with three protected macros.
- [ ] Parameterize candidate-under-review version, method name, protected macros, and comparison dead-count column.
- [ ] Preserve existing v2.1 behavior and current CLI flags.
- [ ] Add CLI options for v2.2 review paths without breaking v2.1 defaults.

### Task 4: Real Artifacts and Docs

**Files:**
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `ROADMAP.md`
- Modify: `docs/regime_model_card.md`
- Modify: `docs/onda4_robustness_plan.md`

- [ ] Run the v2.2 CLI on real project data.
- [ ] Run physical Onda C with v2.2 as candidate under review.
- [ ] Update docs with observed row counts, R2 outcome, Onda C verdict, and next allowed action.

### Task 5: Verification

**Commands:**
- `uv run pytest tests/test_regime_v22_calm_radiative.py tests/test_regime_classifiability.py tests/test_regime_design_validation.py -q`
- `uv run pytest -q -m "not network"`
- `uv run ruff check solarstorm/onda2e solarstorm/__main__.py tests/test_regime_v22_calm_radiative.py tests/test_regime_classifiability.py`

- [ ] Confirm all focused tests pass.
- [ ] Confirm the non-network suite passes.
- [ ] Confirm Ruff reports no issues.
- [ ] Confirm no production model artifacts were created.
