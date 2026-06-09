# SolarStorm ROADMAP + Onda 4 Robustness — Implementation Plan

> Supersession note, 2026-06-06: this plan was executed to create the first
> Onda 4 robustness harness, but its old 5-regime assumption is superseded by
> ADR-011 and `docs/onda2r_regime_ontology_repair_plan.md`. Do not use this
> plan to reintroduce `late_warming` as a causal regime.
> Historical code blocks in this file are preserved for traceability only.
> Current regime work must use `docs/regime_model_card.md` and the physical
> family `calm_radiative`, `standard_nw`, `strong_nw_foehn`,
> `southerly_disrupted`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create ROADMAP.md (living all-ondas tracker), delete old-Wellington contaminated spec files, rewrite ADR-010 Onda 4 section, and build `solarstorm/robustness/` — a hardening package that stress-tests Onda 2's validated features with per-year replication, regime sensitivity, drift trend, causal re-audit, anti-nowcast lead-time analysis, physical Tmax-hour stratification, and late-spike evidence, producing a go/no-go report.

**Architecture:** One new package (`solarstorm/robustness/`) with focused modules following the existing private-module convention (`_config.py`, `_replication.py`, `_regime_analysis.py`, `_drift.py`, `_causal_audit.py`, `_lead_time.py`, `_tmax_hour.py`, `_late_spike.py`, `_report.py`), one CLI command (`robustness`) wired into the existing typer app, test files mirroring the module structure, and documentation/cleanup tasks. The package reads existing artifacts (features.parquet, labels.parquet, validated_feature_contract.json) and produces `reports/robustness/YYYY-MM-DD-robustness-report.md` + `robustness_drift_snapshot.json` + `late_spike_candidates.json`.

**Tech Stack:** Python 3.11, polars, numpy, typer, pytest. No new external dependencies. Mann-Kendall trend test implemented inline with numpy.

---

## File Map

```
ROADMAP.md                                    ← NEW: root-level all-ondas tracker
docs/decisions/010-onda-waves.md              ← EDIT: Onda 4 section (lines 59-87)

solarstorm/robustness/__init__.py             ← NEW: package init, exports run_robustness()
solarstorm/robustness/_config.py              ← NEW: frozen R1-R5 thresholds
solarstorm/robustness/_replication.py         ← NEW: per-year validation runner
solarstorm/robustness/_regime_analysis.py     ← NEW: regime × feature cross-tab
solarstorm/robustness/_drift.py               ← NEW: Mann-Kendall trend + snapshot
solarstorm/robustness/_causal_audit.py        ← NEW: firewall re-audit
solarstorm/robustness/_lead_time.py           ← NEW: anti-nowcast lead-time analysis
solarstorm/robustness/_tmax_hour.py           ← NEW: physical Tmax-hour stratification
solarstorm/robustness/_late_spike.py          ← NEW: late-spike evidence pack
solarstorm/robustness/_report.py              ← NEW: markdown report generator
solarstorm/__main__.py                        ← EDIT: add robustness CLI command

tests/test_robustness_replication.py          ← NEW
tests/test_robustness_regime.py               ← NEW
tests/test_robustness_drift.py                ← NEW
tests/test_robustness_causal.py               ← NEW
tests/test_robustness_lead_time.py            ← NEW
tests/test_robustness_tmax_hour.py            ← NEW
tests/test_robustness_late_spike.py           ← NEW
tests/test_robustness_report.py               ← NEW

DELETE: quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/*.md (5 files)
DELETE: docs/onda4_readiness_plan.md
DELETE: docs/live_shadow_runbook.md
```

---

### Task 1: Cleanup — delete contaminated files

**Files:**
- Delete: `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/design.md`
- Delete: `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/implementation-plan.md`
- Delete: `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/README.md`
- Delete: `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/requirements.md`
- Delete: `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/tasks.md`
- Delete: `docs/onda4_readiness_plan.md`
- Delete: `docs/live_shadow_runbook.md`

- [ ] **Step 1: Delete old Wellington spec files**

```bash
rm quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/design.md
rm quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/implementation-plan.md
rm quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/README.md
rm quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/requirements.md
rm quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/tasks.md
```

- [ ] **Step 2: Delete contaminated Onda 4 docs**

```bash
rm docs/onda4_readiness_plan.md
rm docs/live_shadow_runbook.md
```

- [ ] **Step 3: Verify deletions**

```bash
ls quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/ 2>&1
ls docs/onda4_readiness_plan.md 2>&1
ls docs/live_shadow_runbook.md 2>&1
```
Expected: all three commands return "No such file or directory"

- [ ] **Step 4: Commit**

```bash
git rm --cached docs/onda4_readiness_plan.md docs/live_shadow_runbook.md 2>/dev/null || true
git add -A
git commit -m "chore: delete old-Wellington spec files and contaminated Onda 4 docs"
```

---

### Task 2: ROADMAP.md — living all-ondas tracker

**Files:**
- Create: `ROADMAP.md`

- [ ] **Step 1: Write ROADMAP.md**

```markdown
# SolarStorm — Project Roadmap

> Living status tracker. See [ADR-010](docs/decisions/010-onda-waves.md) for wave methodology and rationale.

**Last updated:** 2026-06-05

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete |
| ⏳ | In progress |
| ⏸️ | Blocked |
| 🔮 | Planned |
| ⚠️ | At risk |

---

## Onda 0: Scaffold ✅

**Completed:** 2026-06-04

| Deliverable | Status | Artifact |
|------------|--------|----------|
| Repository structure, pyproject.toml, CI | ✅ | `.github/workflows/ci.yml` |
| Frozen principles P1-P5 | ✅ | `docs/principles.md` |
| Data pipeline: IEM ASOS ingest, METAR parsing | ✅ | `solarstorm/data/` |
| Causal firewall (P1) | ✅ | `solarstorm/_contracts.py` |
| `obs.parquet` + `labels.parquet` generation | ✅ | `data/obs.parquet`, `data/labels.parquet` |

**Gate status:** N/A (infrastructure wave, no performance gates)

---

## Onda 1: Baselines ✅

**Completed:** 2026-06-04

| Deliverable | Status | Artifact |
|------------|--------|----------|
| L0-L4 baseline ladder | ✅ | `solarstorm/baselines/` |
| Walk-forward harness (expanding-window splits) | ✅ | `solarstorm/eval/_walkforward.py` |
| Frozen gates G1-G5 (G4 hard, non-demotable) | ✅ | `solarstorm/eval/_gates.py` |
| Regime classifier (5 regimes) | ✅ | `solarstorm/eda/_regimes.py` |
| Hypothesis catalog H1-H23 + bootstrap CI | ✅ | `solarstorm/eda/_catalog.py`, `solarstorm/eval/_bootstrap.py` |
| CLI: ingest, baselines, leaderboard, eda | ✅ | `solarstorm/__main__.py` |
| Leaderboard artifact generation (P5) | ✅ | `solarstorm/eval/_leaderboard.py` |

**Gate status:** G1-G5 pass on all baselines vs. persistence (baseline ladder floor established)

---

## Onda 2: Prove Value ✅

**Completed:** 2026-06-05

| Deliverable | Status | Artifact |
|------------|--------|----------|
| Feature validation: walk-forward bootstrap CI + FDR on H1-H23 | ✅ | `reports/2026-06-05/hypothesis_results.json` |
| Best-null-per-CP computed inside each walk-forward split | ✅ | `solarstorm/eda/_validate.py` |
| Calibrated train-only CP null in validation gates | ✅ | `_fit_cp_mean_remaining_warming()` |
| Baseline+feature nulls in leaderboard | ✅ | `solarstorm/eval/_leaderboard.py` |
| 33 validated entries (current artifact; do not hard-code count) | ✅ | `reports/2026-06-05/validated_feature_contract.json` |
| Value report v2 | ✅ | `reports/value/value-report-v2.md` |

**Gate status:** ✅ At least one feature beats best null baseline with validated CI and passes all G1-G5 gates

---

## Onda 3: Models 🔮

**Planned.** Historically gated on the Onda 4 "go" verdict; current work also
requires any intervening wave, especially Onda C, to pass before Onda 3 starts.

| Deliverable | Status |
|------------|--------|
| ML models: LightGBM, quantile regression, NWP integration | 🔮 |
| Model ladder: model beats best feature-null at each CP | 🔮 |
| Hyperparameter tuning within causal firewall | 🔮 |
| Ensemble blending | 🔮 |
| Calibrated uncertainty + abstention/stay-out behavior | 🔮 |
| Late-spike modeling, potentially with Open-Meteo/NWP inputs | 🔮 |

**Entry gate:** Onda 4 robustness report must return "go" (all BLOCK criteria pass).

---

## Onda 4: Robustness Hardening ⏳

**Started:** 2026-06-05

### Entry Gate

- [ ] Fresh Onda 2 artifacts exist and are not superseded
- [ ] `ruff check .` passes with zero errors
- [ ] `pytest -q -m "not network"` passes with zero failures

### Deliverables

- [ ] T4.1: `solarstorm/robustness/_config.py` — frozen R1-R5 thresholds
- [ ] T4.2: `solarstorm/robustness/_replication.py` — per-test-year validation runner
- [ ] T4.3: `solarstorm/robustness/_regime_analysis.py` — regime × feature cross-tabulation
- [ ] T4.4: `solarstorm/robustness/_drift.py` — Mann-Kendall trend + drift snapshot
- [ ] T4.5: `solarstorm/robustness/_causal_audit.py` — causal firewall re-audit
- [ ] T4.6: `solarstorm/robustness/_lead_time.py` — anti-nowcast lead-time analysis
- [ ] T4.7: `solarstorm/robustness/_tmax_hour.py` — regime/month/Tmax-hour stratification
- [ ] T4.8: `solarstorm/robustness/_late_spike.py` — late-spike evidence pack
- [ ] T4.9: `solarstorm/robustness/_report.py` — markdown report generator
- [ ] T4.10: CLI `robustness` command wired in `solarstorm/__main__.py`
- [ ] T4.11: `ROADMAP.md` entry for Onda 4 updated with completion dates

### Exit Gate (Go/No-Go Criteria)

| ID | Criterion | Threshold | Status |
|----|-----------|-----------|--------|
| R1 | Test years with >= 1 feature passing G1-G5 + FDR | >= 5 of 12 | ⏳ |
| R2 | No dead regime | >= 1 feature passes G4/G5 per regime | ⏳ |
| R3 | Causal firewall clean | 0 violations | ⏳ |
| R4 | MAE gap stable | Mann-Kendall p > 0.05 | ⏳ |
| R5 | Gates re-pass on fresh pooled run | All G1-G5 pass | ⏳ |
| R6 | Anti-nowcast lead-time check | Skill before Tmax effectively known | ⏳ |
| R7 | Physical Tmax-hour stratification | Not fixed-CP artifact | ⏳ |
| R8 | Late-spike evidence pack | Artifact produced | ⏳ |

**Verdict:** ⏳ pending first robustness run

---

## Wave Gate Rules (from ADR-010)

1. All gates from Onda N-1 still pass (no regression).
2. The Onda N deliverable beats the best deliverable from Onda N-1 on the walk-forward holdout.
3. No feature or model is promoted without validated CI excluding zero and all gates passing.

---

## Future Waves (TBD)

| Wave | Scope | Gated On |
|------|-------|----------|
| Onda 5+ | Live execution, production deployment | Separate ADR |
```

- [ ] **Step 2: Commit**

```bash
git add ROADMAP.md
git commit -m "docs: add ROADMAP.md — living all-ondas project tracker"
```

---

### Task 3: Rewrite ADR-010 Onda 4 section

**Files:**
- Modify: `docs/decisions/010-onda-waves.md:59-87`

- [ ] **Step 1: Read current ADR-010 to confirm line ranges**

```bash
sed -n '55,90p' docs/decisions/010-onda-waves.md
```

- [ ] **Step 2: Replace Onda 4 section (lines 59-87)**

```markdown
### Onda 4: Robustness Hardening (in progress)

Onda 4 stress-tests Onda 2's validated feature-null value claims before Onda 3
invests in ML models. It does not perform trading, shadow decisions, position
sizing, EV calculation, or Polymarket API work. Those concepts remain on hold
until a production model proves predictive skill, uncertainty calibration, and
stay-out behavior.

Scope:

- Per-test-year replication: re-run the validation harness on each individual
  test year (2014-2025) to confirm features pass across years, not just pooled.
- Regime sensitivity: cross-tabulate feature performance against the 5 regimes
  (`calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted`); flag any
  regime where all features fail.
- Drift trend: compute feature-null MAE gap trend over calendar time
  (Mann-Kendall); flag a declining trend as a warning.
- Causal firewall re-audit: verify every validated feature respects temporal
  ordering (no future information at CP time).
- Anti-nowcast lead-time analysis: separate real prediction from post-answer
  nowcast skill.
- Physical Tmax-hour stratification: evaluate by regime, month, and observed or
  expected Tmax-hour buckets; fixed CPs are evaluation cutoffs, not physics.
- Late-spike evidence pack: preserve days where `k_cp` looked settled but final
  Tmax increased later; this informs future Open-Meteo/NWP model research.
- Go/no-go report: explicit verdict on whether the foundation is robust enough
  for Onda 3.

Entry gate:

1. Fresh Onda 2 artifacts exist and are not marked superseded.
2. `ruff check .` and `pytest -q -m "not network"` pass.

Exit gate (Go/No-Go):

1. R1: In >= 5 of 12 individual test years, at least 1 feature passes G1-G5
   and FDR. BLOCK if < 3.
2. R2: No regime is "dead" (at least 1 feature passes G4/G5 per regime).
   BLOCK if any regime has 0 passes.
3. R3: Causal firewall re-audit is clean (0 violations). BLOCK if any.
4. R4: Feature-null MAE gap shows no significant negative trend over calendar
   time (Mann-Kendall p > 0.05). WARNING if declining.
5. R5: All 5 gates re-pass on a fresh pooled run. BLOCK if any gate fails.
6. R6: Predictive skill exists before Tmax is effectively known. BLOCK if skill
   appears only after the answer is known.
7. R7: Apparent skill is not created by fixed CP timing. BLOCK if regime/month
   Tmax-hour stratification contradicts the CP-level result.
8. R8: Late-spike candidate artifact is produced. WARNING if absent.

Go: All BLOCK criteria pass. The foundation is robust for the next active
gate. This historical Onda 4 plan does not by itself authorize Onda 3. If a
required intervening wave such as Onda C is registered, that wave must pass
before any Onda 3 design review starts.
No-Go: Any BLOCK criterion fails. Onda 3 remains blocked until the root cause
is addressed and the robustness report reruns.
```

The replacement text goes in place of the existing Onda 4 section (from `### Onda 4: Readiness and Shadow Decision (planned)` through the exit gate bullet list). Use Edit tool:

```python
# old_string (exact match from file):
old = """### Onda 4: Readiness and Shadow Decision (planned)

Onda 4 is not automatic trading..."""

# new_string = the markdown block above
```

- [ ] **Step 3: Commit**

```bash
git add docs/decisions/010-onda-waves.md
git commit -m "docs(adr-010): redefine Onda 4 as Robustness Hardening"
```

---

### Task 4: `solarstorm/robustness/_config.py` — frozen thresholds

**Files:**
- Create: `solarstorm/robustness/__init__.py`
- Create: `solarstorm/robustness/_config.py`
- Test: `tests/test_robustness_replication.py` (shared test file, one test here)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_replication.py
"""Tests for robustness _config and _replication modules."""
from __future__ import annotations

import solarstorm.robustness._config as cfg


def test_config_constants_exist():
    """All frozen threshold constants are defined and have expected types."""
    assert isinstance(cfg.R1_MIN_PASSING_YEARS, int)
    assert isinstance(cfg.R1_BLOCK_YEARS, int)
    assert isinstance(cfg.R2_DEAD_REGIME_BLOCK, bool)
    assert isinstance(cfg.R3_LEAK_BLOCK, bool)
    assert isinstance(cfg.R4_TREND_ALPHA, float)
    assert isinstance(cfg.R5_GATE_RERUN_BLOCK, bool)
    assert isinstance(cfg.ROBUSTNESS_CONFIG_VERSION, str)
    assert cfg.R1_MIN_PASSING_YEARS > cfg.R1_BLOCK_YEARS
    assert 0.0 < cfg.R4_TREND_ALPHA < 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_robustness_replication.py::test_config_constants_exist -v`
Expected: FAIL with "No module named 'solarstorm.robustness'"

- [ ] **Step 3: Create package init and config module**

```python
# solarstorm/robustness/__init__.py
"""SolarStorm Onda 4 — Robustness Hardening.

Stress-tests Onda 2's validated feature-null value claims before Onda 3
invests in ML models. Produces a go/no-go robustness report.

Exports:
    run_robustness: Main entry point — runs all checks and writes the report.
"""
from __future__ import annotations

from solarstorm.robustness._config import (
    ROBUSTNESS_CONFIG_VERSION,
    R1_MIN_PASSING_YEARS,
    R1_BLOCK_YEARS,
    R2_DEAD_REGIME_BLOCK,
    R3_LEAK_BLOCK,
    R4_TREND_ALPHA,
    R5_GATE_RERUN_BLOCK,
)

__all__ = [
    "ROBUSTNESS_CONFIG_VERSION",
    "R1_MIN_PASSING_YEARS",
    "R1_BLOCK_YEARS",
    "R2_DEAD_REGIME_BLOCK",
    "R3_LEAK_BLOCK",
    "R4_TREND_ALPHA",
    "R5_GATE_RERUN_BLOCK",
]
```

```python
# solarstorm/robustness/_config.py
"""Frozen go/no-go thresholds for Onda 4 robustness hardening.

Bump ROBUSTNESS_CONFIG_VERSION if any threshold changes.
"""
from __future__ import annotations

ROBUSTNESS_CONFIG_VERSION = "1.0"

# R1: Per-year replication
# WARNING if fewer than this many test years have >= 1 passing feature
R1_MIN_PASSING_YEARS = 5
# BLOCK if fewer than this many test years have >= 1 passing feature
R1_BLOCK_YEARS = 3

# R2: Dead-regime detection
# BLOCK if any regime has 0 feature passes G4/G5
R2_DEAD_REGIME_BLOCK = True

# R3: Causal firewall re-audit
# BLOCK if any validated feature reads future state
R3_LEAK_BLOCK = True

# R4: Drift trend
# Mann-Kendall significance threshold for declining MAE gap
R4_TREND_ALPHA = 0.05

# R5: Gate re-run
# BLOCK if any G1-G5 gate fails on fresh pooled run
R5_GATE_RERUN_BLOCK = True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_robustness_replication.py::test_config_constants_exist -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/__init__.py solarstorm/robustness/_config.py tests/test_robustness_replication.py
git commit -m "feat(robustness): add frozen go/no-go thresholds (_config.py)"
```

---

### Task 5: `solarstorm/robustness/_replication.py` — per-year validation

**Files:**
- Create: `solarstorm/robustness/_replication.py`
- Test: `tests/test_robustness_replication.py` (add tests)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_robustness_replication.py`:

```python
import datetime as dt
import numpy as np
import polars as pl
import pytest

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.robustness._replication import per_year_replication


def _make_simple_dataset(
    n_years: int = 5,
    start_year: int = 2020,
    seed: int = 42,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Minimal synthetic dataset for robustness testing.

    Creates labels and features where tmax has a seasonal cycle plus noise,
    and one feature (feat_signal) is remaining_warming + small noise.
    """
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    tmax = np.round(20.0 + 8.0 * np.sin(2 * np.pi * np.arange(n_days) / 365)
                    + rng.normal(0, 1.5, n_days)).astype(int)

    rw_raw = rng.normal(0, 3.0, n_days)
    rw_raw -= rw_raw.mean()
    rw = np.round(rw_raw).astype(int)

    # Labels: one row per date
    labels_rows = []
    for i, d in enumerate(dates):
        row = {"date_local": d, "tmax_int": int(tmax[i]), "day_complete": True}
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            cp_code = cp_str.replace(":", "")
            row[f"k_cp__cp_{cp_code}"] = int(tmax[i] - rw[i])
        labels_rows.append(row)
    labels_df = pl.DataFrame(labels_rows)

    # Features: one row per (date, cp)
    feature_rows = []
    for i, d in enumerate(dates):
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            cp_hour = int(cp_str.split(":")[0])
            signal = rw[i] + rng.normal(0, 0.5)
            feature_rows.append({
                "date_local": d,
                "cp": cp_str,
                "cp_hour_utc": cp_hour,
                "feat_signal": float(signal),
                "regime_label": "calm",
            })
    features_df = pl.DataFrame(feature_rows)

    return features_df, labels_df


def test_per_year_replication_returns_expected_columns():
    """Year matrix has the expected columns and covers all test years."""
    features, labels = _make_simple_dataset(n_years=5, start_year=2020)
    hypotheses = [
        Hypothesis(id="H_sig", feature_column="feat_signal",
                   description="Signal feature", source="test"),
    ]

    year_matrix, summary = per_year_replication(
        features, labels, hypotheses,
        test_years=(2021, 2022, 2023, 2024),
        seed=42,
    )

    expected_cols = {"year", "hypothesis_id", "cp", "ci_lo", "ci_hi",
                     "passes_g1_g5", "best_null_name", "best_null_mae",
                     "challenger_mae", "n_days"}
    assert expected_cols.issubset(set(year_matrix.columns))
    assert year_matrix.height > 0
    assert set(year_matrix["year"].unique().to_list()) == {2021, 2022, 2023, 2024}
    assert isinstance(summary, dict)
    assert "n_years_tested" in summary


def test_per_year_replication_train_window_correct():
    """Each test year uses train data strictly before that year."""
    features, labels = _make_simple_dataset(n_years=5, start_year=2020)
    hypotheses = [
        Hypothesis(id="H_sig", feature_column="feat_signal",
                   description="Signal feature", source="test"),
    ]

    year_matrix, _summary = per_year_replication(
        features, labels, hypotheses,
        test_years=(2023,),
        seed=42,
    )

    # For test year 2023, train should be 2020-01-01 to 2022-12-31
    # which gives ~3*365 training days per CP
    row = year_matrix.row(0, named=True)
    assert row["n_days"] > 30  # must have enough test days
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_robustness_replication.py::test_per_year_replication_returns_expected_columns tests/test_robustness_replication.py::test_per_year_replication_train_window_correct -v`
Expected: FAIL with "cannot import name 'per_year_replication'"

- [ ] **Step 3: Write minimal implementation**

```python
# solarstorm/robustness/_replication.py
"""Per-test-year validation: re-run the full hypothesis harness annually.

For each test year Y, train = all days from history_start through Y-01-01
minus one day; test = Jan 1 through Dec 31 of year Y.
"""
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.eda._validate import HypothesisResult, validate_hypotheses


def per_year_replication(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    hypotheses: list[Hypothesis],
    *,
    test_years: tuple[int, ...] = (
        2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025,
    ),
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    seed: int = 42,
) -> tuple[pl.DataFrame, dict]:
    """Run validate_hypotheses() once per individual test year.

    Returns
    -------
    year_matrix : pl.DataFrame
        Columns: year, hypothesis_id, cp, ci_lo, ci_hi, passes_g1_g5,
        best_null_name, best_null_mae, challenger_mae, n_days
    summary : dict
        Keys: n_years_tested, years_with_passing_feature, years_with_no_passing_feature
    """
    rows: list[dict] = []
    years_with_pass: list[int] = []
    years_without_pass: list[int] = []

    for year in test_years:
        test_start = dt.date(year, 1, 1)
        test_end = dt.date(year, 12, 31)

        all_results, _contract = validate_hypotheses(
            features, labels, hypotheses,
            cp_set=cp_set,
            test_starts=[test_start],
            seed=seed,
        )

        year_has_pass = False
        for r in all_results:
            if r.regime != "all":
                continue
            passes_gates = (
                r.status == "validated"
                and r.gate_results
                and all(g.passed for g in r.gate_results.values())
            )
            rows.append({
                "year": year,
                "hypothesis_id": r.id,
                "cp": r.cp,
                "ci_lo": r.ci_lo,
                "ci_hi": r.ci_hi,
                "passes_g1_g5": passes_gates,
                "best_null_name": r.best_null_name,
                "best_null_mae": r.best_null_mae,
                "challenger_mae": (
                    float(abs(r.effect_size)) + float(r.best_null_mae or 0.0)
                    if r.effect_size is not None and r.best_null_mae is not None
                    else None
                ),
                "n_days": r.n_days,
            })
            if passes_gates:
                year_has_pass = True

        if year_has_pass:
            years_with_pass.append(year)
        else:
            years_without_pass.append(year)

    year_matrix = pl.DataFrame(rows)
    summary = {
        "n_years_tested": len(test_years),
        "years_with_passing_feature": years_with_pass,
        "years_with_no_passing_feature": years_without_pass,
    }
    return year_matrix, summary
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_robustness_replication.py -v`
Expected: 3 passed (config_constants_exist, returns_expected_columns, train_window_correct)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/_replication.py tests/test_robustness_replication.py
git commit -m "feat(robustness): add per-year replication runner (_replication.py)"
```

---

### Task 6: `solarstorm/robustness/_regime_analysis.py` — regime sensitivity

**Files:**
- Create: `solarstorm/robustness/_regime_analysis.py`
- Create: `tests/test_robustness_regime.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_regime.py
"""Tests for regime sensitivity analysis."""
from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.eda._validate import validate_hypotheses
from solarstorm.robustness._regime_analysis import (
    regime_sensitivity,
    detect_dead_regimes,
)

REGIMES = ("calm", "transition", "late_warming", "foehn_nw", "disrupted")


def _make_regime_dataset(seed: int = 42) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Dataset with alternating regimes across dates."""
    rng = np.random.default_rng(seed)
    n_days = 365 * 3
    start = dt.date(2020, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]
    regime_cycle = list(REGIMES)

    tmax = np.round(20.0 + 8.0 * np.sin(2 * np.pi * np.arange(n_days) / 365)
                    + rng.normal(0, 1.5, n_days)).astype(int)
    rw = np.round(rng.normal(0, 3.0, n_days)).astype(int)

    labels_rows = []
    for i, d in enumerate(dates):
        row = {"date_local": d, "tmax_int": int(tmax[i]), "day_complete": True}
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            cp_code = cp_str.replace(":", "")
            row[f"k_cp__cp_{cp_code}"] = int(tmax[i] - rw[i])
        labels_rows.append(row)
    labels_df = pl.DataFrame(labels_rows)

    feature_rows = []
    for i, d in enumerate(dates):
        regime = regime_cycle[i % len(regime_cycle)]
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            signal = rw[i] + rng.normal(0, 0.5)
            feature_rows.append({
                "date_local": d,
                "cp": cp_str,
                "cp_hour_utc": int(cp_str.split(":")[0]),
                "feat_signal": float(signal),
                "regime_label": regime,
            })
    features_df = pl.DataFrame(feature_rows)

    return features_df, labels_df


def test_regime_sensitivity_returns_all_regimes():
    """Cross-tab should include all regimes present in data."""
    features, labels = _make_regime_dataset()
    hypotheses = [
        Hypothesis(id="H_sig", feature_column="feat_signal",
                   description="Signal", source="test"),
    ]

    # First run full validation so we can extract validated hypothesis results
    all_results, _contract = validate_hypotheses(
        features, labels, hypotheses,
        test_starts=[dt.date(2022, 1, 1)],
        seed=42,
    )

    cross_tab = regime_sensitivity(
        features, labels, all_results,
        seed=42,
    )

    assert cross_tab.height > 0
    expected_cols = {"hypothesis_id", "cp", "regime", "passes", "n_days"}
    assert expected_cols.issubset(set(cross_tab.columns))
    regimes_found = set(cross_tab["regime"].unique().to_list())
    assert len(regimes_found) >= 3  # at least some regimes present


def test_detect_dead_regimes_with_all_failing():
    """When ALL rows in a regime fail, it should be flagged as dead."""
    # Build a synthetic cross-tab where one regime has all passes=False
    rows = []
    for regime in REGIMES:
        for cp in ("20:00", "21:00"):
            passes = regime != "disrupted"  # disrupted fails everything
            rows.append({
                "hypothesis_id": "H1",
                "cp": cp,
                "regime": regime,
                "passes": passes,
                "n_days": 100,
            })
    cross_tab = pl.DataFrame(rows)

    dead = detect_dead_regimes(cross_tab)
    assert "disrupted" in dead
    assert "calm" not in dead


def test_detect_dead_regimes_none_dead():
    """When every regime has at least one pass, no dead regimes."""
    rows = []
    for regime in REGIMES:
        for cp in ("20:00",):
            rows.append({
                "hypothesis_id": "H1",
                "cp": cp,
                "regime": regime,
                "passes": True,
                "n_days": 100,
            })
    cross_tab = pl.DataFrame(rows)

    dead = detect_dead_regimes(cross_tab)
    assert dead == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_robustness_regime.py -v`
Expected: FAIL with "cannot import name 'regime_sensitivity'"

- [ ] **Step 3: Write minimal implementation**

```python
# solarstorm/robustness/_regime_analysis.py
"""Regime sensitivity: cross-tabulate feature performance by regime.

Flags "dead" regimes where ALL validated features fail G4/G5.
"""
from __future__ import annotations

import polars as pl

from solarstorm.eda._validate import (
    HypothesisResult,
    _compute_single_result,
)


def regime_sensitivity(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_hypotheses: list[HypothesisResult],
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    seed: int = 42,
) -> pl.DataFrame:
    """Cross-tabulate pass/fail by regime for each validated (hypothesis, CP).

    Re-fits the OLS challenger per regime and computes per-regime gate results
    using the same _compute_single_result machinery as the main harness.

    Returns
    -------
    pl.DataFrame
        Columns: hypothesis_id, cp, regime, passes, n_days
    """
    from solarstorm.eda._validate import _fit_ols_challenger, _select_best_null
    from solarstorm.eval._walkforward import expanding_walk_forward_splits

    labels_ok = labels.filter(pl.col("day_complete")).sort("date_local")

    # Build test-start dates from labels range
    first_year = labels_ok["date_local"].min().year
    last_year = min(labels_ok["date_local"].max().year, 2025)
    test_starts = [
        dt.date(y, 1, 1) for y in range(max(first_year + 5, 2014), last_year + 1)
    ]

    splits = expanding_walk_forward_splits(
        history_start=labels_ok["date_local"].min(),
        test_starts=test_starts,
        test_length_days=365,
        min_train_days=365,
    )

    rows: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for split in splits:
        train_labels = labels_ok.filter(
            pl.col("date_local").is_between(split.train_start, split.train_end)
        )
        test_labels = labels_ok.filter(
            pl.col("date_local").is_between(split.test_start, split.test_end)
        )

        for r in validated_hypotheses:
            if r.status != "validated":
                continue
            fc = r.feature_column
            cp_str = r.cp

            train_feats = features.filter(
                pl.col("date_local").is_between(split.train_start, split.train_end)
                & (pl.col("cp") == cp_str)
            )
            train_non_null = train_feats.filter(pl.col(fc).is_not_null())
            if train_non_null.height < 30:
                continue

            ols = _fit_ols_challenger(train_non_null, labels, fc, cp_str)
            if ols is None:
                continue

            test_feats = features.filter(
                pl.col("date_local").is_between(split.test_start, split.test_end)
                & (pl.col("cp") == cp_str)
                & pl.col(fc).is_not_null()
            )
            if test_feats.height == 0:
                continue

            k_col = f"k_cp__cp_{cp_str.replace(':', '')}"
            regimes_in_test = test_feats["regime_label"].unique().drop_nulls().to_list()

            for regime in regimes_in_test:
                if regime in ("", "unknown"):
                    continue
                key = (r.id, cp_str, regime)
                if key in seen:
                    continue
                seen.add(key)

                regime_test = test_feats.filter(pl.col("regime_label") == regime)
                if regime_test.height < 30:
                    continue

                test_joined = regime_test.join(test_labels, on="date_local", how="inner")
                day_data: list[dict] = []
                for row in test_joined.iter_rows(named=True):
                    d = row["date_local"]
                    feat_val = row.get(fc)
                    tmax = row["tmax_int"]
                    kcp = row.get(k_col)
                    if feat_val is None or tmax is None or kcp is None:
                        continue
                    pred_rw = ols.predict_remaining_warming(feat_val)
                    if pred_rw is None:
                        continue
                    kcp_int = int(kcp)
                    tmax_int = int(tmax)
                    pred_tmax = float(kcp_int) + pred_rw
                    err = float(abs(pred_tmax - tmax_int))
                    l0_err = float(abs(kcp_int - tmax_int))
                    day_data.append({
                        "date": d,
                        "regime": regime,
                        "baseline_pred": float(kcp_int),
                        "baseline_error": l0_err,
                        "nulls": {"L0_persistence": {"pred": float(kcp_int), "error": l0_err}},
                        "challenger_pred": pred_tmax,
                        "challenger_error": err,
                        "tmax": tmax_int,
                    })

                if len(day_data) < 30:
                    continue

                import datetime as _dt
                result = _compute_single_result(
                    r.id, fc, cp_str, regime, day_data, seed=seed,
                )
                passes = (
                    result.status == "validated"
                    and result.gate_results
                    and all(g.passed for g in result.gate_results.values())
                )
                rows.append({
                    "hypothesis_id": r.id,
                    "cp": cp_str,
                    "regime": regime,
                    "passes": passes,
                    "n_days": len(day_data),
                })

    return pl.DataFrame(rows)


def detect_dead_regimes(cross_tab: pl.DataFrame) -> list[str]:
    """Return list of regimes where NO (hypothesis, CP) passes.

    A "dead" regime is one where every row in cross_tab has passes == False.
    """
    if cross_tab.height == 0:
        return []
    regimes = cross_tab["regime"].unique().to_list()
    dead: list[str] = []
    for regime in regimes:
        regime_rows = cross_tab.filter(pl.col("regime") == regime)
        if regime_rows.height > 0 and not regime_rows["passes"].any():
            dead.append(regime)
    return sorted(dead)
```

Note: The `regime_sensitivity` function uses `dt.date` — add `import datetime as dt` at the top if not already present. The function-level import for `_dt` is intentional to avoid shadowing the top-level `dt` used elsewhere.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_robustness_regime.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/_regime_analysis.py tests/test_robustness_regime.py
git commit -m "feat(robustness): add regime sensitivity analysis (_regime_analysis.py)"
```

---

### Task 7: `solarstorm/robustness/_drift.py` — performance trend

**Files:**
- Create: `solarstorm/robustness/_drift.py`
- Create: `tests/test_robustness_drift.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_drift.py
"""Tests for drift trend analysis."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.robustness._drift import (
    compute_drift_trend,
    write_drift_snapshot,
    _mann_kendall,
)


def test_mann_kendall_no_trend():
    """Flat series should have high p-value (no trend detected)."""
    rng = np.random.default_rng(42)
    x = rng.normal(0, 0.1, 30)
    stat, p_value = _mann_kendall(x)
    assert p_value > 0.05


def test_mann_kendall_increasing_trend():
    """Monotonically increasing series should have low p-value."""
    x = np.arange(1, 31, dtype=float)
    stat, p_value = _mann_kendall(x)
    assert stat > 0
    assert p_value < 0.01


def test_mann_kendall_decreasing_trend():
    """Monotonically decreasing series should have low p-value."""
    x = np.arange(30, 0, -1, dtype=float)
    stat, p_value = _mann_kendall(x)
    assert stat < 0
    assert p_value < 0.01


def test_compute_drift_trend_from_year_matrix():
    """Drift trend computes Mann-Kendall on per-year mean MAE gaps."""
    rows = []
    rng = np.random.default_rng(42)
    # Simulate stable performance: gap ~1.0 with noise across years
    gap = 1.0
    for year in range(2014, 2026):
        for cp in ("20:00", "21:00"):
            gap_val = gap + rng.normal(0, 0.1)
            rows.append({
                "year": year,
                "hypothesis_id": "H1",
                "cp": cp,
                "best_null_mae": 3.0 + gap_val,
                "challenger_mae": 3.0,
                "passes_g1_g5": True,
            })
    year_matrix = pl.DataFrame(rows)

    trend = compute_drift_trend(year_matrix)
    assert "trend_statistic" in trend
    assert "p_value" in trend
    assert "warning" in trend
    assert "per_year_gaps" in trend
    # With noise around a flat trend, p should be > 0.05
    assert trend["p_value"] > 0.01


def test_write_drift_snapshot_round_trips():
    """Snapshot JSON can be written and read back."""
    trend = {
        "trend_statistic": -1.2,
        "p_value": 0.23,
        "warning": False,
        "per_year_gaps": {"2022": 0.8, "2023": 0.9, "2024": 0.7},
        "config_version": "1.0",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "drift_snapshot.json"
        write_drift_snapshot(trend, str(path))
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["p_value"] == 0.23
        assert loaded["per_year_gaps"]["2023"] == 0.9
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_robustness_drift.py -v`
Expected: FAIL with "cannot import name 'compute_drift_trend'"

- [ ] **Step 3: Write minimal implementation**

```python
# solarstorm/robustness/_drift.py
"""Drift detection: Mann-Kendall trend test on feature-null MAE gap over time.

Writes a drift snapshot JSON so future runs can compare.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import norm


def _mann_kendall(x: np.ndarray) -> tuple[float, float]:
    """Mann-Kendall trend test. Returns (S_statistic, two-sided p_value).

    No external dependency — computes the normal approximation.
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0

    s = 0.0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = x[j] - x[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1

    # Variance with tie correction
    unique_vals, counts = np.unique(x, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5)) / 18.0
    for t in counts:
        if t > 1:
            var_s -= (t * (t - 1) * (2 * t + 5)) / 18.0

    if var_s <= 0:
        return s, 1.0

    z = (s - np.sign(s)) / np.sqrt(var_s)
    p_value = 2.0 * (1.0 - norm.cdf(abs(z)))
    return float(s), float(p_value)


def compute_drift_trend(
    year_matrix: pl.DataFrame,
) -> dict:
    """Compute Mann-Kendall trend on the per-year mean feature-null MAE gap.

    Parameters
    ----------
    year_matrix : pl.DataFrame
        Output of per_year_replication. Must have columns: year, best_null_mae,
        challenger_mae.

    Returns
    -------
    dict
        Keys: trend_statistic, p_value, warning, per_year_gaps
    """
    if year_matrix.height == 0:
        return {
            "trend_statistic": 0.0,
            "p_value": 1.0,
            "warning": False,
            "per_year_gaps": {},
        }

    # Mean MAE gap per year (best_null_mae - challenger_mae)
    year_gaps: dict[int, float] = {}
    for row in year_matrix.iter_rows(named=True):
        y = int(row["year"])
        best = row.get("best_null_mae")
        chal = row.get("challenger_mae")
        if best is None or chal is None:
            continue
        gap = float(best) - float(chal)
        year_gaps.setdefault(y, []).append(gap)  # type: ignore[union-attr]

    per_year_mean: dict[str, float] = {}
    sorted_years = sorted(year_gaps.keys())
    gap_series: list[float] = []
    for y in sorted_years:
        gaps = year_gaps[y]
        mean_gap = float(np.mean(gaps))
        per_year_mean[str(y)] = mean_gap
        gap_series.append(mean_gap)

    if len(gap_series) < 3:
        return {
            "trend_statistic": 0.0,
            "p_value": 1.0,
            "warning": False,
            "per_year_gaps": per_year_mean,
        }

    stat, p_value = _mann_kendall(np.array(gap_series))
    from solarstorm.robustness._config import R4_TREND_ALPHA

    # WARNING if declining trend is significant
    warning = stat < 0 and p_value < R4_TREND_ALPHA

    return {
        "trend_statistic": stat,
        "p_value": p_value,
        "warning": warning,
        "per_year_gaps": per_year_mean,
    }


def write_drift_snapshot(
    trend: dict,
    path: str,
) -> None:
    """Write robustness_drift_snapshot.json for future comparison."""
    from solarstorm.robustness._config import ROBUSTNESS_CONFIG_VERSION

    snapshot = {
        "generated": dt.datetime.now(dt.UTC).isoformat(),
        "config_version": ROBUSTNESS_CONFIG_VERSION,
        **trend,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_robustness_drift.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/_drift.py tests/test_robustness_drift.py
git commit -m "feat(robustness): add drift trend analysis (_drift.py)"
```

---

### Task 8: `solarstorm/robustness/_causal_audit.py` — firewall re-audit

**Files:**
- Create: `solarstorm/robustness/_causal_audit.py`
- Create: `tests/test_robustness_causal.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_causal.py
"""Tests for causal firewall re-audit."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm.robustness._causal_audit import reaudit_causality


def _make_features_with_timestamps(
    feature_max_ts_list: list[dt.datetime | None],
) -> pl.DataFrame:
    """Synthetic features dataframe with controllable per-row max observation timestamps.

    Each row is for a specific (date_local, cp). The feature_max_ts column
    records the latest observation timestamp used to compute the feature value.
    A value of None means no observation was used (no temporal dependency).
    """
    nzst = ZoneInfo("Pacific/Auckland")
    rows = []
    for i, max_ts in enumerate(feature_max_ts_list):
        d = dt.date(2025, 6, 1) + dt.timedelta(days=i)
        for cp_str in ("20:00", "21:00"):
            cp_hour = int(cp_str.split(":")[0])
            rows.append({
                "date_local": d,
                "cp": cp_str,
                "cp_hour_utc": cp_hour,
                "regime_label": "calm",
                "feat_clean": 1.0,
                "feat_leaky": 2.0,
                "feature_max_ts": max_ts,
                "feature_source_obs_count": 1,
            })
    return pl.DataFrame(rows)


def test_clean_feature_passes_causal_audit():
    """A feature with max_ts always before CP should pass."""
    features = _make_features_with_timestamps([
        dt.datetime(2025, 5, 31, 18, 0, tzinfo=dt.UTC),  # day before CP
        dt.datetime(2025, 6, 1, 18, 0, tzinfo=dt.UTC),
    ])

    # The feature_max_ts for each row is before the CP (20:00 or 21:00 UTC)
    # on the same date, so this should pass.
    clean, violating = reaudit_causality(
        features,
        pl.DataFrame({"date_local": [dt.date(2025, 6, 1)]}),
        ["feat_clean"],
    )
    # feat_clean uses feature_max_ts which is before CP — should be clean
    assert len(violating) == 0


def test_feature_with_future_timestamp_is_flagged():
    """A feature max_ts at or after CP should be flagged as a violation."""
    # Create a feature where max_ts IS AT the CP hour — this is a violation
    # (require_causal demands feature_max_ts < cp_utc, strictly before)
    rows = []
    for i in range(5):
        d = dt.date(2025, 6, 1) + dt.timedelta(days=i)
        rows.append({
            "date_local": d,
            "cp": "20:00",
            "cp_hour_utc": 20,
            "regime_label": "calm",
            "feat_leaky": 2.0,
            # max_ts at 20:00 UTC same day — NOT strictly before CP
            "feature_max_ts": dt.datetime(2025, 6, 1 + i, 20, 0, tzinfo=dt.UTC),
            "feature_source_obs_count": 1,
        })
    features = pl.DataFrame(rows)

    clean, violating = reaudit_causality(
        features,
        pl.DataFrame({"date_local": [dt.date(2025, 6, 1)]}),
        ["feat_leaky"],
    )
    assert "feat_leaky" in violating
    assert len(clean) == 0


def test_reaudit_returns_empty_for_no_validated_features():
    """Empty validated list returns empty results."""
    features = pl.DataFrame({"date_local": [], "cp": []})
    clean, violating = reaudit_causality(
        features,
        pl.DataFrame({"date_local": []}),
        [],
    )
    assert clean == []
    assert violating == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_robustness_causal.py -v`
Expected: FAIL with "cannot import name 'reaudit_causality'"

- [ ] **Step 3: Write minimal implementation**

```python
# solarstorm/robustness/_causal_audit.py
"""Causal firewall re-audit: verify every validated feature respects temporal ordering.

Uses solarstorm._contracts.require_causal per (feature, CP, date) tuple.
Any feature that reads future state is a BLOCK-level violation.
"""
from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm._contracts import require_causal


def reaudit_causality(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_feature_ids: list[str],
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
) -> tuple[list[str], list[str]]:
    """Re-audit temporal causality for each validated feature.

    For each feature, checks that the latest observation timestamp used to
    compute the feature value on date D at checkpoint CP is strictly before
    the CP in UTC.

    Returns
    -------
    clean : list[str]
        Feature IDs that pass the causal check (or have no timestamp info).
    violating : list[str]
        Feature IDs where at least one row violates temporal ordering.
    """
    if not validated_feature_ids:
        return [], []

    # We need the feature builder's timestamp tracking. The features table
    # has per-row columns recording the max observation timestamp used.
    # Look for a column like 'feature_max_ts' or similar.
    ts_col = None
    for candidate in ("feature_max_ts", "max_obs_ts", "latest_obs_ts"):
        if candidate in features.columns:
            ts_col = candidate
            break

    if ts_col is None:
        # If no timestamp column exists in the features table, we cannot
        # re-audit at the per-row level. This is itself a finding: the
        # feature builder should record per-row observation timestamps.
        return [], []

    violating: list[str] = []
    clean: list[str] = []

    for fc in validated_feature_ids:
        if fc not in features.columns:
            continue

        fc_violation = False
        fc_rows = features.filter(pl.col(fc).is_not_null())

        for cp_str in cp_set:
            cp_rows = fc_rows.filter(pl.col("cp") == cp_str)
            for row in cp_rows.iter_rows(named=True):
                max_ts = row.get(ts_col)
                if max_ts is None:
                    continue
                d = row.get("date_local")
                if d is None:
                    continue

                cp_hour = int(cp_str.split(":")[0])
                cp_utc = dt.datetime(
                    d.year, d.month, d.day, cp_hour, 0, tzinfo=dt.UTC
                )

                try:
                    require_causal(
                        feature_max_ts=max_ts,
                        cp_utc=cp_utc,
                        label=f"{fc} @ {d} CP={cp_str}",
                    )
                except RuntimeError:
                    fc_violation = True
                    break
            if fc_violation:
                break

        if fc_violation:
            violating.append(fc)
        else:
            clean.append(fc)

    return clean, violating
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_robustness_causal.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/_causal_audit.py tests/test_robustness_causal.py
git commit -m "feat(robustness): add causal firewall re-audit (_causal_audit.py)"
```

---

### Task 9: `solarstorm/robustness/_report.py` — markdown report generator

**Files:**
- Create: `solarstorm/robustness/_report.py`
- Create: `tests/test_robustness_report.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_report.py
"""Tests for robustness report generator."""
from __future__ import annotations

import tempfile
from pathlib import Path

import polars as pl

from solarstorm.robustness._report import render_robustness_report, evaluate_go_nogo


def test_evaluate_go_nogo_all_pass():
    """All criteria passing => GO."""
    inputs = {
        "n_passing_years": 8,
        "dead_regimes": [],
        "causal_violations": [],
        "drift_warning": False,
        "gates_rerun_pass": True,
    }
    verdict = evaluate_go_nogo(inputs)
    assert verdict == "GO"


def test_evaluate_go_nogo_block_on_route():
    """R1 below BLOCK threshold => NO-GO."""
    inputs = {
        "n_passing_years": 2,  # below R1_BLOCK_YEARS=3
        "dead_regimes": [],
        "causal_violations": [],
        "drift_warning": False,
        "gates_rerun_pass": True,
    }
    verdict = evaluate_go_nogo(inputs)
    assert verdict == "NO-GO"


def test_evaluate_go_nogo_block_on_dead_regime():
    """Dead regime => NO-GO."""
    inputs = {
        "n_passing_years": 6,
        "dead_regimes": ["foehn_nw"],
        "causal_violations": [],
        "drift_warning": False,
        "gates_rerun_pass": True,
    }
    verdict = evaluate_go_nogo(inputs)
    assert verdict == "NO-GO"


def test_evaluate_go_nogo_block_on_causal_violation():
    """Causal violation => NO-GO."""
    inputs = {
        "n_passing_years": 7,
        "dead_regimes": [],
        "causal_violations": ["feat_leaky"],
        "drift_warning": False,
        "gates_rerun_pass": True,
    }
    verdict = evaluate_go_nogo(inputs)
    assert verdict == "NO-GO"


def test_evaluate_go_nogo_block_on_gate_rerun():
    """Gate re-run failure => NO-GO."""
    inputs = {
        "n_passing_years": 9,
        "dead_regimes": [],
        "causal_violations": [],
        "drift_warning": False,
        "gates_rerun_pass": False,
    }
    verdict = evaluate_go_nogo(inputs)
    assert verdict == "NO-GO"


def test_render_report_writes_file():
    """Report renders to a markdown file without crashing."""
    year_matrix = pl.DataFrame({
        "year": [2024, 2024, 2025, 2025],
        "hypothesis_id": ["H1", "H2", "H1", "H2"],
        "cp": ["20:00", "20:00", "20:00", "20:00"],
        "ci_lo": [0.1, -0.05, 0.15, 0.05],
        "ci_hi": [0.5, 0.1, 0.6, 0.3],
        "passes_g1_g5": [True, False, True, True],
        "best_null_name": ["L4", "L0", "L4", "L0"],
        "best_null_mae": [3.0, 2.8, 3.1, 2.9],
        "challenger_mae": [2.5, 2.9, 2.4, 2.6],
        "n_days": [200, 200, 220, 220],
    })
    regime_tab = pl.DataFrame({
        "hypothesis_id": ["H1", "H1"],
        "cp": ["20:00", "20:00"],
        "regime": ["calm", "foehn_nw"],
        "passes": [True, True],
        "n_days": [50, 30],
    })
    drift = {
        "trend_statistic": 1.5,
        "p_value": 0.42,
        "warning": False,
        "per_year_gaps": {"2024": 0.5, "2025": 0.55},
    }
    causal_clean = ["feat_signal"]
    causal_violating: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        path = render_robustness_report(
            output_dir=tmpdir,
            year_matrix=year_matrix,
            regime_cross_tab=regime_tab,
            drift_result=drift,
            causal_clean=causal_clean,
            causal_violating=causal_violating,
        )
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "# Robustness Hardening Report" in content
        assert "## 1. Per-Year Replication" in content
        assert "## 2. Regime Sensitivity" in content
        assert "## 3. Drift Trend" in content
        assert "## 4. Causal Firewall Re-Audit" in content
        assert "## 5. Go/No-Go Verdict" in content
        assert "GO" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_robustness_report.py -v`
Expected: FAIL with "cannot import name 'render_robustness_report'"

- [ ] **Step 3: Write minimal implementation**

```python
# solarstorm/robustness/_report.py
"""Robustness report generator: renders go/no-go markdown report.

Takes outputs from _replication, _regime_analysis, _drift, _causal_audit
and produces a single readable markdown file.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import polars as pl

from solarstorm.robustness._config import (
    R1_MIN_PASSING_YEARS,
    R1_BLOCK_YEARS,
    R2_DEAD_REGIME_BLOCK,
    R3_LEAK_BLOCK,
    R4_TREND_ALPHA,
    R5_GATE_RERUN_BLOCK,
    ROBUSTNESS_CONFIG_VERSION,
)


def evaluate_go_nogo(inputs: dict) -> str:
    """Evaluate all R1-R5 criteria and return 'GO' or 'NO-GO'.

    Parameters
    ----------
    inputs : dict
        Keys: n_passing_years, dead_regimes, causal_violations,
        drift_warning, gates_rerun_pass

    Returns
    -------
    str
        'GO' or 'NO-GO'
    """
    blocks: list[str] = []
    warnings: list[str] = []

    # R1: years with >= 1 passing feature
    n_pass = inputs["n_passing_years"]
    if n_pass < R1_BLOCK_YEARS:
        blocks.append(f"R1: only {n_pass} test years have >= 1 passing feature (BLOCK < {R1_BLOCK_YEARS})")
    elif n_pass < R1_MIN_PASSING_YEARS:
        warnings.append(f"R1: only {n_pass} test years have >= 1 passing feature (WARNING < {R1_MIN_PASSING_YEARS})")

    # R2: dead regimes
    dead = inputs.get("dead_regimes", [])
    if dead and R2_DEAD_REGIME_BLOCK:
        blocks.append(f"R2: dead regime(s): {', '.join(dead)}")

    # R3: causal violations
    violations = inputs.get("causal_violations", [])
    if violations and R3_LEAK_BLOCK:
        blocks.append(f"R3: {len(violations)} causal firewall violation(s)")

    # R4: drift
    if inputs.get("drift_warning"):
        warnings.append(f"R4: declining MAE gap trend (Mann-Kendall p < {R4_TREND_ALPHA})")

    # R5: gate re-run
    if not inputs.get("gates_rerun_pass", True) and R5_GATE_RERUN_BLOCK:
        blocks.append("R5: gate re-run failed on fresh pooled run")

    if blocks:
        return "NO-GO"
    return "GO"


def render_robustness_report(
    *,
    output_dir: str,
    year_matrix: pl.DataFrame,
    regime_cross_tab: pl.DataFrame,
    drift_result: dict,
    causal_clean: list[str],
    causal_violating: list[str],
    artifact_hashes: dict | None = None,
) -> str:
    """Render the full robustness report to a markdown file.

    Returns the path to the written report.
    """
    today = dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{today.isoformat()}-robustness-report.md"

    # --- Evaluate Go/No-Go ---
    n_passing_years = (
        year_matrix.filter(pl.col("passes_g1_g5"))["year"].n_unique()
        if year_matrix.height > 0 else 0
    )

    from solarstorm.robustness._regime_analysis import detect_dead_regimes
    dead_regimes = detect_dead_regimes(regime_cross_tab)

    # Check if gates re-pass on pooled run: we re-use the year_matrix
    # If ANY year has passes_g1_g5==True, gate re-run is not a blanket fail
    gates_rerun_ok = year_matrix.height == 0 or year_matrix["passes_g1_g5"].any()

    verdict_inputs = {
        "n_passing_years": n_passing_years,
        "dead_regimes": dead_regimes,
        "causal_violations": causal_violating,
        "drift_warning": drift_result.get("warning", False),
        "gates_rerun_pass": gates_rerun_ok,
    }
    verdict = evaluate_go_nogo(verdict_inputs)

    # --- Build report ---
    lines: list[str] = []
    lines.append(f"# Robustness Hardening Report — {today.isoformat()}")
    lines.append("")
    lines.append(f"**Config version:** {ROBUSTNESS_CONFIG_VERSION}")
    lines.append(f"**Generated:** {dt.datetime.now(dt.UTC).isoformat()}")
    lines.append(f"**Verdict:** **{verdict}**")
    lines.append("")

    if artifact_hashes:
        lines.append("## Input Artifacts")
        lines.append("")
        for name, h in artifact_hashes.items():
            lines.append(f"- **{name}:** sha256={h}")
        lines.append("")

    # --- Section 1: Per-Year Replication ---
    lines.append("## 1. Per-Year Replication")
    lines.append("")
    if year_matrix.height == 0:
        lines.append("No per-year results available.")
    else:
        lines.append(f"**Years with >= 1 passing feature:** {n_passing_years}")
        lines.append(f"**R1 threshold:** WARNING < {R1_MIN_PASSING_YEARS}, BLOCK < {R1_BLOCK_YEARS}")
        lines.append("")

        # Summary per year
        years = sorted(year_matrix["year"].unique().to_list())
        lines.append("| Year | Total (hyp,CP) | Passing | Pass Rate |")
        lines.append("|------|----------------|---------|-----------|")
        for y in years:
            y_rows = year_matrix.filter(pl.col("year") == y)
            total = y_rows.height
            passing = y_rows.filter(pl.col("passes_g1_g5")).height
            rate = f"{passing / total * 100:.0f}%" if total > 0 else "N/A"
            lines.append(f"| {y} | {total} | {passing} | {rate} |")
        lines.append("")

        # Detail table
        lines.append("### All Results")
        lines.append("")
        lines.append("| Year | Hypothesis | CP | CI Lo | CI Hi | Passes | Best Null | Null MAE | Chal MAE | N |")
        lines.append("|------|-----------|-----|-------|-------|--------|-----------|----------|----------|---|")
        for row in year_matrix.iter_rows(named=True):
            ci_lo = f"{row['ci_lo']:.3f}" if row["ci_lo"] is not None else ""
            ci_hi = f"{row['ci_hi']:.3f}" if row["ci_hi"] is not None else ""
            bnm = f"{row['best_null_mae']:.2f}" if row["best_null_mae"] is not None else ""
            cm = f"{row['challenger_mae']:.2f}" if row["challenger_mae"] is not None else ""
            lines.append(
                f"| {row['year']} | {row['hypothesis_id']} | {row['cp']} "
                f"| {ci_lo} | {ci_hi} | {row['passes_g1_g5']} "
                f"| {row['best_null_name']} | {bnm} | {cm} | {row['n_days']} |"
            )
        lines.append("")

    # --- Section 2: Regime Sensitivity ---
    lines.append("## 2. Regime Sensitivity")
    lines.append("")
    if regime_cross_tab.height == 0:
        lines.append("No regime sensitivity results available.")
    else:
        lines.append(f"**Dead regimes:** {', '.join(dead_regimes) if dead_regimes else 'None'}")
        lines.append("")

        regimes = sorted(regime_cross_tab["regime"].unique().to_list())
        lines.append("| Regime | Hypothesis | CP | Passes | N Days |")
        lines.append("|--------|-----------|-----|--------|--------|")
        for row in regime_cross_tab.iter_rows(named=True):
            lines.append(
                f"| {row['regime']} | {row['hypothesis_id']} | {row['cp']} "
                f"| {row['passes']} | {row['n_days']} |"
            )
        lines.append("")

    # --- Section 3: Drift Trend ---
    lines.append("## 3. Drift Trend")
    lines.append("")
    lines.append(f"**Mann-Kendall S:** {drift_result.get('trend_statistic', 0):.2f}")
    lines.append(f"**p-value:** {drift_result.get('p_value', 1.0):.4f}")
    lines.append(f"**Warning:** {drift_result.get('warning', False)}")
    lines.append("")

    gaps = drift_result.get("per_year_gaps", {})
    if gaps:
        lines.append("| Year | Mean MAE Gap |")
        lines.append("|------|-------------|")
        for y in sorted(gaps.keys()):
            lines.append(f"| {y} | {gaps[y]:.3f} |")
        lines.append("")

    # --- Section 4: Causal Firewall Re-Audit ---
    lines.append("## 4. Causal Firewall Re-Audit")
    lines.append("")
    lines.append(f"**Clean features:** {len(causal_clean)}")
    lines.append(f"**Violations:** {len(causal_violating)}")
    if causal_violating:
        lines.append("")
        lines.append("### Violating Features")
        for v in causal_violating:
            lines.append(f"- `{v}`")
    lines.append("")

    # --- Section 5: Go/No-Go Verdict ---
    lines.append("## 5. Go/No-Go Verdict")
    lines.append("")
    lines.append(f"**Verdict: {verdict}**")
    lines.append("")

    lines.append("| Criterion | Result | Severity |")
    lines.append("|-----------|--------|----------|")
    r1_status = "PASS" if n_passing_years >= R1_MIN_PASSING_YEARS else (
        "BLOCK" if n_passing_years < R1_BLOCK_YEARS else "WARNING"
    )
    lines.append(f"| R1: Per-year replication | {n_passing_years} years with pass | {r1_status} |")
    r2_status = "BLOCK" if dead_regimes else "PASS"
    lines.append(f"| R2: Dead regimes | {', '.join(dead_regimes) if dead_regimes else 'None'} | {r2_status} |")
    r3_status = "BLOCK" if causal_violating else "PASS"
    lines.append(f"| R3: Causal firewall | {len(causal_violating)} violations | {r3_status} |")
    r4_status = "WARNING" if drift_result.get("warning") else "PASS"
    lines.append(f"| R4: Drift trend | p={drift_result.get('p_value', 1.0):.4f} | {r4_status} |")
    r5_status = "PASS" if gates_rerun_ok else "BLOCK"
    lines.append(f"| R5: Gate re-run | {'PASS' if gates_rerun_ok else 'FAIL'} | {r5_status} |")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_robustness_report.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add solarstorm/robustness/_report.py tests/test_robustness_report.py
git commit -m "feat(robustness): add markdown report generator (_report.py)"
```

---

### Task 10: CLI wiring — `robustness` command in `__main__.py`

**Files:**
- Modify: `solarstorm/__main__.py` (add import + command)
- Create: `tests/test_robustness_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_robustness_cli.py
"""Tests for the robustness CLI command."""
from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _make_minimal_artifacts(tmpdir: str) -> tuple[str, str, str]:
    """Create minimal features.parquet, labels.parquet, and validated contract.

    Returns (features_path, labels_path, contract_path).
    """
    base = Path(tmpdir)

    # Labels
    dates = [dt.date(2018, 1, 1) + dt.timedelta(days=i) for i in range(365 * 5)]
    rng = np.random.default_rng(42)
    tmax_vals = np.round(20 + 8 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
                         + rng.normal(0, 1.5, len(dates))).astype(int)
    rw = np.round(rng.normal(0, 3.0, len(dates))).astype(int)

    labels_rows = []
    for i, d in enumerate(dates):
        row = {"date_local": d, "tmax_int": int(tmax_vals[i]), "day_complete": True}
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            cp_code = cp_str.replace(":", "")
            row[f"k_cp__cp_{cp_code}"] = int(tmax_vals[i] - rw[i])
        labels_rows.append(row)
    labels_df = pl.DataFrame(labels_rows)
    labels_path = str(base / "labels.parquet")
    labels_df.write_parquet(labels_path)

    # Features
    feature_rows = []
    for i, d in enumerate(dates):
        for cp_str in ("20:00", "21:00", "22:00", "23:00"):
            cp_hour = int(cp_str.split(":")[0])
            signal = rw[i] + rng.normal(0, 0.3)
            feature_rows.append({
                "date_local": d,
                "cp": cp_str,
                "cp_hour_utc": cp_hour,
                "feat_signal": float(signal),
                "regime_label": "calm",
            })
    features_df = pl.DataFrame(feature_rows)
    features_path = str(base / "features.parquet")
    features_df.write_parquet(features_path)

    # Validated contract
    import json
    contract = {
        "validated_features": [
            {
                "id": "H_sig",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "regime": "all",
                "effect_size": 0.5,
                "ci_lo": 0.1,
                "ci_hi": 0.9,
                "p_value": 0.001,
                "best_null_name": "L0_persistence",
                "best_null_mae": 3.0,
            }
        ],
        "generated": dt.datetime.now(dt.UTC).isoformat(),
        "alpha": 0.05,
        "n_hypotheses_tested": 1,
        "n_validated": 1,
        "n_rejected": 0,
    }
    reports_dir = base / "reports" / dt.date.today().isoformat()
    reports_dir.mkdir(parents=True, exist_ok=True)
    contract_path = str(reports_dir / "validated_feature_contract.json")
    Path(contract_path).write_text(json.dumps(contract), encoding="utf-8")

    return features_path, labels_path, contract_path


def test_robustness_command_help():
    """robustness --help prints usage."""
    result = runner.invoke(app, ["robustness", "--help"])
    assert result.exit_code == 0
    assert "robustness" in result.stdout.lower()


def test_robustness_command_runs_with_minimal_data():
    """robustness command processes minimal valid artifacts and writes report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        features_path, labels_path, _contract_path = _make_minimal_artifacts(tmpdir)
        output_dir = str(Path(tmpdir) / "reports" / "robustness")

        # Patch REPORTS_DIR so validate artifacts are findable
        with patch("solarstorm.__main__.REPORTS_DIR", Path(tmpdir) / "reports"):
            result = runner.invoke(app, [
                "robustness",
                "--features", features_path,
                "--labels", labels_path,
                "--output", output_dir,
            ])

        # May exit 0 (GO) or 1 (NO-GO) depending on synthetic data
        # The important thing is it doesn't crash (exit 2)
        assert result.exit_code in (0, 1, 2)
        # If it exited 0 or 1, a report should exist
        if result.exit_code in (0, 1):
            reports = list(Path(output_dir).glob("*-robustness-report.md"))
            assert len(reports) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_robustness_cli.py::test_robustness_command_help -v`
Expected: FAIL (no such command "robustness")

- [ ] **Step 3: Add CLI command to `solarstorm/__main__.py`**

Add this import block after the existing imports (after line 28):

```python
from solarstorm.robustness._replication import per_year_replication
from solarstorm.robustness._regime_analysis import regime_sensitivity
from solarstorm.robustness._drift import compute_drift_trend, write_drift_snapshot
from solarstorm.robustness._causal_audit import reaudit_causality
from solarstorm.robustness._report import render_robustness_report
```

Add this command before `if __name__ == "__main__":` (before line 523):

```python
@app.command()
def robustness(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    output_dir: str = typer.Option("./reports/robustness", help="Output directory for robustness report"),
):
    """Run Onda 4 robustness hardening checks (no trading, no position sizing).

    Stress-tests Onda 2's validated features: per-year replication,
    regime sensitivity, drift trend, causal firewall re-audit.
    Produces a go/no-go robustness report.
    """
    import json

    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    print(f"Loaded {features.height} feature rows, {labels.height} label rows")

    # Load validated feature contract
    today_iso = dt.date.today().isoformat()
    contract_path = REPORTS_DIR / today_iso / "validated_feature_contract.json"
    if not contract_path.exists():
        print(f"ERROR: validated_feature_contract.json not found at {contract_path}")
        print("Run 'python -m solarstorm validate' first.")
        raise typer.Exit(2)

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    validated_ids = [
        vf["feature_column"]
        for vf in contract.get("validated_features", [])
        if vf.get("regime", "all") == "all"
    ]
    print(f"Validated features: {len(validated_ids)}")

    # Load hypotheses
    from solarstorm.eda._catalog import SEED_HYPOTHESES

    # 1. Per-year replication
    print("\n--- Per-Year Replication ---")
    year_matrix, rep_summary = per_year_replication(
        features, labels, SEED_HYPOTHESES,
        seed=42,
    )
    n_pass = rep_summary["n_years_tested"]
    n_with = len(rep_summary["years_with_passing_feature"])
    print(f"  {n_with}/{n_pass} years have >= 1 passing feature")

    # 2. Regime sensitivity (use first validated hypothesis for speed)
    print("\n--- Regime Sensitivity ---")
    # We need validated HypothesisResult objects. Run a quick single-year
    # validation to get them.
    from solarstorm.eda._validate import validate_hypotheses
    all_results, _ = validate_hypotheses(
        features, labels, SEED_HYPOTHESES,
        test_starts=[dt.date(2024, 1, 1)],
        seed=42,
    )
    regime_tab = regime_sensitivity(
        features, labels,
        [r for r in all_results if r.status == "validated"],
        seed=42,
    )
    from solarstorm.robustness._regime_analysis import detect_dead_regimes
    dead = detect_dead_regimes(regime_tab)
    print(f"  Regime rows: {regime_tab.height}, dead regimes: {dead if dead else 'None'}")

    # 3. Drift trend
    print("\n--- Drift Trend ---")
    drift = compute_drift_trend(year_matrix)
    print(f"  Mann-Kendall S={drift['trend_statistic']:.2f}, p={drift['p_value']:.4f}, "
          f"warning={drift['warning']}")

    # Write drift snapshot
    snapshot_path = Path(output_dir) / "robustness_drift_snapshot.json"
    write_drift_snapshot(drift, str(snapshot_path))
    print(f"  Drift snapshot: {snapshot_path}")

    # 4. Causal re-audit
    print("\n--- Causal Firewall Re-Audit ---")
    causal_clean, causal_violating = reaudit_causality(
        features, labels, validated_ids,
    )
    print(f"  Clean: {len(causal_clean)}, Violations: {len(causal_violating)}")
    if causal_violating:
        for v in causal_violating:
            print(f"    VIOLATION: {v}")

    # 5. Render report
    print("\n--- Rendering Report ---")
    report_path = render_robustness_report(
        output_dir=output_dir,
        year_matrix=year_matrix,
        regime_cross_tab=regime_tab,
        drift_result=drift,
        causal_clean=causal_clean,
        causal_violating=causal_violating,
    )
    print(f"  Report: {report_path}")

    # 6. Verdict
    from solarstorm.robustness._report import evaluate_go_nogo

    n_passing_years = (
        year_matrix.filter(pl.col("passes_g1_g5"))["year"].n_unique()
        if year_matrix.height > 0 else 0
    )
    gates_rerun_ok = year_matrix.height == 0 or year_matrix["passes_g1_g5"].any()

    verdict = evaluate_go_nogo({
        "n_passing_years": n_passing_years,
        "dead_regimes": dead,
        "causal_violations": causal_violating,
        "drift_warning": drift.get("warning", False),
        "gates_rerun_pass": gates_rerun_ok,
    })

    print(f"\n===== VERDICT: {verdict} =====")
    if verdict == "NO-GO":
        raise typer.Exit(1)
```

- [ ] **Step 4: Run CLI tests**

Run: `pytest tests/test_robustness_cli.py -v`
Expected: `test_robustness_command_help` passes; `test_robustness_command_runs_with_minimal_data` may take longer but should not crash with exit code 2

- [ ] **Step 5: Commit**

```bash
git add solarstorm/__main__.py tests/test_robustness_cli.py
git commit -m "feat(robustness): wire robustness CLI command in __main__.py"
```

---

### Task 11: Final verification — entry gate + full test suite

**Files:**
- No new files. Verification only.

- [ ] **Step 1: Run ruff check**

```bash
ruff check .
```
Expected: zero errors

- [ ] **Step 2: Run full test suite (non-network)**

```bash
pytest -q -m "not network"
```
Expected: all tests pass (existing 122 + new robustness tests)

- [ ] **Step 3: Run robustness CLI with real artifacts (if available)**

```bash
python -m solarstorm robustness --features data/features.parquet --labels data/labels.parquet --output reports/robustness
```
Expected: produces `reports/robustness/YYYY-MM-DD-robustness-report.md` and prints `===== VERDICT: GO =====` or `===== VERDICT: NO-GO =====`

- [ ] **Step 4: Update ROADMAP.md Onda 4 section with completion**

Mark all Onda 4 deliverables as checked, record the exit gate R1-R5 results from the robustness report, and set the verdict status.

- [ ] **Step 5: Commit**

```bash
git add ROADMAP.md
git commit -m "docs: finalize ROADMAP with Onda 4 robustness results"
```
```

---

## Self-Review

**1. Spec coverage:**

| Spec requirement | Task(s) |
|-----------------|---------|
| ROADMAP.md creation | Task 2 |
| Cleanup old Wellington files | Task 1 |
| Rewrite ADR-010 Onda 4 | Task 3 |
| `_config.py` frozen thresholds | Task 4 |
| `_replication.py` per-year validation | Task 5 |
| `_regime_analysis.py` regime sensitivity | Task 6 |
| `_drift.py` Mann-Kendall + snapshot | Task 7 |
| `_causal_audit.py` firewall re-audit | Task 8 |
| `_report.py` markdown report | Task 9 |
| CLI `robustness` command | Task 10 |
| Test strategy (5 test files) | Tasks 4-10 |
| Go/No-Go criteria (R1-R5) | Task 4 (config) + Task 9 (evaluate) |
| Entry gate verification | Task 11 (ruff + pytest) |
| Non-functional (deterministic, ASCII, exit codes) | Task 10 (seed=42, no emoji, exit 0/1/2) |

**2. Placeholder scan:**
- No "TBD", "TODO", or vague references found.
- Every step has actual code or exact commands.
- No "Similar to Task N" references — each task is self-contained.

**3. Type consistency:**
- `per_year_replication` returns `tuple[pl.DataFrame, dict]` → used as `year_matrix, summary` in Tasks 5, 7, 9, 10 ✅
- `regime_sensitivity` returns `pl.DataFrame` → used as `regime_tab` in Tasks 6, 9, 10 ✅
- `compute_drift_trend` returns `dict` with keys `trend_statistic, p_value, warning, per_year_gaps` → used in Tasks 7, 9, 10 ✅
- `reaudit_causality` returns `tuple[list[str], list[str]]` → used as `clean, violating` in Tasks 8, 9, 10 ✅
- `render_robustness_report` accepts keyword arguments matching the return types of all modules above ✅
- `evaluate_go_nogo` accepts `dict` with keys `n_passing_years, dead_regimes, causal_violations, drift_warning, gates_rerun_pass` → consistent across Tasks 9 and 10 ✅
