# Onda 2E Full EDA Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full Onda 2E EDA sprint artifacts, including an individual review of all 251 theses and deep physical-regime architecture EDA.

**Architecture:** Add a focused `solarstorm.onda2e._full_eda` module that consumes existing Onda 2E artifacts, current features, labels, and pre-CP observations. Keep production model/regime code untouched; write CSV and markdown artifacts under `reports/onda2e`.

**Tech Stack:** Python 3.12, Polars, NumPy, Typer, pytest, ruff.

---

### Task 1: Full EDA Artifact API

**Files:**
- Create: `solarstorm/onda2e/_full_eda.py`
- Modify: `solarstorm/onda2e/__init__.py`
- Test: `tests/test_onda2e_full_eda.py`

- [ ] Write failing tests for `build_full_eda_artifacts()` and `write_full_eda_artifacts()`.
- [ ] Implement schemas for thesis review, input manifest, k sweep, profiles, outcome audit, leakage audit.
- [ ] Verify the full thesis review emits one row per atlas thesis.
- [ ] Verify the input manifest marks clustering inputs as causal and excludes outcomes/current regime labels.

### Task 2: Regime Architecture K Selection

**Files:**
- Modify: `solarstorm/onda2e/_full_eda.py`
- Test: `tests/test_onda2e_full_eda.py`

- [ ] Build a pre-CP clustering matrix from obs slices with `valid < CP`.
- [ ] Implement deterministic NumPy k-means for `k=2..6`.
- [ ] Compute silhouette, AIC/BIC approximation, power flags, and external eta-squared after assignment.
- [ ] Emit month and season rows, with underpowered rows retained and flagged.

### Task 3: CLI Integration

**Files:**
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_onda2e.py`

- [ ] Import the full EDA helpers.
- [ ] Run the full EDA stage inside `python -m solarstorm onda2e`.
- [ ] Assert the CLI exports the new full-sprint artifacts.

### Task 4: Real Artifact Regeneration And Verification

**Files:**
- Output: `reports/onda2e/*`

- [ ] Run `uv run python -m solarstorm onda2e --atlas-path reports/onda2e/thesis_atlas_v1.md --features-path data/features.parquet --labels-path data/labels.parquet --obs-path data/obs.parquet --output-dir reports/onda2e`.
- [ ] Verify `full_thesis_review.csv` has 251 rows.
- [ ] Verify `regime_cluster_sweep_by_month_season.csv` contains monthly and seasonal `k=2..6` rows where powered.
- [ ] Run `uv run pytest -q tests/test_onda2e.py tests/test_onda2e_full_eda.py tests/test_onda2e_wind.py tests/test_onda2e_foehn.py tests/test_onda2e_performance.py`.
- [ ] Run `uv run ruff check solarstorm/onda2e solarstorm/__main__.py tests/test_onda2e.py tests/test_onda2e_full_eda.py tests/test_onda2e_wind.py tests/test_onda2e_foehn.py tests/test_onda2e_performance.py`.

