# Foundation Experiment Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a versioned Foundation Experiment Catalog that turns Onda 2E EDA evidence into auditable experiment candidates for baseline, regime, feature, threshold, and validation work.

**Architecture:** Add one focused Onda 2E module that loads existing CSV artifacts, builds a stable Polars catalog schema, writes CSV and markdown artifacts, and exposes a dedicated CLI command. The catalog is an experiment contract only: every row is `EXPERIMENT_ONLY`. Initial catalog v1 did not create a result file; the follow-on results runner now writes `foundation_experiment_results_v1.csv` and keeps every result `EXPERIMENT_ONLY`.

**Tech Stack:** Python, Polars, Typer, pytest, ruff.

---

### Task 1: Catalog Schema And Builder

**Files:**
- Create: `solarstorm/onda2e/_foundation_experiments.py`
- Test: `tests/test_foundation_experiments.py`

- [ ] **Step 1: Write failing unit tests**

Add tests that import `build_foundation_experiment_catalog` from `solarstorm.onda2e` and assert:
- quarantined baseline rules create baseline experiment rows;
- every `regime_design_queue.csv` item creates a regime experiment row;
- `candidate_maritime_cloudy` and `candidate_mixed_or_transition` create dead-regime repair rows when all R2 rows fail;
- rejected decision rows do not become experiments;
- every row has required comparator, metric, gates, source artifacts, and `EXPERIMENT_ONLY`.

- [ ] **Step 2: Verify red**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: import failure for the missing foundation experiment functions.

- [ ] **Step 3: Implement minimal builder**

Create `FOUNDATION_EXPERIMENT_SCHEMA`, `FOUNDATION_WARNING_SCHEMA`, `_empty_frame`, deterministic row helpers, and:

```python
def build_foundation_experiment_catalog(
    *,
    decision_register: pl.DataFrame,
    regime_design_queue: pl.DataFrame,
    quarantined_baselines: pl.DataFrame,
    rejection_register: pl.DataFrame | None = None,
    domain_eda_next_experiments: pl.DataFrame | None = None,
    foehn_repair_candidates: pl.DataFrame | None = None,
    wind_repair_candidates: pl.DataFrame | None = None,
    regime_candidate_r2_validation: pl.DataFrame | None = None,
    optional_artifact_warnings: pl.DataFrame | None = None,
) -> dict[str, pl.DataFrame]:
    ...
```

The returned dict must include `foundation_experiment_catalog` and `foundation_experiment_warnings`.

- [ ] **Step 4: Verify green**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: tests pass.

### Task 2: Artifact Loading And Markdown Writer

**Files:**
- Modify: `solarstorm/onda2e/_foundation_experiments.py`
- Test: `tests/test_foundation_experiments.py`

- [ ] **Step 1: Write failing writer tests**

Add tests for:
- `load_foundation_experiment_inputs(onda2e_dir=..., regime_design_dir=...)` requiring `evidence_decision_register.csv`, `regime_design_queue.csv`, and `quarantined_baseline_register.csv`;
- missing optional artifacts appearing in `foundation_experiment_warnings`;
- `write_foundation_experiment_catalog_artifacts(...)` writing only `foundation_experiment_catalog_v1.csv` and `foundation_experiment_catalog_v1.md`;
- markdown report containing counts by family, domain, weakness target, candidate surface, priority rows, and the not-production guard.

- [ ] **Step 2: Verify red**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: missing loader/writer failures.

- [ ] **Step 3: Implement loader and writer**

Use required artifact checks with clear `FileNotFoundError` messages, optional artifact warnings for absent optional CSV/MD files, Polars CSV writes, and UTF-8 markdown writes.

- [ ] **Step 4: Verify green**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: tests pass.

### Task 3: Public Exports And CLI

**Files:**
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_foundation_experiments.py`

- [ ] **Step 1: Write failing CLI test**

Use `CliRunner` and temp CSVs to invoke:

```bash
foundation-experiments --onda2e-dir <tmp>/onda2e --regime-design-dir <tmp>/regime-design --output-dir <tmp>/foundation-experiments
```

Assert exit code `0`, both artifacts exist, and no `foundation_experiment_results_v1.csv` exists.

- [ ] **Step 2: Verify red**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: CLI command missing.

- [ ] **Step 3: Wire exports and command**

Export `build_foundation_experiment_catalog`, `load_foundation_experiment_inputs`, and `write_foundation_experiment_catalog_artifacts`. Add `@app.command("foundation-experiments")` with `--onda2e-dir`, `--regime-design-dir`, and `--output-dir`; print count and artifact paths.

- [ ] **Step 4: Verify green**

Run: `uv run pytest tests/test_foundation_experiments.py -q`

Expected: tests pass.

### Task 4: Generate Real Artifacts And Verify

**Files:**
- Generate: `reports/foundation-experiments/foundation_experiment_catalog_v1.csv`
- Generate: `reports/foundation-experiments/foundation_experiment_catalog_v1.md`
- Optionally modify: `docs/decisions/012-evidence-to-decision-gate.md`

- [ ] **Step 1: Generate artifacts**

Run:

```bash
uv run python -m solarstorm foundation-experiments --onda2e-dir reports/onda2e --regime-design-dir reports/regime-design --output-dir reports/foundation-experiments
```

- [ ] **Step 2: Inspect real outputs**

Check that the CSV has at least one baseline experiment, one regime experiment, dead-family rows for `candidate_maritime_cloudy` and `candidate_mixed_or_transition`, and only `EXPERIMENT_ONLY` statuses.

- [ ] **Step 3: Update ADR-012 note if needed**

If ADR-012 does not mention the catalog, add a short implementation note that the Foundation Experiment Catalog is the non-production bridge from EDA decisions to future experiment execution.

- [ ] **Step 4: Run verification**

Run:

```bash
uv run pytest tests/test_foundation_experiments.py -q
uv run pytest -q -m "not network"
uv run ruff check .
```

Expected: all pass.
