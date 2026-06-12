# Onda 3F Pooled Temporal/Regime Design

## Status

Accepted for implementation on 2026-06-09 after the Onda 3E train-start
sensitivity result.

This is step 2 of the pre-Open-Meteo model sequence. It is an experiment-only
local-data model iteration, not an external forecast-data integration and not a
production promotion.

## Problem

Onda 3C and Onda 3D train independent CP surfaces inside each rolling test
year. That keeps checkpoint behavior explicit, but it also fragments the data
by CP and leaves month/season effects to be learned indirectly from sparse
yearly folds. The user hypothesis for step 2 is that pooling across CP and
season, while representing CP and seasonality continuously, may recover
statistical strength without adding fragile discrete Wellington regimes.

Onda 3E found that switching from the sparse 2009-start window to a 2012-start
window produced only a very small MAE gain and a small exact-bracket loss. That
result does not justify dropping either train start yet. For Onda 3F, the
canonical model will use the current Onda 3D/Onda 3E local-data surface and the
default full local history; train-start choice remains an audit item for step 4
nested validation.

## Goals

1. Build a pooled rolling model that trains one ridge challenger per test year,
   not one independent model per CP.
2. Add cyclic temporal features:
   - `cp_sin`, `cp_cos`
   - `month_sin`, `month_cos`
   - `doy_sin`, `doy_cos`
3. Reuse the binary-macro continuous interaction idea from Onda 3D:
   `foehn_score` and `cloud_cover_suppression` crossed with
   `binary_macro_regime_label`.
4. Allow categorical pooling features when present:
   `binary_macro_regime_label`, `regime_label`, `regime_score_argmax`, and
   `day_sequence_pattern`.
5. Produce exact-bracket summaries using the same half-up integer settlement
   rule used by the Onda 3 model-attempt review.
6. Write a separate report directory under `reports/onda3-pooled/`.

## Non-Goals

- Do not integrate Open-Meteo or any NWP source.
- Do not implement nested validation in this step; that remains step 4.
- Do not perform the final Onda 3D/Onda 3E/Onda 3F audit comparison here; that
  remains step 3.
- Do not create new production regime labels.
- Do not change `data/features.parquet`, `data/labels.parquet`, or existing
  Onda 3C/3D/3E artifacts.
- Do not claim production readiness, market execution, EV, deployment, or live
  trading readiness.

## Design

The new runner lives in `solarstorm.onda3._pooled_iteration`. It prepares the
input matrix by adding cyclic temporal columns and binary-macro interaction
columns, then runs an annual rolling split:

- for test year `Y`, train rows are `date_local.year < Y`;
- test rows are `date_local.year == Y`;
- later rows are holdout and are not used in that fold.

Unlike Onda 3C/Onda 3D, each fold fits a single ridge model across all CP rows.
The resulting model result rows use `cp = ALL`, while line-level predictions
retain the original CP so bracket summaries and CP slices can still be audited.

```text
features + labels + optional binary macro assignments
        |
        v
Onda 3 pooled matrix
        |
        +--> add cp/month/doy sin/cos
        +--> add continuous x binary macro interactions
        +--> one pooled annual ridge model per test year
        |
        v
reports/onda3-pooled/*
```

The CLI command is `onda3-pooled-model-iteration`.

## Artifacts

Output directory:

- `reports/onda3-pooled/`

CSV/Markdown artifacts:

- `onda3_pooled_feature_audit_v1.csv/.md`
- `onda3_pooled_model_results_v1.csv/.md`
- `onda3_pooled_predictions_v1.csv/.md`
- `onda3_pooled_bracket_overall_v1.csv/.md`
- `onda3_pooled_bracket_by_month_day_v1.csv/.md`
- `onda3_pooled_bracket_by_month_cp_v1.csv/.md`
- `onda3_pooled_regime_performance_v1.csv/.md`
- `onda3_pooled_regime_by_cp_v1.csv/.md`
- `onda3_pooled_slice_diagnostics_v1.csv/.md`
- `onda3_pooled_uncertainty_abstention_v1.csv/.md`
- `onda3_pooled_temporal_diagnostics_v1.csv/.md`
- `onda3_pooled_decision_update_v1.csv/.md`
- `onda3_pooled_model_report_v1.md`

Decision statuses:

- `READY_FOR_ONDA3_AUDIT_COMPARISON`
- `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`

All rows must include `production_status = EXPERIMENT_ONLY`.

## Acceptance Criteria

- The runner adds the expected cyclic temporal columns with bounded sine/cosine
  values.
- The model result table contains pooled `cp = ALL` rows by test year and does
  not train independent CP models.
- Predictions retain original CP values for bracket and slice diagnostics.
- Exact-bracket outputs include daily `any_cp_exact`, final `23:00` exact, and
  CP-specific exact rates.
- Regime summaries use `binary_macro_regime_label` when available.
- The CLI writes all planned artifacts under `reports/onda3-pooled/`.
- The final report states that Open-Meteo forecast data is not integrated.
- Focused tests, adjacent Onda 3 tests, and Ruff pass before the step is
  considered complete.

## Decision

Proceed with Onda 3F as the pooled temporal/regime experiment. The outcome will
feed step 3, the audit comparison against Onda 3D and Onda 3E. Onda 3F remains
`EXPERIMENT_ONLY` regardless of its metrics.
