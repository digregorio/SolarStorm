# Onda 3B Next Model Iteration Design

## Status

Accepted for implementation planning on 2026-06-09.

Onda 4M reviewed the first Onda 3 baseline model and records
`READY_FOR_ONDA3_NEXT_MODEL_ITERATION`, with all gates M1-M8 passing and
`production_status = EXPERIMENT_ONLY`. The next allowed action is another
experimental Onda 3 model iteration, not production deployment.

## Problem

The first Onda 3 model proved that a simple ridge challenger can beat the
train-mean null in aggregate. It did not yet produce a more useful model surface
for repeated iteration because:

- model results are pooled as `cp = ALL`;
- categorical context such as `binary_macro_regime_label` is used for
  diagnostics but not encoded as a model input;
- slice diagnostics report target means rather than model errors;
- Onda 4M could only review a single aggregate model result.

The next Onda 3 iteration should improve the experimental surface without
changing scope. It should remain baseline-first, causal, auditable, and small.

## Goals

1. Train and evaluate the simple ridge challenger separately by CP.
2. Add train-only one-hot encoding for experiment-only categorical context,
   especially `binary_macro_regime_label`.
3. Emit per-CP null and challenger metrics, prediction rows, slice error
   diagnostics, uncertainty/abstention rows, and a decision update.
4. Keep all outputs under `reports/onda3-next/` with
   `production_status = EXPERIMENT_ONLY`.
5. Preserve Onda 3 feature manifest blocking for full-day targets and proxies.
6. Update documentation to show that Onda 3B is the active next model iteration
   after Onda 4M.

## Non-Goals

- Do not introduce NWP/Open-Meteo or new external data.
- Do not add market pricing, EV, trading, shadow decisions, or deployment.
- Do not replace the production regime classifier.
- Do not promote binary macro labels beyond experiment-only context.
- Do not overwrite `reports/onda3/`; write a separate `reports/onda3-next/`
  surface.

## Design

Add a focused next-iteration module under `solarstorm/onda3/`:

```text
data/features.parquet + data/labels.parquet
        |
        v
existing Onda 3 feature manifest + design matrix
        |
        v
Onda 3B CP-specific ridge runner
        |
        +--> train-mean null by CP
        +--> ridge challenger by CP
        +--> train-only categorical one-hot encoding
        +--> prediction rows
        +--> slice error diagnostics
        +--> uncertainty and abstention rows
        |
        v
reports/onda3-next/*
```

The runner should use the same NumPy ridge approach already used in Onda 3.
Categorical encodings must learn categories from the train fold only. Unknown
test categories should encode as all-zero indicator columns for that feature.

## Artifacts

Planned outputs:

- `reports/onda3-next/onda3_next_feature_manifest_v1.csv/.md`
- `reports/onda3-next/onda3_next_model_results_v1.csv/.md`
- `reports/onda3-next/onda3_next_predictions_v1.csv/.md`
- `reports/onda3-next/onda3_next_slice_diagnostics_v1.csv/.md`
- `reports/onda3-next/onda3_next_uncertainty_abstention_v1.csv/.md`
- `reports/onda3-next/onda3_next_decision_update_v1.csv/.md`
- `reports/onda3-next/onda3_next_model_report_v1.md`

Decision statuses:

- `READY_FOR_ONDA4_MODEL_RERUN`
- `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`

## Acceptance Criteria

- Onda 3B has a dedicated spec and implementation plan.
- The CLI `onda3-next-model-iteration` writes `reports/onda3-next/`.
- Results include one null row and one challenger row for each tested CP.
- Prediction rows include `date_local`, `cp`, `actual`, `prediction`,
  `absolute_error`, and `model_name`.
- Slice diagnostics report model MAE by CP and binary macro when available.
- Uncertainty rows have finite residual p50/p90 by CP and an abstention rule.
- The decision remains experiment-only and does not claim production readiness.
- Stable tests and Ruff pass; milestone closes with a clean tree.

## Decision

Proceed with Onda 3B as a CP-specific, categorical-aware next model iteration.
It should produce a richer experimental model surface for the next Onda 4M
review while keeping production, deployment, and market execution blocked.
