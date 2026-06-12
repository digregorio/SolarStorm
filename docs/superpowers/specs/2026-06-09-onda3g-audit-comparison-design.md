# Onda 3G Audit Comparison Design

## Status

Accepted for implementation on 2026-06-09 as step 3 of the pre-Open-Meteo
model sequence.

This is an audit-only comparison of persisted local-data artifacts. It does not
train a new model, does not integrate Open-Meteo/NWP data, and does not promote
any model to production.

## Problem

Onda 3D established the current binary-macro interaction surface. Onda 3E showed
that the 2012 train-start window gives only a tiny MAE gain and a small
exact-bracket loss. Onda 3F then improved MAE materially with a pooled
temporal/regime model, but lost daily `any_cp_exact` while improving the final
`23:00` exact rate.

Before nested validation or Open-Meteo integration, these surfaces need one
auditable comparison table using consistent metrics, consistent bracket rules,
and the same binary-macro and continuous-feature slices.

## Goals

1. Compare Onda 3D, Onda 3E legacy, Onda 3E continuous-2012, and Onda 3F.
2. Recompute exact-bracket metrics from line-level predictions using the same
   half-up integer settlement rule.
3. Compare models overall, by test year, by month, by month x CP, by binary
   macro regime, and by selected feature audit slices.
4. Include audit slices for:
   - `calm_radiative` when present in `regime_label`;
   - top-quartile `foehn_score`;
   - top-quartile `cloud_cover_suppression`;
   - the same top-quartile slices inside `macro_non_southerly`.
5. Produce a decision artifact for step 4 nested validation.

## Non-Goals

- Do not train, tune, refit, or alter any Onda 3D/3E/3F model.
- Do not integrate Open-Meteo/NWP forecast data.
- Do not implement nested validation in this step.
- Do not create new production regime labels.
- Do not claim production readiness, EV, market pricing, deployment, or live
  trading readiness.

## Design

The new module is `solarstorm.onda3._audit_comparison`. It reads persisted
prediction artifacts from:

- `reports/onda3-interactions/onda3_interaction_predictions_v1.csv`
- `reports/onda3-train-start-sensitivity/onda3_train_start_predictions_v1.csv`
- `reports/onda3-pooled/onda3_pooled_predictions_v1.csv`

Onda 3D predictions are enriched with brackets and binary macro assignments.
Onda 3E and Onda 3F predictions are normalized into a common schema. The builder
then recomputes all audit summaries from line-level predictions so the
comparison is not dependent on earlier aggregate CSVs.

Canonical model IDs:

- `onda3_d_binary_macro_interactions`
- `onda3_e_legacy_2009_start`
- `onda3_e_continuous_2012_start`
- `onda3_f_pooled_temporal_regime`

Decision logic:

- If Onda 3F has materially lower MAE than Onda 3D but gives back daily
  `any_cp_exact`, carry both Onda 3D and Onda 3F into nested validation.
- If Onda 3F improves MAE and both exact-bracket headline rates, carry Onda 3F
  as the primary nested-validation candidate.
- Otherwise keep Onda 3D as the reference and keep Onda 3F under experiment
  review.

All outcomes remain `EXPERIMENT_ONLY`.

## Artifacts

Output directory:

- `reports/onda3-audit-comparison/`

CSV/Markdown artifacts:

- `onda3_audit_model_summary_v1.csv/.md`
- `onda3_audit_pairwise_delta_v1.csv/.md`
- `onda3_audit_by_year_v1.csv/.md`
- `onda3_audit_by_month_v1.csv/.md`
- `onda3_audit_by_month_cp_v1.csv/.md`
- `onda3_audit_regime_performance_v1.csv/.md`
- `onda3_audit_regime_winner_v1.csv/.md`
- `onda3_audit_feature_slice_v1.csv/.md`
- `onda3_audit_decision_update_v1.csv/.md`
- `onda3_audit_comparison_report_v1.md`

Decision statuses:

- `CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION`
- `CARRY_ONDA3F_TO_NESTED_VALIDATION`
- `KEEP_ONDA3D_REFERENCE_AND_REVIEW_ONDA3F`

## Acceptance Criteria

- Summary rows include all four canonical model IDs.
- Onda 3F is compared against Onda 3D with MAE, `any_cp_exact_pct`,
  `cp23_exact_pct`, and CP-specific exact deltas.
- Month, CP, binary macro, and feature-slice summaries keep original CP values.
- Feature slices are built from local `data/features.parquet` only.
- The report states that Open-Meteo forecast data is not integrated.
- Every non-empty artifact includes `production_status = EXPERIMENT_ONLY`.
- Focused tests, adjacent Onda 3 tests, and Ruff pass before completion.

## Decision

Proceed with Onda 3G as the audit comparison that feeds step 4 nested
validation. No model is production-ready after this step.
