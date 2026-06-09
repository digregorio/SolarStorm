# Regime Design Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline regime-design validation path that assigns candidate regime labels and tests whether the candidate removes the Onda 4 R2 dead-regime blocker.

**Architecture:** Add a focused `solarstorm.onda2e._regime_design_validation` module that reads Onda 2E candidate artifacts, assigns candidate labels to feature rows, writes audit artifacts, and runs existing R2 validation against an in-memory feature copy. Add a CLI command that writes reports without mutating `data/features.parquet`.

**Tech Stack:** Python, Polars, Typer, existing Onda2e/robustness validation helpers, pytest, ruff.

---

### Task 1: Candidate Ontology And Assignment

**Files:**
- Create: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing ontology and assignment tests**

Add tests that import `build_regime_candidate_artifacts`, build a tiny candidate table with month centroids, assign two feature rows, and assert:

```python
assert artifacts["regime_candidate_ontology"].height == 2
assert artifacts["regime_candidate_assignments"].height == features.height
assert set(artifacts["regime_candidate_assignments"]["production_status"]) == {"NOT_PRODUCTION"}
assert "candidate_regime_label" in artifacts["regime_candidate_assignments"].columns
```

- [ ] **Step 2: Run red test**

Run:

```bash
uv run pytest tests/test_regime_design_validation.py::test_candidate_assignment_uses_month_centroids -q
```

Expected: import or function-not-found failure.

- [ ] **Step 3: Implement assignment module**

Create:

```python
build_regime_candidate_artifacts(candidate: pl.DataFrame, features: pl.DataFrame) -> dict[str, pl.DataFrame]
```

It must emit `regime_candidate_assignments`, `regime_candidate_ontology`, and `regime_candidate_assignment_audit`.

- [ ] **Step 4: Run green test**

Run the same focused pytest command and confirm it passes.

### Task 2: R2 Candidate Validation

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing validation test**

Add a test for:

```python
validate_regime_candidate_r2(features, labels, assignments, hypotheses, cp_set=("20:00",), test_starts=[...])
```

Assert it returns `regime_candidate_r2_validation`, includes `dead_candidate_regimes`, and does not mutate original `features`.

- [ ] **Step 2: Run red test**

Run:

```bash
uv run pytest tests/test_regime_design_validation.py::test_candidate_r2_validation_uses_feature_copy -q
```

Expected: function-not-found failure.

- [ ] **Step 3: Implement validation adapter**

Join assignments into a feature copy, replace `regime_label` only in that copy, call `regime_sensitivity`, and call `detect_dead_regimes(..., regimes=<candidate family list>)`.

- [ ] **Step 4: Run green test**

Run the focused pytest command and confirm it passes.

### Task 3: Writers And CLI

**Files:**
- Modify: `solarstorm/onda2e/_regime_design_validation.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_design_validation.py`

- [ ] **Step 1: Write failing writer/CLI tests**

Add tests that call `write_regime_candidate_validation_artifacts(...)` and `runner.invoke(app, ["regime-design-validate", ...])`. Assert the six required files are written and `data/features.parquet` input remains unchanged.

- [ ] **Step 2: Run red tests**

Run:

```bash
uv run pytest tests/test_regime_design_validation.py::test_regime_design_validate_cli_writes_artifacts -q
```

Expected: CLI command missing.

- [ ] **Step 3: Implement writers and Typer command**

Add CLI command `regime-design-validate` with options for features, labels, candidate, queue, output dir, and optional test starts. Validate that queue contains `WCT-REGIME-016` as `PROMOTED_TO_REGIME_DESIGN`.

- [ ] **Step 4: Run green CLI test**

Run the focused CLI test and confirm it passes.

### Task 4: Reports, Docs, And Verification

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Generated: `reports/regime-design/*`

- [ ] **Step 1: Run command on real artifacts**

Run:

```bash
uv run python -m solarstorm regime-design-validate --features-path data/features.parquet --labels-path data/labels.parquet --candidate-path reports/onda2e/regime_design_candidate_v1.csv --queue-path reports/onda2e/regime_design_queue.csv --output-dir reports/regime-design
```

- [ ] **Step 2: Verify generated counts**

Use a short Polars audit to confirm assignments match feature row count, no null candidate labels exist, and validation/report files exist.

- [ ] **Step 3: Update docs**

Document that candidate validation is offline and not production promotion.

- [ ] **Step 4: Final verification**

Run:

```bash
uv run ruff check .
uv run pytest -q -m "not network"
```
