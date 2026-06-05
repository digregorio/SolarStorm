# SolarStorm ROADMAP + Onda 4 Robustness — Design

**Date:** 2026-06-05
**Status:** Accepted
**Context:** Onda 0/1/2 complete; Onda 3 not started; Onda 4 needs clean redefinition

---

## 1. The Problem

Two problems exist simultaneously:

1. **No single document tracks wave progress.** ADR-010 (`docs/decisions/010-onda-waves.md`) records the *decision* and high-level wave definitions, but doesn't track status, completion dates, artifact paths, or gate pass/fail. The project has no living roadmap.

2. **The current Onda 4 docs (`docs/onda4_readiness_plan.md`, `docs/live_shadow_runbook.md`) are contaminated.** They import the old quarantined Wellington project's "Fase 8 — Shadow trading + EV" framing (position-sizing, equity curves, EV, drawdown, Sharpe). Those concepts belong to the failed project, not SolarStorm. Onda 4 must be redefined from SolarStorm-native principles.

---

## 2. ROADMAP.md

### 2.1 Purpose

`ROADMAP.md` (repo root) is the living status tracker for all ondas. It complements ADR-010: the ADR explains the *why*, the ROADMAP tracks the *what* and *when*.

### 2.2 Structure

```markdown
# SolarStorm — Project Roadmap

## Legend
✅ complete | ⏳ in progress | ⏸️ blocked | 🔮 planned | ⚠️ at risk

## Onda 0: Scaffold ✅ (2026-06-04)
## Onda 1: Baselines ✅ (2026-06-04)
## Onda 2: Prove Value ✅ (2026-06-05)
## Onda 3: Models 🔮 (gated on Onda 4 go)
## Onda 4: Robustness Hardening ⏳ (2026-06-05 → )

### Onda 4 Detail ← expanded inline, task-level

#### Entry Gate
- [ ] Item ...

#### Deliverables
- [ ] Task ...

#### Exit Gate (Go/No-Go Criteria)
```

### 2.3 Conventions

- **Completed ondas** (0/1/2): one summary table each — deliverable name, status emoji, gate result, artifact path link. ~8-12 lines.
- **Active onda** (4): expanded task-level detail inline, with checkboxes. Serves as the Onda 4 mini-implementation-plan.
- **Future ondas** (3): status blurb, gating condition, no task detail.
- **All artifact paths are relative to repo root**, clickable in GitHub/rendered markdown.
- **Dates are absolute** (2026-06-04, not "yesterday").

---

## 3. Onda 4: Robustness Hardening

### 3.1 Purpose

Stress-test Onda 2's 72 validated feature-null hypotheses before investing in Onda 3 ML models. Confirm the foundation is not a split-design artifact, regime-specific fluke, or temporal-leakage ghost.

### 3.1a Entry Gate

Before Onda 4 hardening code runs, the following must pass:

1. Fresh Onda 2 artifacts exist and are not marked superseded:
   - `data/features.parquet`
   - `data/labels.parquet`
   - `reports/2026-06-05/validated_feature_contract.json`
   - `reports/2026-06-05/hypothesis_results.json`
2. `ruff check .` passes with zero errors.
3. `pytest -q -m "not network"` passes with zero failures.
4. The 5 regime labels are confirmed as `calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted` (verifiable via `solarstorm.eda._regimes.classify_regime`).

These are verifiable as a bash script or manual checklist before any robustness code runs.

### 3.2 Why Not Shadow/Trading

The old Wellington project's "Fase 8 — Shadow trading + EV" (quarentena) was designed for a system that predicated Polymarket fills and economic edge. SolarStorm has no trade-execution layer, no position-sizing policy, and no model. Importing shadow-trading into Onda 4 would replicate the old project's core mistake: building downstream on an untested foundation.

The correct Onda 4 is a **hardening gate**: prove the foundation holds under stress before building on it.

### 3.3 Architecture

```
solarstorm/robustness/          ← new package
├── __init__.py
├── _replication.py             ← per-test-year validation runner
├── _regime_analysis.py         ← regime × feature cross-tabulation
├── _drift.py                   ← calendar-time performance trend
├── _causal_audit.py            ← firewall re-audit on validated features
├── _report.py                  ← markdown report generator
└── _config.py                  ← frozen go/no-go thresholds

solarstorm/__main__.py          ← + robustness CLI command

reports/robustness/             ← artifact directory
└── YYYY-MM-DD-robustness-report.md

ROADMAP.md                      ← new (root level)
```

### 3.4 New Module: `solarstorm/robustness/`

#### `_replication.py` — Per-Test-Year Validation

Re-runs `validate_hypotheses()` once per individual test year (not pooled). For each test year Y, the train window is all data from history start through Y-01-01 minus one day — an expanding-window holdout where only one calendar year is tested at a time. Produces a year-by-year pass matrix.

**Interface:**
```python
def per_year_replication(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    hypotheses: list[Hypothesis],
    *,
    test_years: tuple[int, ...] = (2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025),
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
    seed: int = 42,
) -> tuple[pl.DataFrame, dict]:
    """Return (year_matrix, summary_dict)."""
```

**Train rule per year Y:** train_start = history_start (earliest complete day in labels); train_end = Y-01-01 minus one day; test_start = Y-01-01; test_end = Y-12-31 (or Y+1-01-01 minus one day for leap-year safety).

**Year matrix columns:** `year`, `hypothesis_id`, `cp`, `ci_lo`, `ci_hi`, `passes_g1_g5`, `best_null_name`, `best_null_mae`, `challenger_mae`, `n_days`

#### `_regime_analysis.py` — Regime Sensitivity

For each validated (hypothesis, CP), cross-tabulate pass/fail by regime, outputting a regime vulnerability map.

**Interface:**
```python
def regime_sensitivity(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_hypotheses: list[HypothesisResult],
    *,
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
    seed: int = 42,
) -> pl.DataFrame:
    """Return regime_cross_tab with columns: hypothesis_id, cp, regime, passes, n_days."""
```

**Regime labels** (from `solarstorm.eda._regimes`): `calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted`.

**Dead-regime detection:** If ALL 72 hypotheses fail G4/G5 in a specific regime, that regime is "dead" → BLOCK exit gate.

#### `_drift.py` — Performance Trend Tracking

Compute the feature-null MAE gap per calendar year and test for a declining trend (Mann-Kendall on the gap series). Writes a drift snapshot for future comparison.

**Interface:**
```python
def compute_drift_trend(
    year_matrix: pl.DataFrame,
) -> dict:
    """Return dict with trend_statistic, p_value, warning, per_year_gaps."""

def write_drift_snapshot(
    trend: dict,
    path: str,
) -> None:
    """Write robustness_drift_snapshot.json."""
```

#### `_causal_audit.py` — Causal Firewall Re-Audit

For each validated feature, verify temporal ordering: feature values for date D at checkpoint CP must only use observations with `ts_utc < cp_utc`. Uses `solarstorm._contracts.require_causal(feature_max_ts, cp_utc, label)` per (feature, CP, date) tuple. Iterates through the feature builder's per-row timestamps; any row where `require_causal` would raise → violation. Any violation → BLOCK.

**Interface:**
```python
def reaudit_causality(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_feature_ids: list[str],
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
) -> tuple[list[str], list[str]]:
    """Return (clean_feature_ids, violating_feature_ids).

    For each (feature_id, cp), computes the maximum observation timestamp
    used by that feature on each date, and asserts it's strictly before the CP.
    """
```

#### `_report.py` — Report Generator

Renders `reports/robustness/YYYY-MM-DD-robustness-report.md` from the four analysis outputs.

**Sections:**
1. Header (date, run ID, hash of input artifacts)
2. Replication: year-by-year pass matrix table
3. Regime Sensitivity: regime × feature heatmap
4. Drift: gap trend chart (ascii/sparkline) + Mann-Kendall test result
5. Causal Audit: clean count, violations (if any)
6. Go/No-Go: each criterion, result, overall verdict
7. Input artifacts referenced (leaderboard, validated_contract, features.parquet hashes)

#### `_config.py` — Frozen Thresholds

```python
# Go/No-Go thresholds — frozen 2026-06-05, bump version if changed
R1_MIN_PASSING_YEARS = 5       # WARNING below this
R1_BLOCK_YEARS = 3             # BLOCK below this
R2_DEAD_REGIME_BLOCK = True    # BLOCK if any regime has 0 feature passes
R3_LEAK_BLOCK = True           # BLOCK if any feature reads future state
R4_TREND_ALPHA = 0.05          # Mann-Kendall significance threshold
R5_GATE_RERUN_BLOCK = True     # BLOCK if any gate fails on fresh pooled run

ROBUSTNESS_CONFIG_VERSION = "1.0"
```

### 3.5 CLI Wiring

Add to `solarstorm/__main__.py`:

```python
@app.command()
def robustness(
    features_path: Annotated[str, typer.Option("--features")] = "data/features.parquet",
    labels_path: Annotated[str, typer.Option("--labels")] = "data/labels.parquet",
    output_dir: Annotated[str, typer.Option("--output")] = "reports/robustness",
) -> None:
    """Run Onda 4 robustness hardening checks (no trading, no position sizing)."""
```

Flow:
1. Load features + labels
2. Load validated feature contract
3. Per-year replication → year matrix
4. Regime sensitivity → regime cross-tab
5. Drift analysis → trend dict + write snapshot
6. Causal re-audit → clean/violating lists
7. Evaluate go/no-go criteria
8. Render report
9. Print verdict to stdout

### 3.6 Go/No-Go Criteria

| ID | Criterion | Threshold | Severity |
|----|-----------|-----------|----------|
| R1 | Test years with >= 1 feature passing G1-G5 + FDR | >= 5 of 12 | WARNING if <5, **BLOCK** if <3 |
| R2 | No dead regime | >= 1 feature passes G4/G5 per regime | **BLOCK** if any regime dead |
| R3 | Causal firewall clean | 0 violations in validated features | **BLOCK** if any violation |
| R4 | MAE gap stable over calendar time | Mann-Kendall p > 0.05 | WARNING if declining |
| R5 | Gates re-pass on fresh pooled run | All G1-G5 pass | **BLOCK** if any gate fails |

**Go:** All BLOCK criteria pass. Foundation is robust → Onda 3 may proceed.
**No-Go:** >= 1 BLOCK criterion fails → Onda 3 remains blocked until root cause is addressed and the robustness report reruns.

### 3.7 Test Strategy

Each module gets a unit-test file in `tests/`:

| Module | Test file | Key tests |
|--------|-----------|-----------|
| `_replication.py` | `tests/test_robustness_replication.py` | Per-year splits use correct train/test bounds; year matrix has expected shape |
| `_regime_analysis.py` | `tests/test_robustness_regime.py` | Dead-regime detection with synthetic data; cross-tab completeness |
| `_drift.py` | `tests/test_robustness_drift.py` | Mann-Kendall on known trend/no-trend series; snapshot round-trips |
| `_causal_audit.py` | `tests/test_robustness_causal.py` | Known-violation synthetic features flagged; clean features pass |
| `_report.py` | `tests/test_robustness_report.py` | Report renders without crashing; sections present; verdict matches inputs |
| CLI | `tests/test_robustness_cli.py` (or extend existing) | `robustness` subcommand exits 0 on valid inputs |

### 3.8 Non-Functional Requirements

- **Deterministic:** All seeds fixed (bootstrap seed = 42, walk-forward splits deterministic based on history_start)
- **Reproducible:** Report header includes SHA256 hashes of input artifacts (features.parquet, labels.parquet, validated_feature_contract.json)
- **No network calls:** Everything reads from local parquet/JSON artifacts
- **ASCII:** No emoji in CLI output except in rendered markdown report
- **Exit codes:** 0 = go, 1 = no-go (any BLOCK fails), 2 = runtime error

---

## 4. Cleanup: Contaminated Files

### 4.1 Delete (old Wellington plan files)

These are the quarantined old project's spec files that contaminate the workspace:
- `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/design.md`
- `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/implementation-plan.md`
- `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/README.md`
- `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/requirements.md`
- `quarentena/Wellington/.kiro/specs/polymarket-tmax-forecaster/tasks.md`

These are untracked (quarentena/ is in .gitignore), so no git history is affected.

### 4.2 Rewrite/Replace

| Current file | Action | Replacement |
|-------------|--------|-------------|
| `docs/onda4_readiness_plan.md` | Delete | Replaced by this design + the implementation plan |
| `docs/live_shadow_runbook.md` | Delete | Shadow-trading concept removed entirely |
| `docs/decisions/010-onda-waves.md` (Onda 4 section, lines 59-87) | Rewrite | Update to match the redefined robustness scope |

### 4.3 New files

| File | Purpose |
|------|---------|
| `ROADMAP.md` (repo root) | Living all-ondas status tracker |
| `docs/superpowers/specs/2026-06-05-solarstorm-roadmap-onda4-design.md` | This design document |

---

## 5. Out of Scope (Explicit)

- Live trading execution (separate ADR)
- Position sizing, EV, Sharpe, drawdown (old-project concepts, quarantined)
- Polymarket API integration
- Onda 3 model building (gated on this robustness report's "go")
- Modifying any existing Onda 0/1/2 code beyond what the robustness package needs to import
