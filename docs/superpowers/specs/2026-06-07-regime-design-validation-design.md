# Regime Design Validation Design

Status: approved for implementation
Date: 2026-06-07

## Goal

Turn the Onda 2E regime-design queue into an assignable, auditable candidate
regime design and validate whether it removes the Onda 4 R2 blocker before any
Onda 3 model work resumes.

## Context

Onda 2E has resolved the active local thesis backlog. The remaining project
block is not missing EDA; it is validation of a data-backed regime repair.

`reports/onda2e/regime_design_candidate_v1.csv` proposes a k=6 month/season
design for `WCT-REGIME-016`. It is intentionally design evidence only. It has
candidate families, physical signatures, stability diagnostics, and caveats,
but it does not provide a reusable assignment layer for `date_local x cp` rows.

Onda 4 still evaluates regime robustness through `features["regime_label"]`.
The current `regime_label` is a quarantined baseline, so the candidate design
must be tested in a separate feature copy rather than silently replacing the
production feature artifact.

## Scope

This work will build an offline regime-candidate validation path:

- read Onda 2E candidate artifacts and the current feature/label/obs data;
- assign one candidate regime label per `date_local x cp` row using causal
  pre-CP inputs only;
- write candidate assignment, ontology, and leakage/power audit artifacts;
- run R2-style regime sensitivity against a feature copy that uses the
  candidate labels;
- report whether any candidate regime family is dead;
- write an ADR-012-compatible decision outcome for the candidate validation.

The work does not promote a production classifier, rewrite `data/features.parquet`,
train Onda 3 models, introduce external weather/NWP data, or bypass any Onda 4
gate.

## Architecture

Create a focused Onda 2E regime-design module that consumes the existing
candidate profiles and produces assignable labels. The assignment implementation
uses the same causal clustering input families already accepted by the full EDA
sprint: pre-CP wind, pressure, humidity, cloud/rain, dewpoint depression, and
temperature slope. Outcome columns such as `tmax_int`, `remaining_warming`,
`tmax_anomaly`, and `tmax_hour` remain audit-only.

Create a robustness validation adapter that takes a features DataFrame, replaces
only the in-memory `regime_label` with candidate labels, and calls the existing
`regime_sensitivity()` and `detect_dead_regimes()` path. This keeps Onda 4 logic
centralized while making the candidate test reproducible.

Expose the work through a CLI command so the generated artifacts are stable and
rerunnable:

```bash
uv run python -m solarstorm regime-design-validate \
  --features-path data/features.parquet \
  --labels-path data/labels.parquet \
  --obs-path data/obs.parquet \
  --candidate-path reports/onda2e/regime_design_candidate_v1.csv \
  --queue-path reports/onda2e/regime_design_queue.csv \
  --output-dir reports/regime-design
```

## Required Artifacts

- `reports/regime-design/regime_candidate_assignments_v1.csv`
- `reports/regime-design/regime_candidate_ontology_v1.csv`
- `reports/regime-design/regime_candidate_assignment_audit.csv`
- `reports/regime-design/regime_candidate_r2_validation.csv`
- `reports/regime-design/regime_candidate_validation_report.md`
- `reports/regime-design/regime_candidate_decision_update.csv`

## Assignment Policy

Candidate labels must be coarse, physically interpretable families rather than
96 month/cluster IDs. The first implementation should use these families:

- `candidate_southerly_disrupted`
- `candidate_nw_or_foehn`
- `candidate_maritime_cloudy`
- `candidate_mixed_transition`

Rows are assigned to the closest candidate centroid within their month when
month-specific candidates exist. If a month lacks candidate rows, assignment may
fall back to season-level centroids and must record that fallback in the audit.
Distance inputs must be standardized from candidate-profile statistics or from
the assignment population itself, and the standardization method must be written
to the audit artifact.

Every assignment row must include:

- `date_local`
- `cp`
- `candidate_regime_label`
- `candidate_regime_family`
- `source_candidate_id`
- `stratum_type`
- `stratum_value`
- `distance_to_candidate`
- `assignment_confidence`
- `causal_window`
- `production_status`

`production_status` is always `NOT_PRODUCTION` for this phase.

## Validation Policy

The validation path must answer one question first: does the candidate design
remove the Onda 4 R2 dead-regime blocker?

The R2 validation artifact must include one row per candidate regime family and
validated hypothesis/CP result. It must include enough information for
`detect_dead_regimes()` or an equivalent candidate-family detector to report dead
families.

The validation report must state:

- candidate family counts and smallest family support;
- whether the assignment used any season fallback;
- dead candidate families, if any;
- whether R2 would pass for the candidate family set;
- why this is or is not enough to start a full Onda 4 rerun.

If R2 candidate validation passes, the decision update may mark the candidate
as `PROMOTED_TO_ONDA4_CANDIDATE` only if that status is added to ADR-012 and the
decision schema. If no new status is added, the decision must stay
`PROMOTED_TO_REGIME_DESIGN` with a rationale that the next allowed action is a
full Onda 4 rerun. In either case, it is not a production classifier.

## Error Handling

The CLI must fail fast when:

- the candidate artifact is missing or lacks required columns;
- the queue does not contain `WCT-REGIME-016` as `PROMOTED_TO_REGIME_DESIGN`;
- feature rows cannot be joined to candidate assignment rows;
- a required causal input column is unavailable;
- assignment produces null candidate labels;
- validation cannot produce a regime cross-tab.

Failures should print a concise error and exit non-zero rather than writing
partial success reports.

## Testing

Tests must cover:

- candidate ontology construction from `regime_design_candidate_v1.csv`;
- assignment of feature rows to candidate families using only causal inputs;
- audit detection of missing/fallback/low-support assignment cases;
- R2 validation over a feature copy with candidate labels;
- CLI artifact writing;
- no mutation of source `data/features.parquet`;
- report wording that says candidate validation is not production promotion.

Use TDD: add failing tests first, confirm failure, implement the smallest code
that passes, then run the relevant Onda2e/robustness tests and the full
non-network suite.

## Non-Scope

- Onda 3 model training.
- Direct overwrite of `data/features.parquet`.
- Production deployment of a new regime classifier.
- Live/shadow trading, EV, sizing, or Polymarket integration.
- External station, ENSO/IOD, SST, NWP, or Open-Meteo data ingestion.
- Making Onda 4 pass by adding outcome labels or post-CP information.
