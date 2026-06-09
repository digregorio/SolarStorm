# Onda 3 Baseline-First Model Design

## Status

Accepted for implementation planning on 2026-06-09.

Onda 3 design review is now eligible because the binary macro validation gate
records `READY_FOR_ONDA3_DESIGN_REVIEW` for the experiment-only
`macro_southerly_flow` versus `macro_non_southerly` surface. This is not
production approval. It is permission to design and run the first model/baseline
experiments under strict causal and comparison gates.

## Problem

The project has spent too long trying to repair hard regime ontologies before
building a measurable modeling baseline. The useful evidence is now clear:

- More than two hard macro regimes are not classifiable enough in the current
  morning METAR space.
- `macro_calm_radiative` is audit-only, not a production-blocking macro.
- The binary macro surface has no dead R2 macros, stable fold assignment, and
  predictive assignment separability, but `macro_non_southerly` has weak R2
  sensitivity.
- EDA produced high-value continuous signals such as `cloud_cover_suppression`
  and FOEHN/NW descriptors that should be model features or diagnostics, not
  more hard macro labels.

Onda 3 must therefore stop treating regime design as the model itself. Regimes
provide segmentation and interaction context. Predictive skill must come from a
baseline-first model harness that can beat the existing feature-null ladder,
report uncertainty, and show where it should abstain.

## Goals

1. Build the first Onda 3 experiment surface around train-only, causal
   baselines and challenger models.
2. Use the binary macro candidate as a segmentation/input candidate only, with
   `production_status = EXPERIMENT_ONLY`.
3. Carry EDA-derived continuous features into the model candidate set, especially
   cloud, FOEHN, wind, humidity, pressure, warming-rate, and timing-risk
   descriptors that are visible before the CP.
4. Evaluate every result against the best available null for each CP and slice.
5. Persist model, feature, metric, uncertainty, and abstention artifacts so the
   next iteration can improve weaknesses rather than restarting the regime
   debate.
6. Keep market execution, EV, position sizing, and production deployment out of
   scope.

## Non-Goals

- Do not promote the binary macro assignments to production.
- Do not overwrite `data/features.parquet`.
- Do not use full-day targets, `tmax_hour`, final Tmax, or remaining warming as
  live features.
- Do not add NWP/Open-Meteo ingestion in this first Onda 3 sprint.
- Do not re-enter v2.4 calm/radiative threshold tuning.
- Do not optimize trading outcomes, expected value, or market execution.

## Entry Evidence

Required preconditions already generated:

- `reports/regime-design/regime_binary_macro_validation_v1` surface:
  `regime_binary_macro_r2_validation_v1.csv`,
  `regime_binary_macro_classifiability_v1.csv`, and
  `regime_binary_macro_decision_update_v1.csv`.
- Decision status: `READY_FOR_ONDA3_DESIGN_REVIEW`.
- Candidate remains `EXPERIMENT_ONLY`.
- `macro_non_southerly` warning remains active: 3/92 R2 pass rows versus 47/92
  for `macro_southerly_flow`.
- Causal feature signal evidence:
  `cloud_cover_suppression` survives the CEXP-002B causal robustness screen.
- Existing baselines and feature-null gates remain the comparison floor.

## Architecture

Onda 3 is a model experiment layer, not a new regime ontology layer.

The first implementation should create a dedicated Onda 3 module namespace that
builds:

1. a train/test design matrix from existing causal feature and label artifacts;
2. a model feature manifest with provenance and leakage classification;
3. baseline and challenger model result tables;
4. metric and uncertainty reports by CP, month, binary macro, and lead-time
   bucket;
5. a decision artifact that either keeps the candidate in experiment review or
   promotes it to the next robustness rerun.

The minimum challenger family should be deliberately simple:

- train-mean/best-null baseline for each CP/slice;
- regularized linear model for remaining warming or integer Tmax residual;
- optional quantile/interval estimate from train-window residuals;
- abstention rule derived from validation uncertainty or low-confidence slices.

This gives the project a real baseline to beat before more complex models are
introduced.

## Data Flow

```text
data/features.parquet + data/labels.parquet
        |
        +--> causal feature matrix
        |
        +--> EDA feature manifest
        |
        +--> optional experiment-only binary macro assignments
                 |
                 v
        Onda 3 train-only design matrix
                 |
                 v
        baseline ladder + simple challengers
                 |
                 v
        metrics, uncertainty, abstention, slice diagnostics
                 |
                 v
        Onda 3 decision update
```

## Feature Policy

Allowed feature classes:

- pre-CP METAR aggregates already produced by the feature builder;
- EDA-derived causal descriptors computed only from observations visible before
  the CP;
- experiment-only binary macro labels and assignment confidence as candidate
  inputs or segmentation columns;
- train-only historical climatology and baseline summaries.

Blocked feature classes:

- final daily Tmax, full-day target columns, `remaining_warming`, and
  `tmax_hour` as live features;
- post-CP observations;
- market prices or settlement signals;
- labels from superseded regime threshold loops except as audit columns.

## Evaluation Gates

Onda 3 produces an experiment decision, not production deployment.

A candidate can move to the next robustness rerun only if:

- it beats the best train-only null on eligible CP slices;
- it does not concentrate skill only after Tmax is already known;
- it reports calibrated uncertainty or empirical interval coverage;
- it has an explicit abstention/stay-out behavior;
- no causal firewall violation is detected;
- segment diagnostics do not hide catastrophic failure in
  `macro_southerly_flow`, `macro_non_southerly`, month, CP, or lead-time slices.

Failure should create a weakness matrix, not another regime redesign loop.

## Artifacts

Planned Onda 3 artifacts:

- `reports/onda3/onda3_feature_manifest_v1.csv/.md`
- `reports/onda3/onda3_design_matrix_audit_v1.csv/.md`
- `reports/onda3/onda3_baseline_results_v1.csv/.md`
- `reports/onda3/onda3_challenger_results_v1.csv/.md`
- `reports/onda3/onda3_slice_diagnostics_v1.csv/.md`
- `reports/onda3/onda3_uncertainty_abstention_v1.csv/.md`
- `reports/onda3/onda3_decision_update_v1.csv/.md`

## Acceptance Criteria

- Onda 3 has a dedicated spec and implementation plan.
- Binary macro validation no longer fabricates AUC=1.0 for single-class splits.
- ADR-012 and roadmap state that Onda 3 design review is eligible, while
  production remains blocked.
- Planned Onda 3 outputs compare against existing baselines rather than only
  reporting absolute model performance.
- The plan includes tests for leakage blocking, artifact schemas, model metrics,
  uncertainty/abstention, and CLI generation.
- The milestone closes only after the Onda 3 baseline artifacts are generated,
  the verification suite passes, and the working tree is clean for the milestone
  with no stray temporary files.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Onda 3 becomes another regime-repair loop. | Treat regimes as segmentation/input candidates and emit weakness matrices. |
| A simple model underperforms and looks like failure. | Use it as the baseline floor for future model improvement. |
| Binary macro AUC is over-interpreted. | Document it as assignment separability, not Tmax predictive skill. |
| Continuous EDA features leak target information. | Require manifest leakage classification and train-only computation. |
| Project jumps to market execution after one promising result. | Keep Onda 3 experiment-only and require robustness rerun before production. |

## Decision

Proceed with Onda 3 as a baseline-first model experiment sprint. The first
implementation should build the comparison harness, feature manifest, simple
challenger, uncertainty/abstention diagnostics, and decision artifact before
introducing any complex model family.
