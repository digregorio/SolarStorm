# Regime Deadlock Pivot Design

## Status

Accepted for implementation planning on 2026-06-08.

This spec follows `reports/onda2e/regime_deadlock_diagnosis_v1.md` and
supersedes the current active attempt to unlock Onda 3 through additional
`calm_radiative` threshold, restoration, or CEXP calibration loops.

## Problem

The project is blocked because the regime line keeps treating
`macro_calm_radiative` as a production-blocking macro. The evidence generated
by v2.0, v2.1, v2.2, v2.3, Onda C, and CEXP diagnostics now points to a
structural information limit rather than a missing threshold tweak:

- `train_only_gmm` stability is 0.0799 and classifiability is 0.0933, which is
  evidence that the morning METAR feature space does not contain stable
  three-plus macro cluster structure.
- `distance_softmax_v22` has 0.8226 low-confidence share, so most hard labels
  are algorithmic assignments in ambiguous feature space rather than high-trust
  states.
- `macro_calm_radiative` has low walk-forward cell power and repeatedly fails
  R2 as a macro, even though the audit signal `cloud_cover_suppression`
  survives causal robustness screening.
- The current loop produces more artifacts but does not change the blocker:
  calm/radiative fails, Onda C blocks, and Onda 3 remains stalled.

The old path is therefore no longer the active route for project progression.
It remains preserved as audit history only.

## Goals

1. Record a formal pivot decision that makes the deadlock diagnosis actionable.
2. Demote `macro_calm_radiative` from production-blocking macro to audit
   subtype/segment, while still reporting it explicitly.
3. Create an experiment-only binary macro candidate:
   `macro_southerly_flow` versus `macro_non_southerly`.
4. Test `cloud_cover_suppression` as a baseline feature independent of regime
   resolution.
5. Update ADR-012 and project docs so future work cannot silently re-enter the
   failed threshold loop.
6. Keep every new output experiment-only until Onda 4 and model evaluation
   prove predictive value.

## Non-Goals

- Do not create a v2.4 threshold-tuning attempt for calm/radiative.
- Do not weaken R2 globally.
- Do not promote any new production classifier, feature, or model.
- Do not overwrite `data/features.parquet`.
- Do not define live labels from full-day targets, Tmax hour, remaining
  warming, or other post-CP outcomes.
- Do not split calm/radiative into cloudy/clear macros as the active path.

## New Active Path

### Step 1: Pivot Decision Surface

Create a decision artifact that names the deadlock and marks the prior path as
superseded for unlock purposes.

Outputs:

- `reports/regime-design/regime_deadlock_pivot_decision_v1.csv`
- `reports/regime-design/regime_deadlock_pivot_decision_v1.md`
- `reports/regime-design/regime_deadlock_superseded_path_v1.csv`

The decision artifact must include:

- source report path;
- key evidence metrics;
- active path;
- superseded path;
- allowed next action;
- blocked next action;
- production status.

The superseded-path artifact must list v2.2/v2.3/CEXP threshold-restoration
items as audit history, not as active blockers.

### Step 2: Option C Audit Demotion

Create a gate semantics artifact that separates production-blocking macros from
audit-only segments.

Production-blocking macros:

- `macro_nw_continuum`
- `macro_southerly_flow`

Audit-only segment:

- `macro_calm_radiative`

Outputs:

- `reports/regime-design/regime_audit_demotions_v1.csv`
- `reports/regime-design/regime_audit_demotions_v1.md`

Rules:

- A dead production-blocking macro still blocks.
- `macro_calm_radiative` must be reported with support, R2 pass count, power
  warnings, and known cloud signal evidence.
- `macro_calm_radiative` no longer blocks Onda C solely because its R2 rows are
  zero under the current underpowered macro gate.
- The report must state that demotion is not deletion.

### Step 3: Option A Binary Macro Candidate

Create an experiment-only binary macro assignment candidate:

- `macro_southerly_flow`
- `macro_non_southerly`

`macro_non_southerly` absorbs NW, foehn-like, calm/radiative, light marine, and
transition-like cases. Foehn, cloud cover, wind speed, humidity, and pressure
signals remain available as continuous features or audit columns; they do not
become separate production macros in this sprint.

Outputs:

- `reports/regime-design/regime_binary_macro_candidate_v1.csv`
- `reports/regime-design/regime_binary_macro_candidate_v1.md`
- `reports/regime-design/regime_binary_macro_assignments_v1.csv`
- `reports/regime-design/regime_binary_macro_assignment_audit_v1.csv`

Rules:

- Use only pre-CP features or existing non-production assignment artifacts.
- Keep `production_status = EXPERIMENT_ONLY` or `NOT_PRODUCTION` as appropriate.
- Do not mutate current feature parquet files.
- Run R2 screening only on the two binary macros.

### Step 4: Cloud Cover Baseline Experiment

Test `cloud_cover_suppression` as an experiment-only baseline feature
independent of unresolved regime labels.

Outputs:

- `reports/regime-design/cloud_cover_baseline_experiment_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.md`

The experiment compares a simple cloud-adjusted candidate against existing
baseline levels by CP and month. It must be train-window calibrated and
walk-forward evaluated. The experiment result can recommend future baseline
work, but it cannot promote a production feature in this sprint.

### Step 5: Documentation and ADR-012

Update:

- `docs/decisions/012-evidence-to-decision-gate.md`
- `docs/regime_model_card.md`
- `docs/onda4_robustness_plan.md`
- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`

The docs must say:

- The active unlock path is deadlock pivot, not v2.4 threshold tuning.
- `macro_calm_radiative` is audit-only until future evidence proves otherwise.
- Onda 3 is not promoted by this documentation alone.
- Cloud-cover baseline work proceeds because it is independent of regime
  resolution and has causal-screen evidence.

## Data Flow

```text
regime_deadlock_diagnosis_v1.md
        |
        v
pivot decision + superseded path artifacts
        |
        +--> audit demotion artifact
        |        |
        |        v
        |   production macro gate semantics
        |
        +--> binary macro candidate artifacts
        |        |
        |        v
        |   experiment-only R2/classifiability review
        |
        +--> cloud-cover baseline experiment
                 |
                 v
          baseline comparison evidence
```

## Acceptance Criteria

- New pivot artifacts are generated and include the deadlock evidence metrics.
- `macro_calm_radiative` appears in audit outputs but not in
  production-blocking macro lists.
- Binary macro outputs contain exactly the two active labels:
  `macro_southerly_flow` and `macro_non_southerly`.
- Cloud-cover baseline outputs compare against at least one existing baseline
  and report rows by CP/month where possible.
- ADR-012 records the pivot and prevents future threshold loops from being
  treated as the active path.
- Focused tests, relevant regime tests, non-network tests, and Ruff pass before
  the implementation is declared complete.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Demotion hides calm/radiative failures. | Keep explicit audit reports and power warnings. |
| Binary macro loses physical nuance. | Keep subtype/continuous signals as audit/features, not hard macros. |
| Cloud baseline becomes another proxy shortcut. | Keep train-only calibration and no post-CP target-derived features. |
| Project re-enters v2.4 threshold loop. | Record superseded path and update ADR-012. |
| Onda 3 is promoted too early. | Mark all artifacts experiment-only and require Onda 4/model evidence. |

## Decision

Proceed with Option C immediately, Option A experimentally, and the
cloud-cover baseline experiment in the same implementation sprint. The prior
calm/radiative threshold/classifier restoration loop is superseded as the active
unlock path.
