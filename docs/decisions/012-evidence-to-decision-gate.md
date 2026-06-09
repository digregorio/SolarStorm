# ADR-012: Evidence-to-Decision Gate

- **Date:** 2026-06-07
- **Status:** Accepted
- **Last updated:** 2026-06-09

## Context

SolarStorm has repeatedly drifted from data-first climatology into hardcoded
rules, superficial regime names, and trial-and-error feature work. The most
important examples are:

- `late_warming` was treated as a regime even though it is an ex-post Tmax
  timing outcome.
- The first physical regimes were promoted before the EDA proved they were
  climatologically stable.
- `southerly_disrupted` became dominated by a broad cooling trigger before the
  project had separated radiative, frontal, precipitation, and artifact cooling.

Onda 2E now has a 251-thesis climatology atlas. That atlas must not become a
folder of unused CSVs. Every EDA result must feed a traceable project decision.

## Decision

Introduce a mandatory Evidence-to-Decision Gate between EDA and every downstream
use of regimes, features, models, and robustness reruns.

No thesis, regime definition, feature candidate, model input, or robustness
repair may be promoted unless it has a registered decision backed by an
artifact reference.

Decision statuses:

| Status | Meaning | Allowed next step |
|---|---|---|
| `SUPPORTED` | Data supports the thesis descriptively. | May move to causal-availability review. |
| `REJECTED` | Data contradicts or fails to support the thesis. | Must not reappear without new evidence. |
| `ADAPTED` | Original thesis was wrong or too crude, but data produced a better formulation. | New formulation gets a decision record. |
| `BLOCKED` | Cannot be resolved due to missing data, leakage risk, or insufficient power. | Stays blocked; no proxy approximation by guess. |
| `PROMOTED_TO_REGIME_DESIGN` | Evidence can influence a replacement regime ontology. | Enters regime design queue only. |
| `PROMOTED_TO_FEATURE_CANDIDATE` | Evidence is causal-available and may become a feature candidate. | Enters feature design queue only. |
| `QUARANTINED_BASELINE` | Existing rule/artifact is retained only as a diagnostic comparator. | Cannot justify model inputs or claims. |

Every decision record must include:

- thesis ID or rule ID;
- source artifact path;
- evidence level;
- month/CP/regime strata used;
- sample-size or power warning;
- causal availability statement;
- leakage risk;
- decision status;
- short decision rationale;
- next allowed action.

## Generated 2026-06-07 State

The Onda 2E-Gate artifacts generated on 2026-06-07 are the current decision
surface:

- `reports/onda2e/evidence_decision_register.csv`
- `reports/onda2e/regime_design_queue.csv`
- `reports/onda2e/feature_candidate_queue.csv`
- `reports/onda2e/rejection_register.csv`
- `reports/onda2e/quarantined_baseline_register.csv`
- `reports/onda2e/onda2e_decision_report.md`

`evidence_decision_register.csv` has 250 rows: 245 active thesis decisions and
5 baseline-rule decisions. The 6 theses that require unavailable external data
are removed from the active ADR-012 universe and recorded in
`reports/onda2e/removed_external_theses.csv`: `WCT-PRES-008`, `WCT-GAP-014`,
`WCT-GAP-024`, `WCT-GAP-025`, `WCT-GAP-031`, and `WCT-GAP-047`.

Active decision counts are `ADAPTED` 48, `PROMOTED_TO_REGIME_DESIGN` 4,
`QUARANTINED_BASELINE` 2, `REJECTED` 22, and `SUPPORTED` 174. There are 0
active `BLOCKED` thesis decisions.

The thesis-domain EDA is now its own evidence surface:
`reports/onda2e/domain_thesis_evidence.csv` has 245 active local thesis rows,
`reports/onda2e/domain_thesis_decision_updates.csv` has 245 ADR-012 update
rows, and `reports/onda2e/domain_thesis_eda_report.md` summarizes the resolved
backlog. `reports/onda2e/domain_eda_next_experiments.csv` has 0 rows because no
active thesis remains blocked without a decision; future work now proceeds
through explicit queues rather than a blocked EDA backlog.

Implemented Onda 2E domains are `TIMING`, `COOLING`, `FOEHN`, `WIND`, thesis
domain evidence, and regime architecture. Supported thesis decisions are
descriptive evidence only, not production model features.

Promoted regime-design decisions are `WCT-COOL-003`, `WCT-FOEHN-001`,
`WCT-WIND-019`, and `WCT-REGIME-016`. They enter `regime_design_queue.csv`
only; `WCT-REGIME-016` is backed by `regime_design_candidate_v1.csv` and is
not a production classifier.

`WCT-REGIME-016` now also has an offline candidate-validation surface under
`reports/regime-design/`:

- `regime_candidate_assignments_v1.csv`
- `regime_candidate_ontology_v1.csv`
- `regime_candidate_assignment_audit.csv`
- `regime_candidate_validation_scope.csv`
- `regime_candidate_r2_validation.csv`
- `regime_candidate_decision_update.csv`
- `regime_candidate_validation_report.md`

The 2026-06-07 candidate screening assigned 21,824/21,824 feature rows with 0
null candidate labels. The assignment audit has `missing_input_imputation =
WARN` because 3,162 missing causal assignment inputs were imputed from training
means. The validation scope is a one-year R2 screening window
(`test_start = 2025-01-01`, CPs `20:00,21:00,22:00,23:00`), not a full Onda 4
production acceptance run. Candidate family counts are
`candidate_maritime_cloudy` 31, `candidate_mixed_or_transition` 320,
`candidate_nw_or_foehn` 15,638, and `candidate_southerly_disrupted` 5,835.
R2 still finds 2 dead candidate families: `candidate_maritime_cloudy` and
`candidate_mixed_or_transition`. Therefore `WCT-REGIME-016` remains
`PROMOTED_TO_REGIME_DESIGN` and design-review only; the next allowed action is
to revise the candidate ontology or assignment before a full Onda 4 rerun.

Adapted diagnostic comparators are `RULE_LATE_WARMING_FIXED_18`,
`RULE_COOLING_FIXED_MINUS_2_C_PER_H`, and `RULE_FOEHN_SCORE_FIXED_60`. These
rules remain useful for audit/comparison, but they are not production truth.

Active quarantined decision rows are `REGIME_CLASSIFIER_CURRENT` and
`RULE_ONDA2R_PHYSICAL_REGIME_FAMILY`. The separate
`quarantined_baseline_register.csv` still has 5 baseline comparator rows:
current regime classifier, fixed 18:00 late-Tmax logic, fixed `-2 C/h` cooling
threshold, fixed `foehn_score > 60`, and the Onda 2R physical regime family.
The comparator register is therefore not the same as the active quarantine
count in the decision register.

`regime_design_queue.csv` has 9 items: 5 baseline comparators plus
`WCT-COOL-003`, `WCT-FOEHN-001`, `WCT-WIND-019`, and `WCT-REGIME-016`.
`feature_candidate_queue.csv` is empty and `rejection_register.csv` has 22
items.

The Foundation Experiment Catalog is now the bridge from this EDA decision
surface to implementation experiments:

- `reports/foundation-experiments/foundation_experiment_catalog_v1.csv`
- `reports/foundation-experiments/foundation_experiment_catalog_v1.md`

The 2026-06-07 catalog has 25 experiment-only rows: 9 baseline, 11 regime, 4
threshold, and 1 feature experiment. Every row has
`production_status = EXPERIMENT_ONLY`. The first results surface is now
generated separately:

- `reports/foundation-experiments/foundation_experiment_results_v1.csv`
- `reports/foundation-experiments/foundation_experiment_results_v1.md`

`foundation_experiment_results_v1.csv` has 25 rows: 4 completed experiment
rows and 21 `not_run` rows for catalog items without a v1 runner. Status counts
are 2 `passed`, 2 `failed`, and 21 `not_run`. Every row keeps
`production_status = EXPERIMENT_ONLY`. The completed baseline probes are:

- `BEXP-L2-MONTH-REGIME-001`: passed, baseline MAE 1.8256, candidate MAE
  1.5058, effect 0.3198, CI [0.2975, 0.3422], 11,652 rows, 8 years.
- `BEXP-L4-MONTH-CP-REGIME-001`: passed, baseline MAE 1.7523, candidate MAE
  1.1768, effect 0.5755, CI [0.5441, 0.6075], 11,652 rows, 8 years.

The completed dead-regime probes confirm that the current candidate ontology
still blocks Onda 3:

- `REXP-DEAD-MARITIME-001`: failed, `r2_dead_regimes = 2`,
  `candidate_maritime_cloudy` remains dead with 0/92 passing R2 rows and 31
  assignment support rows.
- `REXP-DEAD-MIXED-001`: failed, `r2_dead_regimes = 2`,
  `candidate_mixed_or_transition` remains dead with 0/92 passing R2 rows and
  320 assignment support rows.

The remaining priority rows include calibration probes for cooling, FOEHN, and
southerly-depth regime design.

## Generated 2026-06-08 Regime Ontology v2 State

Regime Ontology v2 is now a formal non-production redesign candidate. It
introduces a hierarchical macro/subtype assignment surface to repair the v1
flat-family failure, while preserving the Onda 2E k=6 physical centroid
evidence as subtype/latent-component structure.

Generated artifacts:

- `reports/regime-design/regime_repair_diagnostics_v1.csv`
- `reports/regime-design/regime_repair_diagnostics_v1.md`
- `reports/onda2e/regime_design_candidate_v2.csv`
- `reports/onda2e/regime_design_candidate_v2.md`
- `reports/regime-design/regime_candidate_assignments_v2.csv`
- `reports/regime-design/regime_candidate_ontology_v2.csv`
- `reports/regime-design/regime_candidate_assignment_audit_v2.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2.csv`
- `reports/regime-design/regime_candidate_v1_v2_comparison.csv`
- `reports/regime-design/regime_candidate_v2_validation_report.md`

`regime_design_candidate_v2.csv` has 96 rows and all rows keep
`production_status = NOT_PRODUCTION`. Macro candidate counts are
`macro_nw_continuum` 56, `macro_southerly_flow` 33, and
`macro_light_marine_or_residual` 7. The v2 assignment run labels 21,824/21,824
feature rows: `macro_nw_continuum` 15,638, `macro_southerly_flow` 5,835, and
`macro_light_marine_or_residual` 351. Assignment artifacts are also
`NOT_PRODUCTION`.

The v2 comparison is experiment-only and does not unlock production:
`regime_candidate_v1_v2_comparison.csv` has 3 rows with
`production_status = EXPERIMENT_ONLY` and `decision_update =
KEEP_IN_REGIME_DESIGN_REVIEW`. `macro_nw_continuum` and
`macro_southerly_flow` pass R2 screening, but
`macro_light_marine_or_residual` remains dead with 0/92 passing R2 rows.
Low-confidence assignment shares are high for all macros, especially the
residual macro. Therefore v2 has reduced the flat-family problem from 2 dead
families to 1 dead macro, but it has not passed the gate for a full Onda 4
rerun.

The v2 redesign does not promote `mixed_or_transition`, `maritime_cloudy`, or
`late_warming` as production macro regimes. `mixed_or_transition` and
`maritime_cloudy` remain residual/low-confidence subtypes, and `late_warming`
remains outside the ex-ante regime ontology.

This v2 result led to the Regime Ontology v2.1 residual-absorption sprint
described below.

## Generated 2026-06-08 Regime Ontology v2.1 State

Regime Ontology v2.1 has now been generated as a non-production screening
experiment. It removes `macro_light_marine_or_residual` from the R2 macro
surface, reassigns those rows to the nearest protected physical macro, and
preserves the residual evidence as audit metadata.

Generated artifacts:

- `reports/regime-design/regime_residual_absorption_diagnostics_v1.csv`
- `reports/regime-design/regime_residual_absorption_diagnostics_v1.md`
- `reports/regime-design/regime_candidate_assignments_v2_1.csv`
- `reports/regime-design/regime_candidate_ontology_v2_1.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2_1.csv`
- `reports/regime-design/regime_candidate_v2_v21_comparison.csv`
- `reports/regime-design/regime_candidate_v21_validation_report.md`

The v2.1 assignment surface has 21,824 rows and all rows keep
`production_status = NOT_PRODUCTION`. The 351 v2 residual rows were absorbed:
241 into `macro_nw_continuum` and 110 into `macro_southerly_flow`.
Residual diagnostics record 329/351 residual rows as low-confidence, but 0
invalid absorption targets. The resulting v2.1 macro support is
`macro_nw_continuum` 15,879 rows and `macro_southerly_flow` 5,945 rows.

The v2.1 R2 validation has 184 rows and 0 dead macros. The comparison artifact
has 2 rows, all `production_status = EXPERIMENT_ONLY`, with
`decision_update = READY_FOR_FULL_ONDA4_RERUN`. `macro_nw_continuum` has 3/92
passing R2 rows and `macro_southerly_flow` has 45/92 passing R2 rows; both are
`PASS`, and no protected macro regressed.

Foundation experiment results were refreshed from the v2.1 comparison:
`foundation_experiment_results_v1.csv` still has 25 experiment-only rows, now
with 4 passed completed rows and 21 `not_run` rows. The dead-regime probes
`REXP-DEAD-MARITIME-001` and `REXP-DEAD-MIXED-001` now pass with
`r2_dead_regimes = 0` because the residual/mixed labels are no longer treated
as production-eligible macro regimes.

The full Onda 4 rerun against the v2.1 candidate feature copy has now passed:
`reports/robustness-v2_1/2026-06-08-robustness-report.md` records verdict
`GO`. The run used `reports/regime-design/features_candidate_v2_1.parquet`,
not `data/features.parquet`, and evaluated R2 against
`macro_nw_continuum,macro_southerly_flow`. Results were R1 8 passing years,
R2 0 dead regimes, R3 0 causal violations, R4 no negative drift warning
(`p = 0.5362`), R5 fresh gates pass, R6 not nowcast-only, R7 no fixed-CP
artifact, R8 late-spike artifact produced, and R9 late-Tmax baseline exists.

This validates Opcao A as a viable non-production candidate surface. It does
not promote the production classifier, does not overwrite `data/features.parquet`,
does not authorize financial execution, shadow trading, EV, or deployment work,
and does not start Onda 3. Onda C is the next required wave:
a classifiability/topology wave comparing the current
distance-softmax assignment surface against train-only GMM, SOM/topological
maps, and Michelangeli-style stability checks. Onda C is non-production and
cannot bypass ADR-012 or future production promotion gates.

No feature, model input, production classifier, or production regime ontology
is promoted by this generated state. Domain EDA has resolved the active local
thesis backlog, and experiment-only Onda 4 baseline/repair work is now
unblocked. The v2.1 screening has eliminated the dead candidate-family blocker,
and the v2.1 Onda 4 candidate rerun has passed.

## Generated 2026-06-08 Onda C Classifiability State

Onda C has been implemented and executed as a classifiability benchmark. It
evaluates the classifiability, stability, and topological structure of the
v2/v2.1 candidate regime surfaces.

Generated artifacts:
- `reports/regime-classifiability/regime_classifiability_assignments_v1.csv`
- `reports/regime-classifiability/regime_classifiability_metrics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_comparison_v1.csv`
- `reports/regime-classifiability/regime_classifiability_diagnostics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_report_v1.md`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`

Current historical state for the v2.2 Onda C route:
- The corrected Onda C Regime Measurement Reset first ran on 2026-06-08 using
  the audited physical meteorological feature basis and kept v2.1 in
  `KEEP_IN_REGIME_DESIGN_REVIEW`.
- The Onda C artifacts were rerun against v2.2. They include 8
  approved physical features, reject `precip_pre_cp_sum` as constant, and do
  not use the forbidden unrestricted numeric fallback.
- The v2.2 overall benchmark verdict is `BLOCK_ONDA_C_PROMOTION`; this is
  retained as evidence for the superseded 3-macro path.
- The later binary macro validation is the active Onda 3 design-review gate and
  records `READY_FOR_ONDA3_DESIGN_REVIEW`.
- Guardrail diagnostics pass for leakage, duplicate assignment keys,
  non-production status, physical feature-basis loading, approved feature
  count, fallback exclusion, outcome exclusion, and quarantined-label
  exclusion.
- The `candidate comparison gate` diagnostic fails because v2.2 is blocked by
  its own R2 comparison before Onda C promotion.
- Onda C remains non-production and did not generate any Onda 3 model files or
  estimators.

## Generated 2026-06-08 Regime Ontology v2.2 State

Regime Ontology v2.2 has now been generated as a non-production screening
experiment. It restores `macro_calm_radiative` as a protected macro by applying
an audited physical overlay to v2.1 assignments. The restoration requires low
pre-CP wind and at least two supporting signals among high humidity, low
dewpoint depression, high cloud cover, and weak pre-CP temperature slope.

Generated artifacts:

- `reports/regime-design/regime_candidate_assignments_v2_2.csv`
- `reports/regime-design/regime_candidate_ontology_v2_2.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.md`
- `reports/regime-design/regime_candidate_r2_validation_v2_2.csv`
- `reports/regime-design/regime_candidate_v21_v22_comparison.csv`
- `reports/regime-design/regime_candidate_v22_validation_report.md`

The v2.2 assignment surface has 21,824 rows and all rows keep
`production_status = NOT_PRODUCTION`. Macro support is
`macro_calm_radiative` 2,572 rows, `macro_nw_continuum` 13,726 rows, and
`macro_southerly_flow` 5,526 rows. The smallest CP support for
`macro_calm_radiative` is 502 rows.

The physical reassignment audit records thresholds
`sknt_mean <= 7.125`, `relh_mean >= 86.719091`,
`dewpoint_depression_mean <= 2.181818`, `cloud_cover_score_mean >= 2.705882`,
and `temp_slope_pre_cp <= 0.0`. It records 1,995 rows with at least one
missing physical rule input as a `WARN`, not a promotion blocker.

The v2.2 R2 comparison is experiment-only and blocks promotion:
`macro_calm_radiative` has 0/92 passing R2 rows and is `DEAD`.
`macro_nw_continuum` has 23/92 passing R2 rows and `macro_southerly_flow` has
47/92 passing R2 rows. Therefore
`regime_candidate_v21_v22_comparison.csv` records
`decision_update = KEEP_IN_REGIME_DESIGN_REVIEW` and v2.2 cannot unlock Onda 3
or a full Onda 4 promotion path.

The Onda C rerun against v2.2 records `BLOCK_ONDA_C_PROMOTION`.
`distance_softmax_v22` has 3 macros and no dead assignment macro inside the
classifiability assignment surface, but low confidence remains high at 0.8226,
classifiability is weak at 0.0539, and stability is below threshold at 0.6154.
Train-only alternatives also remain below classifiability/stability thresholds.
At that point, the correct next step was a v2.3 investigation of whether
calm/radiative needed its own causal feature hypotheses, a different subtype
treatment, or removal from the production-eligible macro surface. The later
deadlock pivot and binary macro validation supersede this as the active Onda 3
entry path.

## Generated 2026-06-08 Regime Ontology v2.3 Diagnostic State

Regime Ontology v2.3 is an experiment-only failure diagnostic, not a new
classifier. It explains why the v2.2 calm/radiative restoration has support but
still fails R2.

Generated artifacts:

- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.md`
- `reports/regime-design/regime_v23_next_experiments.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.md`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.csv`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.md`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.md`

The diagnostic records `CALM_RADIATIVE_VALIDATION_TARGET_GAP`.
`macro_calm_radiative` has 2,572 assignment rows, 825 unique days, 4 CP slices,
and smallest CP support of 502 rows, but it has 0/92 passing R2 rows. Its R2
median `n_days` is 27, versus 210 for `macro_nw_continuum` and 110 for
`macro_southerly_flow`. Feature coverage is a `WARN`, not a production
permission.

The v2.3 next-experiment queue is:

- `CEXP-CALM-RADIATIVE-001`: train-only calm/radiative target diagnostics
  (completed).
- `CEXP-CALM-RADIATIVE-002`: calm-specific causal feature hypotheses
  (completed).
- `CEXP-CALM-RADIATIVE-003`: macro protection versus subtype/audit demotion
  or radiative-clear/cloudy split.

CEXP-001 produced 144 train-window macro x month x CP target cells. The 48
calm/radiative cells have 20 underpowered cells, median p50 remaining warming
of 3.5 C, median p90 remaining warming of 5.0 C, and median p50 Tmax hour of
13:00. This confirms that calm/radiative has a target profile worth testing,
but it is full-day target audit evidence only and cannot be used as CP evidence
or production permission.

CEXP-002 screened 8 train-window calm/radiative feature hypotheses. It found 1
preliminary `CANDIDATE_SIGNAL`, `cloud_cover_suppression` (Pearson corr -0.318,
slope -2.89), plus 4 `WEAK_SIGNAL`, 2 `CONSTANT_FEATURE`, and 1
`UNDERPOWERED_FEATURE`. This result nominates a follow-up robustness check; it
does not promote `cloud_cover_suppression`, change a regime label, clear Onda C,
or unlock Onda 3. All CEXP-002 rows remain `EXPERIMENT_ONLY`, and full-day
target/proxy columns are blocked as `FULL_DAY_TARGET_OR_PROXY_AUDIT_ONLY`.

CEXP-002B then validated `cloud_cover_suppression` against proxy/artifact risk.
It records `SURVIVES_CAUSAL_ROBUSTNESS_SCREEN`: 1,725 rows, overall slope
-2.89, controlled slope -1.75 after dewpoint, warming-rate, dewpoint-collapse,
and pressure controls, controlled retention 0.605, 4/4 CP cells and 25/25
supported month x CP cells with negative slopes, and max proxy correlation
0.340. Its lineage is `PASS_PRE_CP_CLOUD_OBSERVATION`. CEXP-003 demote/split
was not triggered because the failure condition did not occur.

The follow-up binary macro validation has now converted this deadlock into an
Onda 3 design-review entry point. `WCT-BINARY-MACRO` records
`READY_FOR_ONDA3_DESIGN_REVIEW` with an experiment-only
`macro_southerly_flow` versus `macro_non_southerly` surface. The decision is
caveated: `macro_non_southerly` has weak R2 sensitivity, and predictive AUC
measures assignment separability, not direct Tmax skill. The next allowed action
is the Onda 3 baseline-first model design and implementation plan, not
production promotion.


## Regime Policy

The current regime classifier is not the final ontology. It is a quarantined
baseline until Onda 2E produces a data-backed replacement or a documented
reason to retain a specific element.

The project must replace arbitrary regime logic with climatology-derived
definitions. A candidate regime ontology must be built from observed Wellington
structure: month, CP, wind sector and speed, cooling taxonomy, pressure/rain
context, Tmax timing norms, and sample-size power. It must then pass Onda 4 R2
without dead physical regimes before Onda 3 model work resumes.

No fixed threshold such as `tmax_hour >= 18`, `min_delta_t_per_h < -2`, or
`foehn_score > 60` may be treated as production truth unless it has passed this
gate. Hardcoded values may exist only as diagnostic baselines or candidate
tests.

## Consequences

### Required

- Onda 2E must produce a decision register, a regime design queue, a feature
  candidate queue, a rejection register, and a quarantined-baseline register.
- Domain EDA reports must end with decisions, not only descriptive tables.
- Onda C has run against v2.2 and records `BLOCK_ONDA_C_PROMOTION` for the
  superseded 3-macro path. The follow-up binary macro validation records
  `READY_FOR_ONDA3_DESIGN_REVIEW`, so Onda 3 design review may proceed under
  the baseline-first plan while production remains blocked.
- Old Wellington reports and current heuristic regimes are evidence sources or
  baselines, not authority.
- Polymarket, EV, shadow/live execution, position sizing, and production
  deployment remain on hold. The project focus is a predictive model with
  uncertainty and stay-out behavior, not nowcast or execution.

### Prevented

- Continuing with regimes because they already exist in code.
- Promoting features because they look plausible in a table.
- Reintroducing rejected ideas under new names.
- Using unavailable data proxies or hardcoded constants to fill gaps silently.
- Letting the 251-thesis atlas become an archive with no effect on the project.

## Generated 2026-06-08 Regime Deadlock Pivot State

The active unlock path now follows `reports/onda2e/regime_deadlock_diagnosis_v1.md`.
The v2.2/v2.3 calm/radiative restoration and threshold-calibration loop is
superseded as the active path for Onda 3 unlock.

New experiment-only artifacts:

- `reports/regime-design/regime_deadlock_pivot_decision_v1.csv`
- `reports/regime-design/regime_deadlock_pivot_decision_v1.md`
- `reports/regime-design/regime_deadlock_superseded_path_v1.csv`
- `reports/regime-design/regime_audit_demotions_v1.csv`
- `reports/regime-design/regime_audit_demotions_v1.md`
- `reports/regime-design/regime_binary_macro_candidate_v1.csv`
- `reports/regime-design/regime_binary_macro_candidate_v1.md`
- `reports/regime-design/regime_binary_macro_assignments_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.md`

`macro_calm_radiative` is retained as an audit segment and no longer blocks the
production macro gate by itself. The production-blocking macro set for the
pivot review is `macro_nw_continuum` and `macro_southerly_flow`.

This did not by itself promote Onda 3, did not alter `data/features.parquet`,
and did not promote `cloud_cover_suppression` to production.

## Generated 2026-06-09 Binary Macro Validation and Onda 3 Design State

The binary macro validation fixes the active gate surface:

- `reports/regime-design/regime_binary_macro_r2_validation_v1.csv`
- `reports/regime-design/regime_binary_macro_r2_validation_v1.md`
- `reports/regime-design/regime_binary_macro_classifiability_v1.csv`
- `reports/regime-design/regime_binary_macro_classifiability_v1.md`
- `reports/regime-design/regime_binary_macro_decision_update_v1.csv`

Current decision:

- `decision_status = READY_FOR_ONDA3_DESIGN_REVIEW`
- `production_status = EXPERIMENT_ONLY`
- `predictive_auc = 0.9886`
- `stability_score = 0.8089`
- `temporal_stability = 0.9917`
- `macro_non_southerly` warning: 3/92 R2 pass rows versus 47/92 for
  `macro_southerly_flow`

The AUC gate must not approve train/test folds with only one class. Such splits
now block as `BLOCKED_INSUFFICIENT_CLASS_VARIATION` rather than receiving a
fabricated perfect AUC.

Onda 3 planning artifacts:

- `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`
- `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`

Onda 3 may now proceed only as baseline-first model experimentation. The first
implementation must compare against train-only nulls, carry EDA-derived
continuous features through a leakage-audited manifest, report uncertainty and
abstention diagnostics, and keep market execution out of scope.

No full-day target labels (`tmax_hour`, `remaining_warming`, `tmax_int`) may be
used as live model features or as regime-definition criteria. This rule is
unchanged by the pivot.

## Generated 2026-06-09 Onda 3 Baseline Model State

The first baseline-first Onda 3 implementation has now generated
experiment-only model artifacts:

- `reports/onda3/onda3_feature_manifest_v1.csv`
- `reports/onda3/onda3_design_matrix_audit_v1.csv`
- `reports/onda3/onda3_baseline_results_v1.csv`
- `reports/onda3/onda3_challenger_results_v1.csv`
- `reports/onda3/onda3_slice_diagnostics_v1.csv`
- `reports/onda3/onda3_uncertainty_abstention_v1.csv`
- `reports/onda3/onda3_decision_update_v1.csv`
- `reports/onda3/onda3_baseline_model_report_v1.md`

The first generated comparison records train-mean null MAE 2.8120 and ridge
challenger MAE 1.3487. `onda3_decision_update_v1.csv` records
`decision_status = READY_FOR_ONDA4_MODEL_RERUN` and
`production_status = EXPERIMENT_ONLY`.

This does not promote a production model, does not authorize deployment, and
does not unlock market execution. The next allowed action is an Onda 4-style
model robustness rerun/review of the experiment-only Onda 3 baseline result.

## Generated 2026-06-09 Onda 4 Model Robustness Review State

Onda 4 model review has generated the first model robustness artifact surface.
It reads the Onda 3 baseline artifacts from `reports/onda3/`, evaluates
model-specific M1-M8 gates, and writes review artifacts under
`reports/onda4-model/`.

Planning artifacts:

- `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`
- `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`

Generated artifacts:

- `reports/onda4-model/onda4_model_input_audit_v1.csv`
- `reports/onda4-model/onda4_model_input_audit_v1.md`
- `reports/onda4-model/onda4_model_gate_results_v1.csv`
- `reports/onda4-model/onda4_model_gate_results_v1.md`
- `reports/onda4-model/onda4_model_slice_review_v1.csv`
- `reports/onda4-model/onda4_model_slice_review_v1.md`
- `reports/onda4-model/onda4_model_uncertainty_review_v1.csv`
- `reports/onda4-model/onda4_model_uncertainty_review_v1.md`
- `reports/onda4-model/onda4_model_decision_update_v1.csv`
- `reports/onda4-model/onda4_model_decision_update_v1.md`
- `reports/onda4-model/onda4_model_robustness_report_v1.md`

Allowed review decisions:

- `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`
- `BLOCK_MODEL_PROMOTION`

These decisions remain experiment-only. They cannot promote a production model,
replace the production classifier, authorize deployment, or unlock market
execution. Onda 4 model gates are named M1-M8 so they do not overwrite the
historical R1-R9 regime/feature-null robustness semantics.

Current decision:

- `decision_status = READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- `production_status = EXPERIMENT_ONLY`
- M1-M8 all pass.
- The next allowed action is a next Onda 3 model iteration, not production
  deployment or market execution.

## References

- `reports/onda2e/thesis_atlas_v1.md`
- `reports/onda2e/regime_deadlock_diagnosis_v1.md`
- `reports/onda2e/onda2e_prerequisite_report.md`
- `docs/superpowers/specs/2026-06-06-wellington-climatology-thesis-atlas-design.md`
- `docs/superpowers/specs/2026-06-08-regime-deadlock-pivot-design.md`
- `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`
- `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`
- `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`
- `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`
- `docs/decisions/011-regime-ontology-repair.md`
- `ROADMAP.md`
