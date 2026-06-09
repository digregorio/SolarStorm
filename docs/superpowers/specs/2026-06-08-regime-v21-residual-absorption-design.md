# Regime v2.1 Residual Absorption Design

Status: approved for implementation planning
Date: 2026-06-08

## Goal

Remove the remaining dead macro-regime blocker from Regime Ontology v2 by
treating `macro_light_marine_or_residual` as an audit/uncertainty surface, not
as a production-eligible macro regime. The output is a non-production v2.1
screening experiment that reassigns residual assignments to the nearest
physical macro while preserving the residual evidence for diagnostics.

## Current Evidence

Regime Ontology v2 generated a formal candidate, but the gate still blocks:

- `macro_nw_continuum`: R2 PASS.
- `macro_southerly_flow`: R2 PASS.
- `macro_light_marine_or_residual`: R2 DEAD with 0/92 passing R2 rows.

The dead macro has only 351 assignment rows out of 21,824. It is also highly
uncertain:

- 329/351 assignments are `low_confidence_flag = true`.
- Mean component entropy is 1.45.
- Mean component margin is 0.238.
- Nearest alternatives are `macro_nw_continuum` for 241 rows and
  `macro_southerly_flow` for 110 rows.

The assignments are concentrated in five monthly centroids:

| Source candidate | Subtype | Assignment rows |
|---|---:|---:|
| `RDC-V1-MONTH-4-C05` | `subtype_transition_low_confidence` | 92 |
| `RDC-V1-MONTH-12-C02` | `subtype_transition_low_confidence` | 83 |
| `RDC-V1-MONTH-8-C00` | `subtype_transition_low_confidence` | 80 |
| `RDC-V1-MONTH-5-C03` | `subtype_transition_low_confidence` | 65 |
| `RDC-V1-MONTH-2-C02` | `subtype_maritime_cloudy` | 31 |

The residual macro therefore aggregates rare boundary states, not a stable
third macro regime. Keeping it as a macro repeats the v1 failure in a smaller
form.

## Design Decision

Implement `Regime Ontology v2.1` as a residual-absorption screening experiment:

1. Keep `macro_nw_continuum` and `macro_southerly_flow` as the only
   meteorological macros evaluated by R2.
2. Remove `macro_light_marine_or_residual` from the R2 macro surface.
3. Reassign each residual row to `nearest_alternative_macro`.
4. Preserve original residual information in audit columns:
   `original_macro_regime_label`, `original_subtype_label`,
   `absorbed_from_residual`, `residual_absorption_reason`,
   `nearest_alternative_macro`, `component_entropy`, `component_margin`, and
   `low_confidence_flag`.
5. Preserve subtype evidence as diagnostics, not as macro truth.

This is not a production classifier. It is a stricter test of whether the two
robust physical macro families can carry the full candidate assignment surface
without dead R2 macros.

## Onda C Follow-Up

Onda C is a planned follow-up after v2.1. It must not be lost in the flow.

Onda C will be a probabilistic classifiability and topology wave. It should
compare distance-softmax v2/v2.1 against more scientific regime-discovery
methods:

- Michelangeli-style classifiability or surrogate stability checks.
- Train-only GMM with BIC/AIC and membership probabilities.
- SOM or topology-preserving weather-state maps for transition structure.
- Seasonal/monthly sensitivity rather than one global flat ontology.

Onda C may recommend a replacement backend for the assignment probabilities,
but it must preserve the v2/v2.1 artifact contracts: macro label, subtype or
component label, family probabilities, entropy, margin, confidence, causal
window, and production status. Onda C must also remain non-production until it
passes ADR-012 and Onda 4.

## Scope

The v2.1 sprint builds:

- residual absorption diagnostics;
- v2.1 assignment artifacts derived from v2 assignments;
- v2.1 R2 validation;
- v2-v2.1 comparison artifacts;
- foundation experiment result consumption of the v2.1 comparison;
- ADR-012, ROADMAP, and model-card updates with the observed result.

## Non-Scope

- No Onda 3 model training.
- No production classifier promotion.
- No overwrite of `data/features.parquet`.
- No external data ingestion.
- No relaxation of Onda 4 gates.
- No promotion of `mixed_or_transition`, `maritime_cloudy`, `late_warming`, or
  intraday state-change labels as macro regimes.
- No GMM/SOM/Michelangeli implementation in this sprint; those belong to Onda C.

## Required Artifacts

The sprint must generate:

- `reports/regime-design/regime_residual_absorption_diagnostics_v1.csv`
- `reports/regime-design/regime_residual_absorption_diagnostics_v1.md`
- `reports/regime-design/regime_candidate_assignments_v2_1.csv`
- `reports/regime-design/regime_candidate_ontology_v2_1.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2_1.csv`
- `reports/regime-design/regime_candidate_v2_v21_comparison.csv`
- `reports/regime-design/regime_candidate_v21_validation_report.md`

Every v2.1 assignment and ontology row must keep
`production_status = NOT_PRODUCTION`. Every comparison or foundation-result row
must keep `production_status = EXPERIMENT_ONLY`.

## v2.1 Assignment Contract

`regime_candidate_assignments_v2_1.csv` must include all v2 assignment columns
plus:

| Column | Meaning |
|---|---|
| `candidate_version` | Always `v2.1`. |
| `original_macro_regime_label` | Macro label before absorption. |
| `original_subtype_label` | Subtype label before absorption. |
| `absorbed_from_residual` | True when the original macro was `macro_light_marine_or_residual`. |
| `residual_absorption_reason` | Short deterministic reason for the reassignment. |

For rows not absorbed from the residual macro, original and current labels are
the same and `absorbed_from_residual = false`.

For residual rows, the new `macro_regime_label` and `candidate_regime_label`
must equal `nearest_alternative_macro`. If `nearest_alternative_macro` is empty
or not one of the protected physical macros, the row must remain audit-only and
the builder must record a failing diagnostic rather than silently inventing a
macro.

## Diagnostics Contract

`regime_residual_absorption_diagnostics_v1.csv` must include:

| Column | Meaning |
|---|---|
| `diagnostic_item` | Stable diagnostic key. |
| `status` | `PASS`, `WARN`, or `FAIL`. |
| `detail` | Human-readable detail. |
| `n_rows` | Count relevant to the diagnostic. |
| `production_status` | Always `EXPERIMENT_ONLY`. |

Required diagnostics:

- residual row count;
- residual low-confidence share;
- residual nearest-alternative distribution;
- invalid nearest-alternative count;
- absorbed row count;
- v2.1 macro count;
- production-status guardrail.

## v2-v2.1 Comparison Contract

`regime_candidate_v2_v21_comparison.csv` must include:

| Column | Meaning |
|---|---|
| `candidate_version` | Always `v2.1`. |
| `macro_regime_label` | v2.1 macro label. |
| `assignment_rows` | v2.1 assignment support. |
| `absorbed_residual_rows` | Residual rows absorbed into this macro. |
| `r2_rows` | R2 rows for the macro. |
| `r2_pass_rows` | Passing R2 rows for the macro. |
| `r2_dead_status` | `PASS` or `DEAD`. |
| `v2_dead_regimes` | Dead macro count before absorption. |
| `v21_dead_regimes` | Dead macro count after absorption. |
| `protected_regression_flag` | True if a protected physical macro becomes dead. |
| `decision_update` | `READY_FOR_FULL_ONDA4_RERUN` or `KEEP_IN_REGIME_DESIGN_REVIEW`. |
| `production_status` | Always `EXPERIMENT_ONLY`. |

The decision is `READY_FOR_FULL_ONDA4_RERUN` only when:

- there are zero v2.1 dead macros;
- neither `macro_nw_continuum` nor `macro_southerly_flow` regresses to dead;
- no row has an invalid residual absorption target;
- all artifacts preserve non-production status.

Even then, the only allowed next action is a full Onda 4 rerun. Onda 3 remains
blocked until that full rerun passes.

## CLI

Add a CLI command:

```powershell
uv run python -m solarstorm regime-design-v21-validate `
  --features-path data/features.parquet `
  --labels-path data/labels.parquet `
  --assignments-v2-path reports/regime-design/regime_candidate_assignments_v2.csv `
  --r2-v2-path reports/regime-design/regime_candidate_r2_validation_v2.csv `
  --output-dir reports/regime-design
```

The command must:

1. read v2 assignments;
2. build v2.1 assignments and diagnostics;
3. run R2 on v2.1 assignments;
4. compare v2 versus v2.1;
5. write all required artifacts;
6. print assignment count, absorbed row count, dead macro count, and report path.

The command must not mutate the source feature parquet.

## Testing

Required tests:

- residual rows are reassigned to nearest physical macro;
- non-residual rows keep their labels;
- invalid nearest alternative is diagnosed and prevents a ready decision;
- v2.1 comparison reports zero dead macros only when R2 actually passes;
- writer emits all v2.1 artifacts with correct filenames;
- CLI writes artifacts and does not mutate `features.parquet`;
- foundation experiment results can consume the v2.1 comparison;
- docs mention Onda C as planned follow-up.

## Acceptance Criteria

The sprint is accepted when:

- all required v2.1 artifacts exist;
- v2.1 candidate/assignment artifacts are `NOT_PRODUCTION`;
- v2-v2.1 comparison artifacts are `EXPERIMENT_ONLY`;
- the observed decision is documented exactly as generated;
- ROADMAP and ADR-012 state that Onda C follows v2.1;
- focused tests, full non-network tests, and ruff pass.
