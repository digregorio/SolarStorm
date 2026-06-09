# SolarStorm Project Roadmap

Living status tracker for the SolarStorm rewrite. See
`docs/decisions/010-onda-waves.md` for the wave methodology.

Last updated: 2026-06-09

## Project Focus

SolarStorm is a model-first intraday Tmax forecaster for NZWN. The current goal
is not a financial system. The current goal is a model foundation that can prove
real predictive skill, identify uncertainty, and stay out when it has no edge.

Financial execution, EV, position sizing, shadow trading, and Polymarket API
work are on hold until a production model passes its predictive gates.

Core rule: no regime, feature, model input, or robustness repair may be promoted
from EDA unless it passes the Evidence-to-Decision Gate in ADR-012. Descriptive
tables are evidence, not permission to proceed.

## Onda 0: Scaffold

Status: complete

- Repository, tooling, CI, and core docs.
- IEM/METAR ingest, labels, settlement, and causal firewall.
- No model and no market layer.

## Onda 1: Baselines

Status: complete

- L0-L4 baseline ladder.
- Walk-forward validation harness.
- Frozen G1-G5 gates.
- Historical regime classifier and hypothesis catalog.

## Onda 2: Feature-Null Value

Status: complete on regenerated 2026-06-06 artifacts; regime-dependent claims remain gated by Onda 4

- Feature builder for H1-H23.
- Walk-forward validation with real best-null-per-CP.
- Calibrated train-only CP null.
- Validated feature contract and leaderboard artifacts.

Current fresh artifact count: 28 validated entries, 60 rejected, 4 blocked.
Do not hard-code this count in future plans; use the current contract artifact.

Regime-dependent features from the pre-Onda 2R run were provisional because
Onda 4 found the old regime ontology mixed causal states with ex-post Tmax
timing. The regenerated Onda 2R contract now uses physical regimes, but Onda 4
still blocks model work until each physical regime has robust segment evidence.

## Onda 2R: Regime Ontology Repair

Status: implemented in code and regenerated artifacts; Onda 4 rerun remains NO-GO

Purpose: rebuild the regime layer before Onda 3. The project must separate
causal physical regimes from ex-post timing events.

Required changes:

- Supersede the old 5-regime heuristic in ADR-006.
- Promote causal physical regimes only:
  `southerly_disrupted`, `standard_nw`, `strong_nw_foehn`,
  `calm_radiative`.
- Remove `late_warming` from the required ex-ante regime list.
- Define late Tmax as a month/regime-relative timing event learned train-only,
  not as `tmax_hour >= 18`.
- Revalidate regime-dependent features before they can support Onda 3. Fresh
  validation produced 28 validated pooled entries, all with `regime=all`.
- Rerun Onda 4 under the repaired R2/R7/R8/R9 semantics. The structural
  `late_warming` failure is fixed, but R2 now exposes dead physical regimes:
  `calm_radiative` and `standard_nw`.

Plan: `docs/onda2r_regime_ontology_repair_plan.md`
Design: `docs/regime_ontology_design.md`
Model card: `docs/regime_model_card.md`
Evidence: `reports/regime/2026-06-06-regime-clustering-report.md`
Trigger audit: `reports/regime/2026-06-06-regime-trigger-audit.md`
Cooling experiment: `reports/regime/2026-06-06-cooling-rule-experiment.md`

## Onda 2E: Wellington Climatology Thesis Atlas

Status: started on 2026-06-06; prerequisite EDA artifacts generated; decision gate now mandatory

Purpose: replace trial-and-error feature work with a dense, data-first
climatology atlas for Wellington. The base EDA document is
`reports/onda2e/thesis_atlas_v1.md`, which adopts 251 thesis IDs. These are
theses to prove, reject, adapt, or block, not features to implement.

Onda 2E is not complete when reports exist. It is complete only when the EDA
has produced a decision register and queues that tell the project what changes,
what stays quarantined, what is rejected, and what remains blocked.

Initial artifacts:

- `reports/onda2e/thesis_registry.csv`
- `reports/onda2e/thesis_testability_audit.csv`
- `reports/onda2e/onda2e_prerequisite_report.md`
- `reports/onda2e/prereq_power_map.csv`
- `reports/onda2e/prereq_regime_frequency.csv`
- `reports/onda2e/prereq_monthly_wind_rose.csv`
- `reports/onda2e/prereq_tmax_hour_distribution.csv`
- `reports/onda2e/prereq_remaining_warming_distribution.csv`
- `reports/onda2e/prereq_cooling_mechanism_taxonomy.csv`
- `reports/onda2e/prereq_tmax_anomaly_by_month.csv`

First findings:

- 251 thesis entries are preserved in the machine registry.
- 6 theses are blocked by external data.
- 22 entries need registry-detail repair: 20 `IX` interaction theses are
  declared in the atlas summary but missing detailed rows, and
  `WCT-TIMING-017`/`WCT-TIMING-018` are referenced outside the quick-reference
  table.
- 113 of 228 month x regime x CP cells have fewer than 30 rows, so stratified
  thesis testing must carry power flags.
- The monthly wind-rose prerequisite is now produced from pre-CP observations.
  Aggregate pre-CP obs counts are dominated by `N` (204,807), then `S`
  (87,444), `NE` (51,628), `SE` (20,163), `NW` (13,610), `SW` (12,660),
  `E` (6,738), and `W` (3,270).
- The cooling mechanism taxonomy is now produced from pre-CP observations using
  fractional-hour METAR deltas. Initial totals are `no_material_cooling`
  (19,513), `radiative_pre_dawn` (988), `southerly_frontal` (552),
  `ambiguous_cooling` (507), `post_dawn_advective` (158), and
  `insufficient_obs` (106).
- A regression test now protects against truncating half-hour METAR intervals to
  zero hours; this matters because false infinite/NaN cooling rates would make
  the cooling EDA dishonest.

## Onda 2E-Gate: Evidence-to-Decision Framework

Status: implemented and generated on 2026-06-07; active EDA backlog unblocked;
experiment-only Onda 4 baseline and repair work now open

Purpose: prevent the 251-thesis atlas and future EDA tables from becoming
archived evidence that the project ignores. Every EDA result must be translated
into an explicit project decision before it can affect regimes, features,
models, Onda 4 reruns, or Onda 3 planning.

Required artifacts:

- `reports/onda2e/evidence_decision_register.csv`
- `reports/onda2e/regime_design_queue.csv`
- `reports/onda2e/feature_candidate_queue.csv`
- `reports/onda2e/rejection_register.csv`
- `reports/onda2e/quarantined_baseline_register.csv`
- `reports/onda2e/onda2e_decision_report.md`

Current generated state:

- `evidence_decision_register.csv` has 250 rows: 245 active thesis decisions
  and 5 baseline-rule decisions.
- The 6 theses that require unavailable external data are removed from the
  active ADR-012 universe and recorded in
  `reports/onda2e/removed_external_theses.csv`.
- Current active decision counts: 48 `ADAPTED`, 4
  `PROMOTED_TO_REGIME_DESIGN`, 2 active `QUARANTINED_BASELINE`, 22
  `REJECTED`, 174 `SUPPORTED`, and 0 active `BLOCKED` thesis decisions.
- Implemented domain EDA feeding the gate now covers `TIMING`, `COOLING`,
  `FOEHN`, `WIND`, thesis-domain evidence, and regime architecture.
- Supported decisions are descriptive evidence only; they do not promote a
  production feature, model input, classifier, or regime ontology.
- Promoted regime-design items are `WCT-COOL-003`, `WCT-FOEHN-001`,
  `WCT-WIND-019`, and `WCT-REGIME-016`. They enter regime design review only.
- Adapted diagnostic comparators are `RULE_LATE_WARMING_FIXED_18`,
  `RULE_COOLING_FIXED_MINUS_2_C_PER_H`, and `RULE_FOEHN_SCORE_FIXED_60`.
  These are not production truth.
- Active quarantined decision rows are `REGIME_CLASSIFIER_CURRENT` and
  `RULE_ONDA2R_PHYSICAL_REGIME_FAMILY`.
- `quarantined_baseline_register.csv` still has 5 baseline comparator rows:
  current regime classifier, fixed 18:00 late-Tmax logic, fixed `-2 C/h`
  cooling threshold, fixed `foehn_score > 60`, and the Onda 2R physical regime
  family. This comparator register is intentionally broader than the two active
  `QUARANTINED_BASELINE` decision rows.
- `regime_design_queue.csv` has 9 investigation items: 5 baseline comparators
  plus `WCT-COOL-003`, `WCT-FOEHN-001`, `WCT-WIND-019`, and
  `WCT-REGIME-016`.
- `feature_candidate_queue.csv` is empty and `rejection_register.csv` has 22
  rows. No model feature, production classifier change, or production
  regime/model claim is promoted.
- `domain_eda_next_experiments.csv` has 0 rows because no active thesis remains
  blocked without a decision; future work proceeds through explicit queues.
- `reports/foundation-experiments/foundation_experiment_catalog_v1.csv` has 25
  experiment-only rows: 9 baseline, 11 regime, 4 threshold, and 1 feature
  experiment.
- `reports/foundation-experiments/foundation_experiment_results_v1.csv` has 25
  rows: 4 completed experiment rows and 21 `not_run` rows for catalog items
  without a v1 runner. After the v2.1 refresh, status counts are 4 `passed`
  and 21 `not_run`; every row is `production_status = EXPERIMENT_ONLY`.
  `BEXP-L2-MONTH-REGIME-001` passed with candidate MAE 1.5058 versus baseline
  MAE 1.8256, and `BEXP-L4-MONTH-CP-REGIME-001` passed with candidate MAE
  1.1768 versus baseline MAE 1.7523.
- The first two dead-regime probes now pass when fed the v2.1 comparison:
  `REXP-DEAD-MARITIME-001` and `REXP-DEAD-MIXED-001` both report
  `r2_dead_regimes = 0`. This does not promote residual/mixed labels as macro
  regimes; it records that v2.1 removed them from the production-eligible macro
  surface and preserved them as residual audit metadata.
- Regime Ontology v2 is now the active repair path for the candidate-family R2
  blocker. Generated 2026-06-08 artifacts include
  `reports/onda2e/regime_design_candidate_v2.csv`,
  `reports/regime-design/regime_candidate_assignments_v2.csv`,
  `reports/regime-design/regime_candidate_r2_validation_v2.csv`, and
  `reports/regime-design/regime_candidate_v1_v2_comparison.csv`.
- The v2 candidate has 96 `NOT_PRODUCTION` centroid rows and assigns 21,824
  feature rows into 3 macros: `macro_nw_continuum` 15,638,
  `macro_southerly_flow` 5,835, and `macro_light_marine_or_residual` 351.
- The v2 screen itself was not a pass. `macro_nw_continuum` and
  `macro_southerly_flow` passed R2 screening, but
  `macro_light_marine_or_residual` remained dead with 0/92 passing R2 rows.
  `regime_candidate_v1_v2_comparison.csv` therefore records
  `KEEP_IN_REGIME_DESIGN_REVIEW`, with all rows `EXPERIMENT_ONLY`.
- Regime Ontology v2.1 residual absorption is now generated. It removes
  `macro_light_marine_or_residual` from the R2 macro surface, reassigns its
  351 rows to the nearest physical macro, and preserves residual/maritime
  evidence as subtype/audit metadata. Generated artifacts include
  `reports/regime-design/regime_candidate_assignments_v2_1.csv`,
  `reports/regime-design/regime_candidate_r2_validation_v2_1.csv`, and
  `reports/regime-design/regime_candidate_v2_v21_comparison.csv`.
- v2.1 assigns 21,824 rows into two macros: `macro_nw_continuum` 15,879 and
  `macro_southerly_flow` 5,945. It absorbs 351 residual rows, has 0 invalid
  absorption targets, 0 v2.1 dead macros, and records
  `decision_update = READY_FOR_FULL_ONDA4_RERUN`. All v2.1 assignment rows are
  `NOT_PRODUCTION`; comparison and foundation-result rows are
  `EXPERIMENT_ONLY`.
- The full Onda 4 candidate rerun against
  `reports/regime-design/features_candidate_v2_1.parquet` has now passed with
  verdict `GO` in
  `reports/robustness-v2_1/2026-06-08-robustness-report.md`. The run used
  `--regime-set macro_nw_continuum,macro_southerly_flow`; R2 has 0 dead
  candidate macros.
- This validates Opcao A as a viable non-production candidate surface, but it
  does not start Onda 3. Onda C then ran as the required
  probabilistic classifiability/topology check.
- The corrected Onda C Regime Measurement Reset ran on 2026-06-08 using the
  audited physical meteorological feature basis. The audit artifacts are
  `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
  and `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`.
  It included 8 approved physical features, rejected `precip_pre_cp_sum` as
  constant, and did not use the forbidden unrestricted numeric fallback.
- Onda C first returned `KEEP_IN_REGIME_DESIGN_REVIEW` for v2.1; it did not
  unblock Onda 3 and could not bypass ADR-012 or Onda 4. The follow-up v2.2
  sprint restored calm/radiative as a protected macro, then re-ran R2 and
  Onda C as experiment-only artifacts.
- v2.2 assigns 21,824 rows into three macros: `macro_calm_radiative` 2,572,
  `macro_nw_continuum` 13,726, and `macro_southerly_flow` 5,526. The v2.2 R2
  screen blocks promotion because `macro_calm_radiative` has 0/92 passing R2
  rows.
- The v2.3 calm/radiative failure diagnostic has now been generated under
  `reports/regime-design/`. It records `CALM_RADIATIVE_VALIDATION_TARGET_GAP`:
  calm/radiative has 2,572 assignment rows, 825 unique days, smallest CP
  support of 502 rows, but R2 median `n_days` is only 27 and R2 pass rows are
  0/92. The next work is target/feature/ontology experiments, not Onda 3.
- `CEXP-CALM-RADIATIVE-001` has now generated
  `regime_calm_radiative_target_diagnostics_v1.csv/.md`. It contains 144
  train-window macro x month x CP target cells, including 48 calm/radiative
  cells. Calm/radiative has 20/48 underpowered cells, median p50 remaining
  warming of 3.5 C, median p90 remaining warming of 5.0 C, and median p50
  Tmax hour of 13:00. This suggests the macro has a distinct target profile but
  still needs calm-specific causal features before promotion.
- `CEXP-CALM-RADIATIVE-002` has now generated
  `regime_calm_radiative_feature_hypotheses_v1.csv/.md`. It screened 8
  train-window calm-specific feature hypotheses: 1 preliminary
  `CANDIDATE_SIGNAL` (`cloud_cover_suppression`), 4 `WEAK_SIGNAL`, 2
  `CONSTANT_FEATURE`, and 1 `UNDERPOWERED_FEATURE`. The output is
  `EXPERIMENT_ONLY`; it does not promote a feature, regime, Onda C, or Onda 3.
- `CEXP-CALM-RADIATIVE-002B` has now generated
  `regime_calm_radiative_cloud_signal_validation_v1.csv/.md`. It records
  `SURVIVES_CAUSAL_ROBUSTNESS_SCREEN`: 1,725 rows, overall slope -2.89,
  controlled slope -1.75, controlled retention 0.605, 4/4 CP cells and 25/25
  supported month x CP cells with negative slopes, and max proxy correlation
  0.340. `CEXP-CALM-RADIATIVE-003` demote/split was not triggered in this
  sprint.
- The Onda C rerun against v2.2 records `BLOCK_ONDA_C_PROMOTION` for the
  superseded 3-macro path. The later binary macro validation is the active Onda
  3 design-review entry point.

Allowed decision statuses:

- `SUPPORTED`
- `REJECTED`
- `ADAPTED`
- `BLOCKED`
- `PROMOTED_TO_REGIME_DESIGN`
- `PROMOTED_TO_FEATURE_CANDIDATE`
- `QUARANTINED_BASELINE`

Regime policy:

- The current regime classifier is a quarantined baseline, not final ontology.
- `late_warming`, fixed `18:00` late-Tmax definitions, fixed cooling thresholds,
  and fixed foehn thresholds are not production truth unless retained by the
  decision gate.
- New regime definitions must come from Wellington climatology: month, CP,
  wind sector/speed, cooling taxonomy, pressure/rain context, Tmax timing norms,
  sample-size power, and causal availability.
- Onda 2E is unblocked for experiment execution. The v2.1 candidate surface
  passed a full candidate Onda 4 rerun, but corrected Onda C kept regime design
  in review and the v2.2 calm/radiative restoration now blocks promotion. Onda C
  must return `READY_FOR_ONDA3_DESIGN_REVIEW` before Onda 3.
- Production promotion remains separate: the current production classifier is
  still quarantined until a future promotion gate replaces it explicitly.

ADR: `docs/decisions/012-evidence-to-decision-gate.md`
Report: `reports/onda2e/onda2e_decision_report.md`

## Onda 4: Robustness Hardening

Status: historical feature/regime robustness implemented; model robustness
review is the active next wave after Onda 3 baseline

Purpose: stress-test the Onda 2 feature-null foundation before Onda 3 models.
Onda 4 is not shadow trading and not financial readiness.

Latest v2.1 candidate checks:

- Per-year replication: PASS, 8 years with at least one passing feature.
- Regime sensitivity and dead-regime detection: PASS, 0 dead regimes under
  `macro_nw_continuum,macro_southerly_flow`.
- Causal re-audit of validated features: PASS, 0 violations.
- Drift trend of feature-null skill: PASS, Mann-Kendall p=0.5362 and no
  negative trend warning.
- Fresh G1-G5 gate re-run: PASS.
- Anti-nowcast lead-time check: PASS, evidence is not nowcast-only.
- Physical Tmax-hour stratification by regime and month: PASS, no fixed-CP
  artifact detected.
- Late-spike evidence pack for future model research: PASS, artifact produced.
- Late-Tmax risk baseline: PASS, month/regime q90 baseline exists.

Artifacts:

- `reports/robustness/2026-06-06-robustness-report.md`
- `reports/robustness/robustness_drift_snapshot.json`
- `reports/robustness/late_spike_candidates.json`
- `reports/robustness-v2_1/2026-06-08-robustness-report.md`
- `reports/robustness-v2_1/robustness_drift_snapshot.json`
- `reports/robustness-v2_1/late_spike_candidates.json`

Exit: the v2.1 candidate Onda 4 rerun passes. This cleared Opcao A's immediate
dead-regime blocker, but the corrected Onda C measurement reset kept regime
design in review and the v2.2 calm/radiative restoration now blocks promotion
because `macro_calm_radiative` is dead in R2. The older post-Onda 2R NO-GO
remains historical evidence that the quarantined production classifier should
not be treated as final.

## Onda 4M: Model Robustness Review

Status: first model review generated; next action is Onda 3 next model
iteration under experiment-only constraints

Purpose: review the first Onda 3 baseline model result before any further model
iteration can be treated as robust. This wave reads `reports/onda3/` and writes
separate experiment-only review artifacts under `reports/onda4-model/`.

Entry state:

- Onda 3 generated baseline artifacts under `reports/onda3/`.
- `onda3_decision_update_v1.csv` records
  `READY_FOR_ONDA4_MODEL_RERUN`.
- Train-mean null MAE is 2.8120; ridge challenger MAE is 1.3487.
- All Onda 3 outputs remain `EXPERIMENT_ONLY`.

Design:

- `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`

Plan:

- `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`

Generated review artifacts:

- `reports/onda4-model/onda4_model_input_audit_v1.csv/.md`
- `reports/onda4-model/onda4_model_gate_results_v1.csv/.md`
- `reports/onda4-model/onda4_model_slice_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_uncertainty_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_decision_update_v1.csv/.md`
- `reports/onda4-model/onda4_model_robustness_report_v1.md`

Gate policy:

- Onda 4M uses M1-M8 model-specific gates for input integrity, causal manifest
  safety, challenger lift, temporal robustness, slice robustness,
  uncertainty/abstention, anti-nowcast/model timing, and decision hygiene.
- M1-M8 are separate from the historical Onda 4 R1-R9 regime/feature-null
  robustness checks.
- Passing Onda 4M may only produce an experiment decision such as
  `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`; it does not approve production,
  deployment, market execution, EV, position sizing, or trading.

First review result:

- M1-M8 all pass.
- M3 records null MAE 2.8120, challenger MAE 1.3487, and lift 1.4632.
- M6 records residual absolute p50 1.0315 and p90 2.9818 with an abstention
  rule present.
- Decision status is `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Production status remains `EXPERIMENT_ONLY`.

## Regime Ontology v2.2: Calm/Radiative Restoration

Status: implemented as experiment-only; blocked by R2 and active Onda C

Purpose: restore `macro_calm_radiative` as a protected physical macro without
reviving `macro_light_marine_or_residual` as a production-eligible regime.

Artifacts:

- `reports/regime-design/regime_candidate_assignments_v2_2.csv`
- `reports/regime-design/regime_candidate_ontology_v2_2.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.csv`
- `reports/regime-design/regime_calm_radiative_reassignment_audit_v1.md`
- `reports/regime-design/regime_candidate_r2_validation_v2_2.csv`
- `reports/regime-design/regime_candidate_v21_v22_comparison.csv`
- `reports/regime-design/regime_candidate_v22_validation_report.md`
- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.md`
- `reports/regime-design/regime_v23_next_experiments.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.md`

Decision update:

- v2.2 restores `macro_calm_radiative` by a physical rule over the audited
  Onda 2E matrix: low wind plus at least two supporting signals among high
  humidity, low dewpoint depression, high cloud cover, and weak pre-CP slope.
- Macro support is `macro_calm_radiative` 2,572, `macro_nw_continuum` 13,726,
  and `macro_southerly_flow` 5,526.
- `macro_calm_radiative` has adequate sample support but fails R2 with 0/92
  passing rows, so v2.2 remains `KEEP_IN_REGIME_DESIGN_REVIEW`.
- v2.3 explains that failure as `CALM_RADIATIVE_VALIDATION_TARGET_GAP`, with
  R2 median `n_days` 27 for calm/radiative versus 210 for
  `macro_nw_continuum` and 110 for `macro_southerly_flow`. The next
  experiment queue is:
  `CEXP-CALM-RADIATIVE-001` target diagnostics,
  `CEXP-CALM-RADIATIVE-002` calm-specific feature hypotheses, and
  `CEXP-CALM-RADIATIVE-003` demote/split ontology comparison.
- `CEXP-CALM-RADIATIVE-001` is now complete. Its target-only audit shows
  calm/radiative has higher median remaining warming than the other macros
  across month x CP cells (`3.5 C` versus `2.0 C` for NW and `1.0 C` for
  southerly), but 20/48 calm cells remain underpowered. This does not unlock
  Onda 3; it prioritizes `CEXP-CALM-RADIATIVE-002`.
- `CEXP-CALM-RADIATIVE-002` is now complete as an experiment-only feature
  screen. It found only one preliminary candidate signal,
  `cloud_cover_suppression` (Pearson corr -0.318, slope -2.89), while
  `cloud_base_transparency` and `nocturnal_plateau_flag` were constant in the
  calm/radiative context.
- `CEXP-CALM-RADIATIVE-002B` is now complete. `cloud_cover_suppression`
  survives the current causal robustness screen as pre-CP cloud evidence, not a
  proxy/artifact: negative slope in every supported CP and month x CP stability
  cell, controlled slope retention 0.605, and max proxy correlation 0.340.
  This does not unlock Onda 3; it means CEXP-003 demote/split is not triggered
  by this signal failure condition.
- This is not a production classifier and does not overwrite
  `data/features.parquet`.

The cooling-rule experiment is diagnostic only. Under variants where cooling
cannot be the sole disruption trigger, 13,367 rows move out of
`southerly_disrupted` into `standard_nw`, `strong_nw_foehn`, or
`calm_radiative`. This is evidence for investigation, not a production
classifier change.

Intraday changes in wind, clearing, cooling, or warming are not a new regime
family. They are later day-state/risk features between already-known physical
regimes. Because the base regimes are still not clear enough to pass R2,
transition-risk modeling remains on hold.

## Onda C: Regime Classifiability

Status: complete; v2.2 blocked historically; binary macro validation is ready for Onda 3 design review

Purpose: run a non-production validation benchmark on the candidate regime
surface to verify classifiability, stability, and topological structure.

Artifacts:
- `reports/regime-classifiability/regime_classifiability_assignments_v1.csv`
- `reports/regime-classifiability/regime_classifiability_metrics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_comparison_v1.csv`
- `reports/regime-classifiability/regime_classifiability_diagnostics_v1.csv`
- `reports/regime-classifiability/regime_classifiability_report_v1.md`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
- `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`

Decision update:
- Corrected Onda C first ran on 2026-06-08 using the audited physical
  meteorological feature basis and kept v2.1 in
  `KEEP_IN_REGIME_DESIGN_REVIEW`.
- The active Onda C artifacts were then rerun against v2.2 with
  `macro_calm_radiative`, `macro_nw_continuum`, and `macro_southerly_flow` as
  protected macros.
- The audit included 8 approved physical features, rejected
  `precip_pre_cp_sum` as constant, and did not use the forbidden unrestricted
  numeric fallback.
- The v2.2 benchmark verdict was `BLOCK_ONDA_C_PROMOTION`; that result is now
  retained as historical evidence for the failed 3-macro path.
- The candidate comparison gate fails because v2.2 is already blocked by R2:
  `macro_calm_radiative` has 0/92 passing R2 rows.
- `distance_softmax_v22` improves low-confidence share versus v2, but remains
  weak: low confidence 0.8226, classifiability score 0.0539, stability 0.6154.
- The v2.3 threshold loop is superseded. The active unlock path is the regime
  deadlock pivot (`reports/onda2e/regime_deadlock_diagnosis_v1.md`).
- `macro_calm_radiative` is now an audit-only segment, not a production-blocking
  macro. Production-blocking set: `macro_nw_continuum`, `macro_southerly_flow`.
- Binary macro experiment (`macro_southerly_flow` vs `macro_non_southerly`) has
  now completed validation as an experiment-only candidate.
- `cloud_cover_suppression` baseline comparison is running as an independent
  experiment; 96 walk-forward rows generated (2024-2025, all 4 CPs).
- The binary macro validation records `READY_FOR_ONDA3_DESIGN_REVIEW` with
  stability 0.8089, temporal stability 0.9917, low confidence share 0.0000,
  and predictive assignment AUC 0.9886.
- This AUC is assignment separability, not direct Tmax predictive skill.
- `macro_non_southerly` remains weakly sensitive in R2: 3/92 passing rows versus
  47/92 for `macro_southerly_flow`.
- The AUC gate now blocks insufficient class-variation splits instead of
  fabricating a perfect score.
- Onda C remains non-production and did not write any Onda 3 model artifacts.

## Regime Deadlock Pivot

Status: PIVOT_ACCEPTED — 2026-06-08

The project formally abandoned the v2.2/v2.3/CEXP threshold-restoration loop as
the active Onda 3 unlock path. Evidence:

- `train_only_gmm` stability 0.0799 — morning METAR space has no stable
  3-macro cluster structure.
- 82% low-confidence share across all classifiers — most daily assignments are
  ambiguous.
- 0/92 R2 pass rows for `macro_calm_radiative` across all versions v2.0–v2.2.

Active path: Option C (audit demotion) + Option A (binary macro experiment) +
cloud-cover baseline comparison.

Artifacts:

- `reports/regime-design/regime_deadlock_pivot_decision_v1.csv/.md`
- `reports/regime-design/regime_audit_demotions_v1.csv/.md`
- `reports/regime-design/regime_deadlock_superseded_path_v1.csv`
- `reports/regime-design/regime_binary_macro_candidate_v1.csv/.md`
- `reports/regime-design/regime_binary_macro_assignments_v1.csv`
- `reports/regime-design/regime_binary_macro_r2_validation_v1.csv/.md`
- `reports/regime-design/regime_binary_macro_classifiability_v1.csv/.md`
- `reports/regime-design/regime_binary_macro_decision_update_v1.csv`
- `reports/regime-design/cloud_cover_baseline_experiment_v1.csv/.md` (96 rows)

Blocked actions:

- No v2.4 calm/radiative threshold tuning.
- No global R2 weakening.
- No cloudy/clear macro split as the active path.

## Onda 3: Models

Status: first baseline model generated; ready for experiment-only Onda 4 model
rerun review; production remains blocked

The first model wave must target predictive power, not market execution.

Entry state:

- Binary macro candidate passed the experiment-only design-review gate:
  `READY_FOR_ONDA3_DESIGN_REVIEW`.
- Onda 3 must start as a baseline-first model experiment, not a new regime
  ontology loop.
- Planned spec:
  `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`.
- Planned implementation:
  `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`.
- `macro_non_southerly` must be modeled with continuous features and slice
  diagnostics because its R2 sensitivity remains weak.

Generated 2026-06-09 baseline state:

- CLI: `python -m solarstorm onda3-baseline-model`.
- Artifacts:
  `reports/onda3/onda3_feature_manifest_v1.csv`,
  `reports/onda3/onda3_design_matrix_audit_v1.csv`,
  `reports/onda3/onda3_baseline_results_v1.csv`,
  `reports/onda3/onda3_challenger_results_v1.csv`,
  `reports/onda3/onda3_slice_diagnostics_v1.csv`,
  `reports/onda3/onda3_uncertainty_abstention_v1.csv`,
  `reports/onda3/onda3_decision_update_v1.csv`, and
  `reports/onda3/onda3_baseline_model_report_v1.md`.
- Train-mean null MAE is 2.8120 and ridge challenger MAE is 1.3487 on the
  first generated train/test split.
- Decision status is `READY_FOR_ONDA4_MODEL_RERUN`, with
  `production_status = EXPERIMENT_ONLY`.
- Missing numeric feature values are imputed from train-window means; the
  feature manifest still blocks full-day target/proxy columns.

Requirements:

- Beat the best feature-null at each eligible CP/lead-time slice.
- Report calibrated uncertainty.
- Learn when to abstain.
- Preserve causal firewall constraints.
- Evaluate by regime, month, lead time, and Tmax-hour bucket.
- Treat late spikes as a specific physical risk class.

Candidate inputs may include Open-Meteo/NWP in future work, especially to study
late spikes. Production deployment, EV, market pricing, and execution remain on
hold until a model passes its own predictive and uncertainty gates.

## On Hold

- Financial objective functions.
- EV and market pricing.
- Position sizing.
- Shadow trading.
- Live trading.
- Polymarket API integration.
- Production deployment.
