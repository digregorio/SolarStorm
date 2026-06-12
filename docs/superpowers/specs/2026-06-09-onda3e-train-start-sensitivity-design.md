# Onda 3E Train-Start Sensitivity Design

## Status

Accepted for implementation planning on 2026-06-09.

This is the first step in the next pre-Open-Meteo model sequence. It is an
experiment-only sensitivity test, not a production model and not an external
forecast-data integration.

## Problem

The current Onda 3D binary-macro interaction surface trains rolling folds from
the earliest available local feature rows. The local feature/label history is
very sparse before 2012:

- 2009 has 2 usable dates after 2009-04-23.
- 2010 has 37 usable dates.
- 2011 has 156 usable dates.
- 2012 has 360 usable dates.
- 2013 onward is effectively continuous in the Onda 3 feature/label surface.

The sparse 2009-2011 period adds only 195 unique training days to the fixed
2024 training window, but it can still affect ridge coefficients, category
priors, train means, and regime/feature interactions. Before changing regime
architecture or integrating Open-Meteo, the project needs to test whether
starting the model history at 2012-01-01 improves or degrades out-of-sample
performance.

## Goals

1. Re-run the Onda 3D binary-macro interaction model with two train-start
   variants:
   - `legacy_2009_start`: `train_start = 2009-04-23`
   - `continuous_2012_start`: `train_start = 2012-01-01`
2. Keep the same rolling test years as Onda 3D: 2023, 2024, and 2025.
3. Compare the variants by weighted MAE, exact integer bracket rate,
   `any_cp_exact`, final `23:00` exact rate, CP, month, and binary macro.
4. Preserve Onda 3D as the comparator surface and keep all outputs under a new
   experiment-only report directory.
5. Produce a decision artifact that records whether the 2012 start should be
   carried into the next pooled-model experiment.

## Non-Goals

- Do not integrate Open-Meteo or any NWP source.
- Do not introduce nested validation in this step; that is step 4 of the
  pre-Open-Meteo sequence.
- Do not implement the pooled month/CP cyclical model; that is step 2.
- Do not change `data/features.parquet`, `data/labels.parquet`, or the current
  production/quarantined regime classifier.
- Do not overwrite `reports/onda3-interactions/`.
- Do not claim production readiness, deployment, market execution, EV, or
  trading readiness.

## Design

Add an Onda 3E experiment runner that reuses the existing Onda 3D interaction
builder. The runner loads the same feature, label, and binary macro assignment
surface used by Onda 3D, builds the same matrix, then filters the matrix by the
selected `train_start` before running the interaction model.

```text
data/features.parquet
data/labels.parquet
reports/regime-design/regime_binary_macro_assignments_v1.csv
        |
        v
Onda 3 matrix with binary_macro_regime_label
        |
        +--> variant legacy_2009_start: date_local >= 2009-04-23
        |
        +--> variant continuous_2012_start: date_local >= 2012-01-01
        |
        v
existing Onda 3D interaction model runner
        |
        v
reports/onda3-train-start-sensitivity/*
```

The rolling fold semantics remain unchanged:

- for test year 2023, train rows are from `train_start` through 2022-12-31;
- for test year 2024, train rows are from `train_start` through 2023-12-31;
- for test year 2025, train rows are from `train_start` through 2024-12-31;
- rows after each test year are holdout rows and are not used in that fold.

The test windows are identical between variants. Only the historical training
start changes. This isolates whether the sparse 2009-2011 period helps or
hurts.

## Artifacts

Output directory:

- `reports/onda3-train-start-sensitivity/`

Planned CSV/Markdown artifacts:

- `onda3_train_start_scope_v1.csv/.md`
- `onda3_train_start_model_results_v1.csv/.md`
- `onda3_train_start_predictions_v1.csv/.md`
- `onda3_train_start_bracket_overall_v1.csv/.md`
- `onda3_train_start_bracket_by_month_day_v1.csv/.md`
- `onda3_train_start_bracket_by_month_cp_v1.csv/.md`
- `onda3_train_start_regime_performance_v1.csv/.md`
- `onda3_train_start_comparison_v1.csv/.md`
- `onda3_train_start_decision_update_v1.csv/.md`
- `onda3_train_start_sensitivity_report_v1.md`

Decision statuses:

- `CARRY_2012_START_TO_ONDA3F`
- `KEEP_2009_START_FOR_ONDA3F`
- `KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION`

All rows must include `production_status = EXPERIMENT_ONLY`.

## Acceptance Criteria

- A CLI command `onda3-train-start-sensitivity` writes the new report directory
  from local artifacts.
- The experiment emits both train-start variants and never overwrites existing
  Onda 3D artifacts.
- Scope rows show train periods, test periods, and row counts for every
  train-start variant and test year.
- Weighted MAE is reported for both variants.
- Exact bracket metrics use the same half-up settlement rule as Polymarket
  integer settlement.
- Bracket metrics include overall CP-specific rates, daily `any_cp_exact`, and
  final `23:00` exact rate.
- Regime summaries compare `macro_non_southerly` and `macro_southerly_flow`
  when binary assignments are available.
- The final report states explicitly that Open-Meteo is not integrated.
- Focused tests and Ruff pass before the step is considered complete.

## Decision

Proceed with Onda 3E as the first pre-Open-Meteo experiment. The experiment
answers one narrow question: whether the sparse 2009-2011 period should remain
in the local-data training window. The next steps, pooled temporal/regime
modeling and nested validation, depend on this result.
