# Onda 3H Nested Validation Design

## Status

Accepted for implementation on 2026-06-09 as step 4 of the pre-Open-Meteo
model sequence.

This step is a local-data model-selection gate. It does not integrate
Open-Meteo/NWP forecast data, does not promote a model to production, and does
not make deployment, market, EV, or execution claims.

## Problem

Onda 3G found a real tradeoff: Onda 3F pooled temporal/regime improves MAE and
the final `23:00` exact-bracket rate versus Onda 3D, but gives back daily
`any_cp_exact`. Testing feature design decisions directly on the same years used
for headline reporting is fragile. The next gate needs a distinct validation
year for model selection before looking at the test year.

The user also raised a valid concern about leaving too many years out. Onda 3H
therefore uses a two-stage fold:

- validation fit: train from `2012-01-01` through `Y-2`, validate on `Y-1`;
- test fit: after the candidate design is chosen by validation, refit using
  history from `2012-01-01` through `Y-1`, then test on `Y`.

This keeps the test year clean while avoiding unnecessary loss of the latest
validated training year.

## Goals

1. Compare Onda 3D and Onda 3F under identical nested walk-forward folds.
2. Default to test years `2023,2024,2025`, with validation years
   `2022,2023,2024`.
3. Start the historical training window at `2012-01-01`.
4. Select the candidate winner per outer fold by validation MAE, with exact
   bracket metrics reported as guardrails.
5. Evaluate the validation-selected candidate on the test year after refitting
   through `Y-1`.
6. Export fold scope, validation/test metrics, selection rows, regime/month/CP
   diagnostics, and a decision artifact.
7. Require binary macro assignments for the Onda 3D candidate and use an
   explicit Onda 3H feature allowlist so quarantined regime/timing features do
   not enter the nested gate by accident.

## Non-Goals

- Do not integrate Open-Meteo/NWP forecast features.
- Do not add new regime labels or change the regime ontology.
- Do not tune hyperparameters or search model families beyond the two carried
  candidates from Onda 3G.
- Do not include the sparse 2009-2011 historical window in the default gate.
- Do not claim production readiness.

## Design

Add `solarstorm.onda3._nested_validation`.

Candidate definitions:

- `onda3_d_binary_macro_interactions`: Onda 3D, using the existing
  binary-macro interaction builder and CP-specific ridge surface.
- `onda3_f_pooled_temporal_regime`: Onda 3F, using the existing pooled
  temporal/regime builder with cyclic CP/month/day-of-year features.

For each outer test year `Y`:

1. Build a validation candidate run with data from `2012-01-01` through
   December 31 of `Y-1`; the internal test year is `Y-1`, so the train years are
   `2012..Y-2`.
2. Pick the validation winner by lowest validation MAE. If MAE ties within
   `0.001`, prefer higher `cp23_exact_pct`; if still tied, prefer Onda 3D as the
   conservative reference. Missing `cp23_exact_pct` values sort behind available
   `23:00` metrics.
3. Build a test candidate run with data from `2012-01-01` through December 31
   of `Y`; the internal test year is `Y`, so the train years are `2012..Y-1`.
4. Record both candidates' test metrics and mark which candidate was selected
   by validation for that outer fold.

The builder recomputes exact brackets from line predictions using the half-up
`floor(value + 0.5)` rule already used by Onda 3G. Every non-empty output has
`production_status = EXPERIMENT_ONLY`.

The CLI validates that `regime_binary_macro_assignments_v1.csv` exists, is
non-empty, has `date_local`, `cp`, and `binary_macro_regime_label`, and covers
all feature rows before the build starts.

## Artifacts

Output directory:

- `reports/onda3-nested-validation/`

CSV/Markdown artifacts:

- `onda3_nested_fold_scope_v1.csv/.md`
- `onda3_nested_model_results_v1.csv/.md`
- `onda3_nested_predictions_v1.csv/.md`
- `onda3_nested_metric_summary_v1.csv/.md`
- `onda3_nested_selection_v1.csv/.md`
- `onda3_nested_test_selected_summary_v1.csv/.md`
- `onda3_nested_by_month_v1.csv/.md`
- `onda3_nested_by_month_cp_v1.csv/.md`
- `onda3_nested_regime_performance_v1.csv/.md`
- `onda3_nested_decision_update_v1.csv/.md`
- `onda3_nested_validation_report_v1.md`

Decision statuses:

- `PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS`
- `KEEP_ONDA3D_REFERENCE_AFTER_NESTED_VALIDATION`
- `KEEP_BOTH_CANDIDATES_AFTER_NESTED_VALIDATION`

## Acceptance Criteria

- Onda 3H includes both Onda 3D and Onda 3F in every valid fold.
- Validation rows use train years ending at `Y-2`.
- Test rows use train years ending at `Y-1`.
- Selection rows show the validation winner and that winner's test MAE for each
  outer year.
- Month, month x CP, and binary macro regime diagnostics are generated from
  line-level predictions.
- `cp23` summaries expose `n_days_with_cp23` and `cp23_exact_days`.
- Quarantined regime/timing columns such as `regime_label`,
  `regime_score_argmax`, `tmax_hour_by_regime_month`, `late_warming_anomaly`,
  and `intraday_regime_change` are not selected by the Onda 3H CLI.
- The report states that Open-Meteo forecast data is not integrated.
- Every non-empty artifact includes `production_status = EXPERIMENT_ONLY`.
- Focused tests, adjacent Onda 3 tests, and Ruff pass before completion.

## Decision

Proceed with Onda 3H as the nested validation gate before any Open-Meteo/NWP
integration. The expected output is a decision about the evaluation harness and
candidate carry-forward, not a production promotion.
