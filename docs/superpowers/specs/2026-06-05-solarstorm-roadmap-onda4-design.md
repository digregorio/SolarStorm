# SolarStorm ROADMAP + Onda 4 Robustness — Design

> Supersession note, 2026-06-06: the regime assumptions in this spec are stale.
> ADR-011 and `docs/onda2r_regime_ontology_repair_plan.md` supersede the old
> required 5-regime list. `late_warming` is now treated as a timing-risk target,
> not a causal physical regime.
> Historical code blocks in this file that name
> `calm`/`transition`/`late_warming`/`foehn_nw`/`disrupted` are not executable
> guidance for current work. Use `docs/regime_model_card.md` and
> `solarstorm/eda/_regimes.py`.

**Date:** 2026-06-05
**Status:** Accepted
**Context:** Onda 0/1/2 complete; Onda 3 not started; Onda 4 needs clean redefinition
**Scope update 2026-06-06:** Onda 4 is model-first robustness. Financial
execution, EV, position sizing, shadow trading, and Polymarket API work are on
hold until Onda 3 proves a production model.

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
## Onda 3: Models 🔮 (historically gated on Onda 4; now also gated on Onda C)
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

Stress-test Onda 2's current validated feature-null hypotheses before investing
in Onda 3 ML models. The validated count must be read from the latest
`validated_feature_contract.json`; do not hard-code a stale count. Confirm the
foundation is not a split-design artifact, regime-specific fluke,
temporal-leakage ghost, nowcast proxy, or fixed-CP timing artifact.

### 3.1a Entry Gate

Before Onda 4 hardening code runs, the following must pass:

1. Fresh Onda 2 artifacts exist and are not marked superseded:
   - `data/features.parquet`
   - `data/labels.parquet`
   - `reports/2026-06-05/validated_feature_contract.json`
   - `reports/2026-06-05/hypothesis_results.json`
2. `ruff check .` passes with zero errors.
3. `pytest -q -m "not network"` passes with zero failures.
4. Historical pre-Onda 2R context / superseded, not executable guidance: the old 5 regime labels were confirmed as `calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted` (verifiable at the time via `solarstorm.eda._regimes.classify_regime`).
5. The Onda 4 scope is model-first robustness only; financial, shadow, and live-market work is on hold.

These are verifiable as a bash script or manual checklist before any robustness code runs.

### 3.2 Why Not Shadow/Trading

The old Wellington project's "Fase 8 — Shadow trading + EV" (quarentena) was designed for a system that predicated Polymarket fills and economic edge. SolarStorm has no trade-execution layer, no position-sizing policy, and no model. Importing shadow-trading into Onda 4 would replicate the old project's core mistake: building downstream on an untested foundation.

The correct Onda 4 is a **hardening gate**: prove the foundation holds under
stress before building on it. It must also prove that apparent skill is not
nowcasting, not an artifact of fixed CP timing, and not blind to late-spike
regimes.

### 3.3 Architecture

```
solarstorm/robustness/          ← new package
├── __init__.py
├── _replication.py             ← per-test-year validation runner
├── _regime_analysis.py         ← regime × feature cross-tabulation
├── _drift.py                   ← calendar-time performance trend
├── _causal_audit.py            ← firewall re-audit on validated features
├── _lead_time.py               ← anti-nowcast lead-time analysis
├── _tmax_hour.py               ← physical Tmax-hour stratification
├── _late_spike.py              ← late-spike evidence pack
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

**Regime labels** (historical pre-Onda 2R context / superseded, not executable guidance; formerly from `solarstorm.eda._regimes`): `calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted`.

**Dead-regime detection:** If all currently validated hypotheses fail G4/G5 in
a specific regime, that regime is "dead" -> BLOCK exit gate.

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

#### `_lead_time.py` — Anti-Nowcast Lead-Time Analysis

Separates genuine prediction from nowcasting. For every validated
(hypothesis, CP), report skill by lead-time bucket and whether the observed Tmax
had already occurred before the cutoff. Skill that appears only after the answer
is effectively known blocks Onda 3.

**Interface:**
```python
def lead_time_skill(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_hypotheses: list[HypothesisResult],
    *,
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
    seed: int = 42,
) -> pl.DataFrame:
    """Return skill by hypothesis_id, cp, lead_time_bucket, tmax_already_seen."""
```

#### `_tmax_hour.py` — Physical Tmax-Hour Stratification

Evaluates feature skill by regime, month, and observed/expected Tmax-hour
buckets. Fixed CPs remain contractual evaluation cutoffs, but they must not be
treated as the physical clock of Tmax.

**Interface:**
```python
def tmax_hour_stratification(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_hypotheses: list[HypothesisResult],
    *,
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
) -> pl.DataFrame:
    """Return skill by hypothesis_id, cp, regime, month, tmax_hour_bucket."""
```

#### `_late_spike.py` — Late-Spike Evidence Pack

Builds an artifact of days where one or more CPs looked settled (`k_cp` near the
eventual market consensus) but final Tmax increased later. This is not a
trading artifact. It is future model research material, especially for
Open-Meteo/NWP features.

**Interface:**
```python
def late_spike_candidates(
    labels: pl.DataFrame,
    *,
    cp_set: tuple[str, ...] = ("20:00","21:00","22:00","23:00"),
) -> pl.DataFrame:
    """Return dates/CPs where Tmax increased after the cutoff."""
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
5. Drift analysis -> trend dict + write snapshot
6. Causal re-audit -> clean/violating lists
7. Lead-time anti-nowcast analysis
8. Physical Tmax-hour stratification
9. Late-spike evidence pack
10. Evaluate go/no-go criteria
11. Render report
12. Print verdict to stdout

### 3.6 Go/No-Go Criteria

| ID | Criterion | Threshold | Severity |
|----|-----------|-----------|----------|
| R1 | Test years with >= 1 feature passing G1-G5 + FDR | >= 5 of 12 | WARNING if <5, **BLOCK** if <3 |
| R2 | No dead regime | >= 1 feature passes G4/G5 per regime | **BLOCK** if any regime dead |
| R3 | Causal firewall clean | 0 violations in validated features | **BLOCK** if any violation |
| R4 | MAE gap stable over calendar time | Mann-Kendall p > 0.05 | WARNING if declining |
| R5 | Gates re-pass on fresh pooled run | All G1-G5 pass | **BLOCK** if any gate fails |
| R6 | Anti-nowcast lead-time check | Skill exists before Tmax is effectively known | **BLOCK** if skill is only post-answer |
| R7 | Physical Tmax-hour stratification | Skill is not only a fixed-CP artifact | **BLOCK** if fixed CP timing creates apparent skill |
| R8 | Late-spike evidence pack | Artifact produced for future modeling | WARNING if absent |

**Go:** All BLOCK criteria pass. Foundation is robust for the next active gate.
This historical Onda 4 result does not by itself authorize Onda 3. If a
required intervening wave such as Onda C is registered, that wave must pass
before any Onda 3 design review starts.
**No-Go:** >= 1 BLOCK criterion fails -> Onda 3 remains blocked until root cause is addressed and the robustness report reruns.

### 3.7 Test Strategy

Each module gets a unit-test file in `tests/`:

| Module | Test file | Key tests |
|--------|-----------|-----------|
| `_replication.py` | `tests/test_robustness_replication.py` | Per-year splits use correct train/test bounds; year matrix has expected shape |
| `_regime_analysis.py` | `tests/test_robustness_regime.py` | Dead-regime detection with synthetic data; cross-tab completeness |
| `_drift.py` | `tests/test_robustness_drift.py` | Mann-Kendall on known trend/no-trend series; snapshot round-trips |
| `_causal_audit.py` | `tests/test_robustness_causal.py` | Known-violation synthetic features flagged; clean features pass |
| `_lead_time.py` | `tests/test_robustness_lead_time.py` | Tmax-already-seen rows are separated from predictive rows |
| `_tmax_hour.py` | `tests/test_robustness_tmax_hour.py` | Month/regime/Tmax-hour buckets are complete |
| `_late_spike.py` | `tests/test_robustness_late_spike.py` | Synthetic late-spike days are detected |
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
- Shadow trading / shadow decisions
- Polymarket API integration
- Onda 3 model building (historically depended on this robustness report's
  "go"; current work also requires Onda C and the active ADR sequence)
- Open-Meteo/NWP ingestion implementation (future Onda 3+ model input focused on late spikes)
- Modifying any existing Onda 0/1/2 code beyond what the robustness package needs to import
