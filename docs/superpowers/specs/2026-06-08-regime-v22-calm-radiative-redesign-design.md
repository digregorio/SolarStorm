# Regime v2.2 Calm/Radiative Redesign Design

## Goal

Implement Regime Ontology v2.2 as a non-production redesign candidate that
restores `macro_calm_radiative` as a protected physical macro before any Onda 3
work resumes.

## Context

v2.1 solved the v2 residual dead-macro problem by absorbing
`macro_light_marine_or_residual` into `macro_nw_continuum` and
`macro_southerly_flow`. Corrected Onda C then kept v2.1 in regime-design
review because the two-macro surface was weakly classifiable over the audited
physical meteorological basis.

The old residual macro must not be revived as a production-eligible regime.
The v2.2 change is a physical overlay on v2.1, not a label rollback.

## Design

Create a dedicated v2.2 artifact builder that consumes:

- `reports/regime-design/regime_candidate_assignments_v2_1.csv`
- the physical Onda 2E cluster matrix rebuilt from `data/features.parquet`,
  `data/labels.parquet`, and `data/obs.parquet`

The builder reassigns rows to `macro_calm_radiative` only when all conditions
below are met:

- wind speed is in the lower quartile of the physical matrix;
- at least two of these four supporting physical signals are true:
  high relative humidity, low dewpoint depression, high cloud-cover score, or
  weak/non-positive pre-CP temperature slope.

The thresholds are quantile-derived from the audited physical feature basis.
No outcome columns, Tmax labels, post-CP data, or model features may enter the
v2.2 rule.

## Protected Macros

v2.2 protected macros are:

- `macro_nw_continuum`
- `macro_southerly_flow`
- `macro_calm_radiative`

`macro_light_marine_or_residual` remains an audit surface only and must not be
restored as a protected macro.

## Artifacts

The sprint writes these experiment-only artifacts:

- `reports/regime-design/regime_candidate_assignments_v2_2.csv`
- `reports/regime-design/regime_candidate_ontology_v2_2.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.md`
- `reports/regime-design/regime_candidate_r2_validation_v2_2.csv`
- `reports/regime-design/regime_candidate_v21_v22_comparison.csv`
- `reports/regime-design/regime_candidate_v22_validation_report.md`

All assignment rows remain `production_status = NOT_PRODUCTION`. Comparison,
audit, and Onda C rows remain `production_status = EXPERIMENT_ONLY`.

## Validation

The sprint must:

1. run R2 candidate validation for v2.2;
2. compare v2.1 against v2.2 with all three protected macros;
3. run corrected physical Onda C against the v2.2 candidate under review;
4. update ADR-012, ROADMAP, and regime docs with the observed v2.2 result.

Passing R2 or Onda C does not promote production. The only allowed downstream
status after this sprint is still design review unless Onda C explicitly
returns `READY_FOR_ONDA3_DESIGN_REVIEW`.
