# Regime Model Card - Onda 2R

Status: production heuristic quarantined; binary macro experiment is design-review eligible.
Date: 2026-06-09

## Purpose

`regime_label` is a causal weather-state feature for NZWN intraday Tmax
forecasting. It must be inferable from observations visible before the CP.

## Labels

- `southerly_disrupted`: precipitation, sharp cooling, or strong southerly flow.
- `standard_nw`: normal N/NW flow without strong foehn score.
- `strong_nw_foehn`: strong N/NW flow with high dewpoint depression.
- `calm_radiative`: default weak-flow/radiative morning state.
- `insufficient`: fewer than three valid pre-CP observations.

`late_warming` is not a valid causal regime label.

## Implementation

Production classifier: `solarstorm/eda/_regimes.py`

Inputs expected by the classifier:

- `ts_local`
- `tmp_c_int`
- `wind_dir_deg`
- `sknt`
- `dwp_c_int`
- `p01i`

The feature builder passes a strictly pre-CP slice. Observations at or after
the CP are excluded before calling the classifier.

## Current Heuristic

- `southerly_disrupted`: precipitation sum above 0.01, minimum hourly cooling
  below -2 C/h, or at least half observations in 135-225 degrees with mean
  southerly speed at least 12 kt.
- `strong_nw_foehn`: NW-sector mean wind speed times mean dewpoint depression
  above 60.
- `standard_nw`: at least 40% observations in the wrapped 270-45 degree sector
  or mean direction in that sector.
- `calm_radiative`: none of the above.

## Timing Risk Separation

Late Tmax is represented as a timing-risk target/audit layer, not as a regime.
Onda 4 R9 verifies that a month/regime q90 late-Tmax baseline exists separately
from deterministic Tmax MAE.

Future model features using late-Tmax timing must compute thresholds inside the
walk-forward training window.

## Evidence

- `reports/regime/2026-06-06-regime-clustering-report.md`
- `research/regime_clustering_report.md`
- `docs/decisions/011-regime-ontology-repair.md`

## 2026-06-06 Artifact Distribution

Regenerated `data/features.parquet` contains 21,824 feature rows:

| Regime | Rows |
|--------|------|
| `southerly_disrupted` | 17,308 |
| `standard_nw` | 2,466 |
| `strong_nw_foehn` | 1,309 |
| `calm_radiative` | 625 |
| `insufficient` | 116 |

Onda 4 R2 no longer fails because of `late_warming`, but the post-Onda 2R
robustness rerun still returns NO-GO because `calm_radiative` and
`standard_nw` have no passing feature. This may indicate underpowered segments,
poor regime separation, or missing regime-specific features. These labels must
not be treated as production-ready until R2 passes.

## Trigger Audit

Artifact: `reports/regime/2026-06-06-regime-trigger-audit.md`

The regenerated artifact shows the current `southerly_disrupted` class is
primarily a cooling-trigger class, not a precipitation-trigger class:

| Primary trigger | Rows | Share within `southerly_disrupted` |
|-----------------|------|------------------------------------|
| `cooling` | 16,382 | 0.946 |
| `southerly` | 926 | 0.054 |

`precip_trigger` is 0 rows in this audit. Any regime repair should therefore
start by testing the cooling rule and its overlap with NW/foehn/radiative cases,
not by treating light precipitation as the main cause of imbalance.

## Cooling-Rule Diagnostic

Artifact: `reports/regime/2026-06-06-cooling-rule-experiment.md`

This is an offline simulation only. It does not change the production
classifier.

If cooling is removed as a standalone disruption trigger, the candidate
distribution becomes less dominated by `southerly_disrupted`:

| Candidate regime | Rows under variant |
|------------------|--------------------|
| `standard_nw` | 11,036 |
| `strong_nw_foehn` | 4,055 |
| `southerly_disrupted` | 3,941 |
| `calm_radiative` | 2,676 |
| `insufficient` | 116 |

The key simulated moves are 8,570 rows from `southerly_disrupted` to
`standard_nw`, 2,746 to `strong_nw_foehn`, and 2,051 to `calm_radiative`.
This makes the cooling rule the next classifier-repair target, but not yet a
production change.

## Regime Deadlock Pivot — 2026-06-08

Status: PIVOT_ACCEPTED

The active unlock path is the deadlock pivot, not v2.4 threshold tuning.

- `macro_calm_radiative` is audit-only until future evidence proves otherwise.
- Production-blocking macros: `macro_nw_continuum` and `macro_southerly_flow`.
- The binary macro experiment (`macro_southerly_flow` vs `macro_non_southerly`)
  is experiment-only and has passed the Onda 3 design-review gate with caveats.
- `cloud_cover_suppression` may proceed to baseline comparison but is not yet
  a production feature.
- Onda 4 must evaluate the binary candidate and cloud baseline separately.
- No full-day target labels (`tmax_hour`, `remaining_warming`) may be used as
  live features or regime-definition criteria.

Artifacts:

- `reports/regime-design/regime_deadlock_pivot_decision_v1.md`
- `reports/regime-design/regime_audit_demotions_v1.md`
- `reports/regime-design/regime_binary_macro_candidate_v1.md`
- `reports/regime-design/regime_binary_macro_classifiability_v1.md`
- `reports/regime-design/regime_binary_macro_r2_validation_v1.md`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.md`
- `reports/onda2e/regime_deadlock_diagnosis_v1.md`

## Binary Macro Validation - 2026-06-09

The experiment-only binary macro candidate records
`READY_FOR_ONDA3_DESIGN_REVIEW`, not production readiness.

Evidence:

- 0 dead binary macros in R2 screening.
- Predictive assignment AUC 0.9886 on the physical classifiability matrix.
- Fold stability 0.8089 and temporal stability 0.9917.
- Low confidence share 0.0000 for the hard binary assignment surface.

Caveats:

- AUC measures assignment separability, not direct Tmax predictive skill.
- `macro_non_southerly` remains weakly sensitive: 3/92 R2 pass rows versus 47/92
  for `macro_southerly_flow`.
- The validation gate blocks single-class train/test splits as
  `BLOCKED_INSUFFICIENT_CLASS_VARIATION`.
- Onda 3 must use continuous EDA-derived features and slice diagnostics rather
  than treating the binary macro label as a complete physical explanation.

## Intraday State-Change Layer

Intraday changes are changes in the observed characteristics of the day, not a
new regime ontology. Future features may estimate risks such as clearing,
southerly interruption, or NW re-strengthening between known physical regimes.
That layer should not be promoted until the base regimes themselves are clear
and pass R2.

## Regime Ontology v2 Candidate

Artifacts:

- `reports/onda2e/regime_design_candidate_v2.csv`
- `reports/onda2e/regime_design_candidate_v2.md`
- `reports/regime-design/regime_candidate_assignments_v2.csv`
- `reports/regime-design/regime_candidate_ontology_v2.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2.csv`
- `reports/regime-design/regime_candidate_v1_v2_comparison.csv`
- `reports/regime-design/regime_candidate_v2_validation_report.md`

The v2 redesign is a non-production candidate that separates macro regimes,
local subtypes, latent centroid components, and assignment confidence. It keeps
all candidate/assignment artifacts at `production_status = NOT_PRODUCTION`;
the v1-v2 comparison remains `EXPERIMENT_ONLY`.

The 2026-06-08 v2 candidate has 96 centroid rows and three macro labels:
`macro_nw_continuum`, `macro_southerly_flow`, and
`macro_light_marine_or_residual`. It assigns all 21,824 feature rows, but the
screening result is still `KEEP_IN_REGIME_DESIGN_REVIEW` because
`macro_light_marine_or_residual` has 0/92 passing R2 rows. Assignment
confidence is also weak enough that the residual/light-marine surface needs
redesign before a full Onda 4 rerun.

The production-facing `regime_label` remains the quarantined Onda 2R baseline
until ADR-012 and Onda 4 approve a replacement. Passing a future v2 screening
may only unlock full Onda 4 robustness validation, not direct Onda 3 model
training.

## Regime Ontology v2.1 Residual Absorption

Artifacts:

- `reports/regime-design/regime_residual_absorption_diagnostics_v1.csv`
- `reports/regime-design/regime_residual_absorption_diagnostics_v1.md`
- `reports/regime-design/regime_candidate_assignments_v2_1.csv`
- `reports/regime-design/regime_candidate_ontology_v2_1.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2_1.csv`
- `reports/regime-design/regime_candidate_v2_v21_comparison.csv`
- `reports/regime-design/regime_candidate_v21_validation_report.md`

The v2.1 residual-absorption experiment removes
`macro_light_marine_or_residual` from the R2 macro surface. Its 351 assignment
rows are reassigned to the nearest protected physical macro while preserving
`original_macro_regime_label`, `original_subtype_label`,
`absorbed_from_residual`, and residual diagnostics as audit metadata.

The generated v2.1 assignments keep all 21,824 rows at
`production_status = NOT_PRODUCTION`: `macro_nw_continuum` has 15,879 rows and
`macro_southerly_flow` has 5,945 rows. Residual absorption sent 241 rows to
`macro_nw_continuum` and 110 rows to `macro_southerly_flow`; diagnostics found
0 invalid absorption targets. Residual/maritime evidence is therefore an
audit/subtype layer, not a production macro regime.

The v2.1 R2 screen has 0 dead macros and
`regime_candidate_v2_v21_comparison.csv` records
`decision_update = READY_FOR_FULL_ONDA4_RERUN`, with every comparison row
`EXPERIMENT_ONLY`. The full candidate Onda 4 rerun then passed with verdict
`GO` in `reports/robustness-v2_1/2026-06-08-robustness-report.md`, using
`reports/regime-design/features_candidate_v2_1.parquet` and
`--regime-set macro_nw_continuum,macro_southerly_flow`.

This supports Opcao A as a viable non-production candidate surface, but it did
not start Onda 3. Onda C then tested whether the candidate structure was
classifiable, stable, and topologically coherent enough to become an Onda 3
modeling surface.

## Regime Ontology v2.2 Calm/Radiative Restoration

Artifacts:

- `reports/regime-design/regime_candidate_assignments_v2_2.csv`
- `reports/regime-design/regime_candidate_ontology_v2_2.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.md`
- `reports/regime-design/regime_candidate_r2_validation_v2_2.csv`
- `reports/regime-design/regime_candidate_v21_v22_comparison.csv`
- `reports/regime-design/regime_candidate_v22_validation_report.md`

v2.2 restores `macro_calm_radiative` as a protected macro with a physical
overlay on v2.1 assignments: low pre-CP wind plus at least two supporting
signals among high humidity, low dewpoint depression, high cloud cover, and
weak pre-CP slope. It does not revive `macro_light_marine_or_residual` as a
production-eligible macro.

The generated v2.2 assignments keep all 21,824 rows at
`production_status = NOT_PRODUCTION`: `macro_calm_radiative` has 2,572 rows,
`macro_nw_continuum` has 13,726 rows, and `macro_southerly_flow` has 5,526
rows. The smallest calm/radiative CP support is 502 rows, so the failure is not
just lack of sample size.

The v2.2 R2 screen blocks promotion: `macro_calm_radiative` has 0/92 passing
R2 rows, while `macro_nw_continuum` has 23/92 and `macro_southerly_flow` has
47/92. v2.2 therefore remains `KEEP_IN_REGIME_DESIGN_REVIEW`.

## Regime Ontology v2.3 Calm/Radiative Failure Diagnostic

Artifacts:

- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.md`
- `reports/regime-design/regime_v23_next_experiments.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.md`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.md`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.csv`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.md`

v2.3 is a diagnostic layer, not a new classifier. It explains the v2.2 blocker
as `CALM_RADIATIVE_VALIDATION_TARGET_GAP`: `macro_calm_radiative` has 2,572
assignment rows, 825 unique days, and smallest CP support of 502 rows, but it
still has 0/92 passing R2 rows. Its R2 median `n_days` is only 27, compared
with 210 for `macro_nw_continuum` and 110 for `macro_southerly_flow`.

The historical next experiment queue was `CEXP-CALM-RADIATIVE-001` target
diagnostics, `CEXP-CALM-RADIATIVE-002` calm-specific causal feature hypotheses,
and `CEXP-CALM-RADIATIVE-003` macro-versus-subtype/split comparison. That queue
explained the calm/radiative failure and led to the deadlock pivot; it is no
longer the active Onda 3 entry path.

`CEXP-CALM-RADIATIVE-001` is now complete. It produced 144 train-window
macro x month x CP target cells, including 48 calm/radiative cells. The
calm/radiative cells show median p50 remaining warming of 3.5 C, median p90
remaining warming of 5.0 C, and median p50 Tmax hour of 13:00, but 20/48 cells
remain underpowered. This is target/audit evidence only; it supports
calm-specific causal feature investigation, not production classifier
promotion.

`CEXP-CALM-RADIATIVE-002` is complete as an experiment-only feature screen.
It evaluated 8 train-window calm-specific hypotheses and found 1 preliminary
candidate signal, `cloud_cover_suppression` (Pearson corr -0.318, slope -2.89).
The remaining features were weak, constant, or underpowered. This nominates a
causal robustness check for `cloud_cover_suppression`; it does not promote a
feature or production classifier.

`CEXP-CALM-RADIATIVE-002B` is also complete. It validates
`cloud_cover_suppression` as pre-CP cloud evidence under the current train
window, not a proxy/artifact: 1,725 rows, overall slope -2.89, controlled slope
-1.75, controlled retention 0.605, negative slopes in 4/4 CP cells and 25/25
supported month x CP cells, and max proxy correlation 0.340. CEXP-003
demote/split was not triggered by signal failure.

## Onda C Classifiability Result

Onda C has been implemented and executed as a classifiability benchmark. The
corrected Regime Measurement Reset ran on 2026-06-08 using the audited physical
meteorological feature basis.

Artifacts:
- `reports/regime-classifiability/regime_classifiability_assignments_v1.csv`
- `reports/regime-classifiability/regime_classifiability_metrics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_comparison_v1.csv`
- `reports/regime-classifiability/regime_classifiability_diagnostics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_report_v1.md`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`

Historical v2.2 result and status:
- The v2.2 overall benchmark verdict is `BLOCK_ONDA_C_PROMOTION`; this is
  retained as evidence for the superseded 3-macro path.
- The reset included 8 approved physical features.
- `precip_pre_cp_sum` was rejected as constant.
- The forbidden unrestricted numeric fallback was not used.
- The later binary macro validation is the active Onda 3 design-review gate and
  records `READY_FOR_ONDA3_DESIGN_REVIEW`.
- Guardrail diagnostics pass for non-production status, leakage checks,
  duplicate assignment keys, physical feature-basis loading, fallback
  exclusion, and exclusion of outcome and quarantined-label columns.
- The v2.2 candidate comparison gate fails because `macro_calm_radiative` is
  dead in R2 before Onda C promotion.
- `distance_softmax_v22` has 3 macros and no missing protected macro in the
  assignment surface, but it remains weak: low confidence share 0.8226,
  classifiability score 0.0539, and stability 0.6154.
- Onda C remains non-production and did not generate any Onda 3 model files or
  estimators.
- The later deadlock pivot and binary macro validation supersede this result as
  the active Onda 3 entry path while preserving it as audit history.

## Onda 3 Baseline Model Handoff

The first Onda 3 baseline-first model artifacts have been generated under
`reports/onda3/`. The run uses the binary macro surface as experiment-only
context and continuous causal features as model inputs rather than adding a new
hard regime ontology.

Result:

- train-mean null MAE: 2.8120
- ridge challenger MAE: 1.3487
- decision status: `READY_FOR_ONDA4_MODEL_RERUN`
- production status: `EXPERIMENT_ONLY`

This is a model-review handoff, not production promotion. The production-facing
regime classifier remains quarantined, and the binary macro surface remains
experiment-only until a future robustness/promotion gate explicitly replaces
the current classifier.

## Onda 4 Model Review Status

Onda 4M model robustness review has now run. It reads the experiment-only Onda 3
artifacts from `reports/onda3/` and writes model review outputs under
`reports/onda4-model/`.

Planning artifacts:

- `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`
- `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`

The review uses M1-M8 model gates for input integrity, causal manifest safety,
challenger lift, temporal robustness, slice robustness, uncertainty/abstention,
anti-nowcast/model timing, and decision hygiene. These gates are separate from
historical Onda 4 R1-R9 regime robustness.

Generated result:

- M1-M8 all pass.
- decision status: `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- production status: `EXPERIMENT_ONLY`

The regime model remains non-production. This passing Onda 4M review allows the
next Onda 3 model iteration only; it cannot promote the regime classifier,
binary macro assignments, deployment, or market execution.

## Onda 3B Model Iteration Handoff

Onda 3B has now generated CP-specific next-model artifacts under
`reports/onda3-next/`. The run uses the binary macro surface only as
experiment-only categorical context and does not promote it to production.

Result:

- `20:00` ridge MAE 1.3761 versus null MAE 2.8120.
- `21:00` ridge MAE 1.3120 versus null MAE 2.8120.
- `22:00` ridge MAE 1.1981 versus null MAE 2.8120.
- `23:00` ridge MAE 1.1973 versus null MAE 2.8120.
- decision status: `READY_FOR_ONDA4_MODEL_RERUN`
- production status: `EXPERIMENT_ONLY`

The follow-up Onda 4M model robustness review of `reports/onda3-next/` has now
run under `reports/onda4-model-next/`.

Review result:

- M1-M8 all pass.
- M3 records null MAE 2.8120, challenger MAE 1.2708, lift 1.5411, and
  challenger failures 0 across CP-specific rows.
- decision status: `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- production status: `EXPERIMENT_ONLY`

The next action is another experiment-only Onda 3 model iteration. The regime
classifier and binary macro assignments remain non-production.

## Onda 3D Binary-Macro Interaction Handoff

Onda 3D has now tested the model structure implied by the binary macro pivot:
the binary macro label acts as a structural switch, while continuous signals
explain residual variance inside each macro.

The experiment adds four interaction inputs:

- `foehn_score_x_macro_non_southerly`
- `foehn_score_x_macro_southerly_flow`
- `cloud_cover_suppression_x_macro_non_southerly`
- `cloud_cover_suppression_x_macro_southerly_flow`

Result:

- all 12 year x CP challenger rows beat their train-mean nulls.
- all 12 year x CP challenger rows improve versus the Onda 3C no-interaction
  challenger.
- mean MAE delta versus no-interaction rolling surface: -0.0300.
- Onda 4M M3 records null MAE 2.9522, challenger MAE 1.1726, lift 1.7796,
  and challenger failures 0.
- Onda 4M M4 records rolling temporal diagnostics for `2023,2024,2025`.
- decision status: `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- production status: `EXPERIMENT_ONLY`

This supports the binary macro regime as a predictive switch, not as a claim
that Wellington has only two descriptive meteorological regimes. The regime
classifier and binary macro assignments remain non-production.

## Onda 3C Rolling Temporal Handoff

Onda 3C has now generated rolling annual model artifacts under
`reports/onda3-rolling/`. It reruns the CP-specific ridge challenger against
test years `2023,2024,2025`, with each test year trained only on prior years.

Result:

- 12 year x CP challenger rows beat their train-mean nulls.
- Onda 4M M3 records null MAE 2.9522, challenger MAE 1.2026, lift 1.7496,
  and challenger failures 0.
- Onda 4M M4 records rolling temporal diagnostics for `2023,2024,2025`.
- decision status: `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- production status: `EXPERIMENT_ONLY`

The next action is another experiment-only Onda 3 model iteration. The regime
classifier and binary macro assignments remain non-production.
