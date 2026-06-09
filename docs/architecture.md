# SolarStorm Architecture

Pipeline overview, module map, and data flow for the Onda 0-4 foundation.

SolarStorm is data-first before it is model-first. Financial execution, EV,
position sizing, shadow trading, and Polymarket API integration are
intentionally out of scope until a production model proves predictive skill,
calibrated uncertainty, and stay-out behavior.

## Pipeline

```
ingest -> labels -> features -> baselines -> validate -> leaderboard -> robustness
                         ^
                         |
                 onda2e -> evidence decisions -> regime-design-validate
```

Each stage produces a versioned, reproducible artifact (P5). The pipeline is
executed via the CLI (`tmax` entry point, defined in `solarstorm/__main__.py`).

## Data Flow

```
  IEM ASOS (HTTP)
       |
       v
  obs.parquet              <- ingest: fetch + parse METAR, persist enriched parquet
       |
       v
  labels.parquet           <- labels: Tmax/CP, k_cp, remaining_warming, day_complete
       |
       v
  features.parquet         <- features: causal feature columns (H1-H23) per (date, CP)
       |
       v
  hypothesis_results.json  <- validate: walk-forward bootstrap CI + FDR + gates
       |
       v
  validated_feature_contract.json
       |
       v
  leaderboard              <- leaderboard: permanent scoreboard artifact (JSON + MD)
       |
       v
  robustness reports       <- Onda 4 go/no-go evidence, no financial layer

  onda2e decision register <- ADR-012 gate before regimes/features/models
  regime-design reports    <- offline candidate labels and R2 screening only
```

## Module Map

```
solarstorm/
  __init__.py          # package version
  __main__.py          # CLI (typer): ingest, baselines, features, validate, leaderboard, eda, robustness
  _config.py           # Centralised constants: ICAO, TZ_NAME, CP_SET_UTC, SEED
  _contracts.py        # Causal firewall (P1): require_causal(), ensure_closed_left()
  data/
    _iem.py            # IEM ASOS HTTP client with parquet caching
    _metar.py          # Regex METAR parser (TT/DD from raw text)
    _obs.py            # Per-observation enrichment (dwp, dewpoint depression)
    _labels.py         # Daily Tmax labels, k_cp per CP, day_complete, risco_de_flip
    _calendar.py       # NZST/DST calendar: cp_to_utc(), day_local_window()
    _settlement.py     # Integer settlement: bracket_for(), flip_risk()
  baselines/
    _climatology.py    # L2: DOY-smoothed circular convolution (31d), monthly percentiles
    _empirical.py      # L4: Empirical conditional P(k_eod | month, CP, k_cp)
    _ladder.py         # Baseline ladder: LadderResult, best_null_for_cp()
    _persistence.py    # L0: Persistence baseline
  features/
    builder.py         # Causal feature builder: H1-H23 columns, coverage manifest
  eda/
    _catalog.py        # SEED_HYPOTHESES list (H1-H23)
    _hypotheses.py     # Hypothesis dataclass + run_hypothesis_test()
    _regimes.py        # historical heuristic classifier; superseded by Onda 2R design
    _validate.py       # Walk-forward bootstrap validation harness
  eval/
    _bootstrap.py      # Paired bootstrap CI for mean difference
    _gates.py          # Frozen gates G1-G5 (G4 non-demotable)
    _leaderboard.py    # Leaderboard builder + JSON/MD export
    _metrics.py        # Forecast evaluation metrics
    _segments.py       # Evaluation segments
    _walkforward.py    # Expanding-window walk-forward splits
```

## Key Contracts

| File              | Purpose                                                   |
|-------------------|-----------------------------------------------------------|
| `_config.py`      | Station identity (ICAO=NZWN), CP set, timezone, seed      |
| `_contracts.py`   | Causal firewall invariant, temporal window semantics      |
| `_settlement.py`  | Integer output layer: commercial rounding, flip risk      |

## Directory Structure

```
data/                   # Parquet artifacts (obs, labels, features)
  obs.parquet
  labels.parquet
  features.parquet
reports/                # Versioned outputs
  YYYY-MM-DD/
    hypothesis_results.json
    hypothesis_results.md
    validated_feature_contract.json
    feature_coverage.json
  leaderboard/
    YYYY-MM-DDTHHMMZ-leaderboard.json
    YYYY-MM-DDTHHMMZ-leaderboard.md
    latest-leaderboard.json
    latest-leaderboard.md
  value/
    value-report-v2.md
  hypotheses/
    YYYY-MM-DD-hypotheses.json
    YYYY-MM-DD-hypotheses.md
  onda2e/
    thesis_registry.csv
    thesis_testability_audit.csv
    prereq_*.csv
    evidence_decision_register.csv
    regime_design_queue.csv
    feature_candidate_queue.csv
    rejection_register.csv
    quarantined_baseline_register.csv
    onda2e_decision_report.md
  regime-design/
    regime_candidate_assignments_v1.csv
    regime_candidate_ontology_v1.csv
    regime_candidate_assignment_audit.csv
    regime_candidate_validation_scope.csv
    regime_candidate_r2_validation.csv
    regime_candidate_decision_update.csv
    regime_candidate_validation_report.md
tests/                  # unit and regression tests
archive/wellington-legacy/  # Frozen prior iteration (no predictive value)
quarentena/             # Historical reports, postmortems, and legacy contracts
```

## Entry Points

```bash
pip install -e ".[dev]"
tmax ingest          # Backfill METAR from IEM (2009-present)
tmax features        # Build causal feature columns
tmax baselines       # Fit L0-L4 baselines
tmax validate        # Run hypothesis validation harness
tmax leaderboard     # Evaluate baselines, export leaderboard
tmax robustness      # Run Onda 4 go/no-go robustness checks
tmax onda2e          # Generate Onda 2E EDA and decision-gate registers
tmax regime-design-validate  # Offline WCT-REGIME-016 candidate R2 screening
tmax eda             # Export hypothesis catalog
```

## Evaluation vs Continuous Updates

The contractual CPs are evaluation cutoffs. They define what information was
available at a forecast time, but they are not the physical clock for Tmax.
Regime and month can shift the plausible Tmax hour.

METAR ingestion and feature processing should remain continuous after a CP has
passed. Later observations can update the day state and support late-spike
research, but they must never be used to score a prediction made at an earlier
cutoff.

## Regime Ontology

The promoted design now separates causal physical regimes from ex-post timing
events.

- `regime_label` must be inferable from observations available before the CP.
- Full-day labels such as late Tmax timing may be used for evaluation only.
- `late_warming` is deprecated as a regime because `tmax_hour >= 18` is an
  outcome, not a causal weather state.
- Late Tmax must be modeled as a month/regime-relative risk target learned from
  train-only timing norms.

See ADR-011 and `docs/onda2r_regime_ontology_repair_plan.md`.

The current heuristic classifier is a quarantined baseline until ADR-012
decision records explicitly retain, adapt, or replace each relevant rule. It
must not be treated as final climatological truth merely because it exists in
code.

## Evidence-to-Decision Gate

Onda 2E EDA outputs are descriptive evidence. They become actionable only after
the ADR-012 decision register assigns one of the allowed statuses:
`SUPPORTED`, `REJECTED`, `ADAPTED`, `BLOCKED`,
`PROMOTED_TO_REGIME_DESIGN`, `PROMOTED_TO_FEATURE_CANDIDATE`, or
`QUARANTINED_BASELINE`.

No regime repair, feature candidate, model input, or Onda 4 rerun may use an
EDA finding without an artifact-backed decision record.

`tmax regime-design-validate` is an offline bridge from ADR-012 regime-design
evidence to Onda 4 repair work. It assigns candidate labels into a feature copy,
writes `reports/regime-design/`, and never mutates `data/features.parquet` or
the production regime classifier. Its default R2 run is a one-year candidate
screening window, explicitly recorded in `regime_candidate_validation_scope.csv`;
production promotion still requires a full Onda 4 pass with no dead regimes.

## Design Principles Applied

- **P1 (Causal Firewall):** Every feature at a checkpoint uses only observations
  with `ts_utc < cp_utc`. Violation is a RuntimeError.
- **P4 (Settlement Honesty):** Decimal internally, integer output. Commercial
  rounding (half-up). `risco_de_flip` quantifies boundary risk.
- **P5 (Versioned Artifacts):** All decision outputs are versioned, reproducible,
  and stored in JSON and/or Markdown.
- **P6 (Evidence Must Become Decisions):** EDA artifacts must feed explicit
  project decisions before changing regimes, features, models, or gates.
