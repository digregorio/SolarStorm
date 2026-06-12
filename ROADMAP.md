# SolarStorm Project Roadmap

Living status tracker for the SolarStorm rewrite. See
`docs/decisions/010-onda-waves.md` for the wave methodology.

Last updated: 2026-06-12

## Project Focus

SolarStorm is a model-first intraday Tmax forecaster for NZWN. The current goal
is not a financial system. The current goal is a model foundation that can prove
real predictive skill, identify uncertainty, and stay out when it has no edge.

Financial execution, EV, position sizing, shadow trading, and Polymarket API
work are on hold until a production model passes its predictive gates.

Core rule: no regime, feature, model input, or robustness repair may be promoted
from EDA unless it passes the Evidence-to-Decision Gate in ADR-012. Descriptive
tables are evidence, not permission to proceed.

## Production Roadmap P0-P5 (Forensic v2, 2026-06-12)

The forensic investigation v2 (`reports/forensic-investigation-v2.md`)
supersedes the previous "next technical sprint order". Verified findings:

- The M3 train-mean null (MAE 2.812) is a strawman. The honest null
  `k_cp + train-only climatological remaining warming` scores MAE
  1.62/1.39/1.10/0.85 at CPs 20:00-23:00 UTC and beats Onda 3F at CP 23:00
  (0.850 vs 1.028) while nearly tying at CP 22:00.
- At CP 23:00, 26.1% of days have already realized Tmax and 62.0% have
  <= 1 C remaining; the M7 anti-nowcast gate is hardcoded PASS and the
  lead-time check requires only 1 day. Anticipation has never been proven.
- `k_cp` never reaches the model matrix (silently dropped by the allowlist
  filter because `features.parquet` lacks it), and 6.8-9.0% of the best
  Open-Meteo candidate predictions violate the physical floor
  `prediction >= k_cp`.
- Open-Meteo policies emit one prediction per day repeated across the four
  CPs, discarding intraday information at the CPs where nowcast dominates.
- The earlier `reports/forensic-investigation-report.md` mixed evidence from
  the quarantined old project; its G1/G2/G4 diagnoses do not apply to this
  repo. The `solarstorm/serving/`, `solarstorm/calib/`, and `scripts/` files
  from that session are unaudited drafts, not project infrastructure; they
  were moved to the gitignored `quarentena/` directory on 2026-06-12.

Phases (each gated; everything stays `EXPERIMENT_ONLY` until the exit gates
pass):

1. **P0 Honest evaluation harness — implemented/generated.** Honest null per
   CP, physical floor audit, remaining-warming strata, frozen gates H1-H4,
   persistence ablation, `honest-evaluation` CLI. First generated artifact:
   `reports/honest-evaluation/honest_evaluation_report_v1.md`; decision
   `BLOCK_MODEL_PROMOTION_HONEST_NULL` for Onda 3F, as pre-registered.
   Spec: `docs/superpowers/specs/2026-06-12-p0-honest-evaluation-design.md`.
   Plan: `docs/superpowers/plans/2026-06-12-p0-honest-evaluation.md`.
2. **P1 Horizon hybrid model — implemented/generated.** Target
   `remaining_warming`, reconstruction `tmax = k_cp + max(0, rw)`, k_cp as a
   real input, lead-aware NWP anchor blend, judged by the P0 gates plus the
   pre-registered same-row MAE comparison against
   `hybrid_local_only_covered_rows` on identical covered rows (spec success
   criterion 2). First generated artifact:
   `reports/onda3-hybrid/onda3_hybrid_model_report_v1.md`; decision
   `READY_FOR_P2_DISTRIBUTION_DESIGN`, with all outputs still
   `EXPERIMENT_ONLY`.
   Spec: `docs/superpowers/specs/2026-06-12-p1-horizon-hybrid-model-design.md`.
   Plan: `docs/superpowers/plans/2026-06-12-p1-horizon-hybrid-model.md`.
3. **P2 Calibrated distribution.** EMOS/NGR trained on CRPS (or Analog
   Ensemble) over the hybrid blend; ensemble members via the Open-Meteo
   Ensemble API; bracket probabilities from the CDF; PIT/coverage gates.
4. **P3 Late-spike risk and executable abstention.** Late-spike classifier
   (4.1% of days rise >= 4 C after CP 23:00, summer-skewed) and a
   `forecast_valid` rule replacing the current abstention string; thresholds
   frozen ex-ante per ADR-012.
5. **P4 Data expansion.** OM-M15 live forward collection extended with the
   Forecast + Ensemble APIs and the MetService Point Forecast API
   (forward-only; no deep history exists); UKMO Global / BOM ACCESS-G
   Previous Runs backfill from 2024.
6. **P5 Realized-EV harness and shadow trading.** Only after P0-P3 gates
   pass; minimum-edge threshold, fractional Kelly, stay-out default, one
   full summer season of shadow trading before any capital.

Exit gates from EXPERIMENT_ONLY: honest skill (beat the honest null at every
CP and on the `remaining_warming >= 2` stratum, in >= 2 folds plus mature
forward data), anticipation (skill survives persistence ablation at early
CPs), calibration (uniform PIT, IC80 coverage in [0.78, 0.84], CRPS below the
climatological null), physics (zero floor violations), executable abstention
with reported stay-out rate, and positive realized EV with non-negative CLV
across one shadow-traded season.

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

Status: binary-macro interaction model review generated for Onda 3D; next
action is another experiment-only Onda 3 model iteration, not production

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

Onda 3B review result:

- CLI:
  `python -m solarstorm onda4-model-review --onda3-dir ./reports/onda3-next --artifact-prefix onda3_next --output-dir ./reports/onda4-model-next`.
- Generated artifacts live under `reports/onda4-model-next/`.
- M1-M8 all pass.
- M3 records null MAE 2.8120, challenger MAE 1.2708, lift 1.5411, and
  challenger failures 0 across CP-specific rows.
- M6 records residual absolute p50 1.0805 and p90 3.1088 with an abstention
  rule present.
- Decision status is `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Production status remains `EXPERIMENT_ONLY`.

Onda 3C rolling review result:

- CLI:
  `python -m solarstorm onda4-model-review --onda3-dir ./reports/onda3-rolling --artifact-prefix onda3_rolling --output-dir ./reports/onda4-model-rolling`.
- Generated artifacts live under `reports/onda4-model-rolling/`.
- M1-M8 all pass.
- M3 records null MAE 2.9522, challenger MAE 1.2026, lift 1.7496, and
  challenger failures 0 across 12 year x CP challenger rows.
- M4 records rolling temporal diagnostics for test years `2023,2024,2025`.
- Decision status is `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Production status remains `EXPERIMENT_ONLY`.

Onda 3D interaction review result:

- CLI:
  `python -m solarstorm onda4-model-review --onda3-dir ./reports/onda3-interactions --artifact-prefix onda3_interaction --output-dir ./reports/onda4-model-interactions`.
- Generated artifacts live under `reports/onda4-model-interactions/`.
- M1-M8 all pass.
- M3 records null MAE 2.9522, challenger MAE 1.1726, lift 1.7796, and
  challenger failures 0 across 12 year x CP challenger rows.
- M4 records rolling temporal diagnostics for test years `2023,2024,2025`.
- M6 records residual absolute p50 1.0198 and p90 2.6165 with an abstention
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

Status: Onda 3D binary-macro interaction model iteration reviewed by Onda 4M;
ready for another experiment-only model iteration; production remains blocked

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

Generated 2026-06-09 Onda 3B state:

- CLI: `python -m solarstorm onda3-next-model-iteration`.
- Artifacts live under `reports/onda3-next/`.
- The model now evaluates ridge challengers separately for CPs `20:00`,
  `21:00`, `22:00`, and `23:00`.
- It uses train-only one-hot encoding for experiment-only
  `binary_macro_regime_label` context when available.
- All four CP-specific ridge challengers beat the CP train-mean null:
  MAE 1.3761 at `20:00`, 1.3120 at `21:00`, 1.1981 at `22:00`, and
  1.1973 at `23:00`, versus null MAE 2.8120 for each CP.
- Decision status is `READY_FOR_ONDA4_MODEL_RERUN`, with
  `production_status = EXPERIMENT_ONLY`.

Requirements:

- Beat the best feature-null at each eligible CP/lead-time slice.
- Report calibrated uncertainty.
- Learn when to abstain.
- Preserve causal firewall constraints.
- Evaluate by regime, month, lead time, and Tmax-hour bucket.
- Treat late spikes as a specific physical risk class.

The follow-up Onda 4M model robustness review of `reports/onda3-next/` has
now run under `reports/onda4-model-next/`. The next allowed action is another
experiment-only Onda 3 model iteration, not production deployment.

Generated 2026-06-09 Onda 3C rolling temporal state:

- CLI: `python -m solarstorm onda3-rolling-model-iteration --test-years 2023,2024,2025`.
- Artifacts live under `reports/onda3-rolling/`.
- The model reruns CP-specific ridge challengers in rolling annual splits for
  test years 2023, 2024, and 2025.
- All 12 year x CP ridge challenger rows beat their train-mean nulls.
- Decision status is `READY_FOR_ONDA4_MODEL_RERUN`, with
  `production_status = EXPERIMENT_ONLY`.
- The follow-up Onda 4M review under `reports/onda4-model-rolling/` passes
  M1-M8 and records temporal diagnostics for `2023,2024,2025`.

Generated 2026-06-09 Onda 3D interaction state:

- CLI: `python -m solarstorm onda3-interaction-model-iteration --test-years 2023,2024,2025`.
- Artifacts live under `reports/onda3-interactions/`.
- The model keeps the binary macro surface as the structural switch and adds
  continuous x macro interactions for `foehn_score` and
  `cloud_cover_suppression`.
- Interaction features:
  `foehn_score_x_macro_non_southerly`,
  `foehn_score_x_macro_southerly_flow`,
  `cloud_cover_suppression_x_macro_non_southerly`, and
  `cloud_cover_suppression_x_macro_southerly_flow`.
- Mean MAE delta versus the Onda 3C no-interaction rolling surface is
  -0.0300; all 12 year x CP challenger rows improve versus the no-interaction
  challenger.
- Decision status is `READY_FOR_ONDA4_MODEL_RERUN`, with
  `production_status = EXPERIMENT_ONLY`.
- The follow-up Onda 4M review under `reports/onda4-model-interactions/`
  passes M1-M8.

Interpretation:

- The current evidence supports the two-regime design as a structural switch,
  not as a complete descriptive taxonomy for Wellington.
- The predictive gain came from continuous features and their binary-macro
  interactions, not from adding a third discrete regime.
- Open-Meteo/NWP integration is now the active experiment track. Further
  handcrafted local interactions stay paused until the provider calibration
  and calibrated nested-validation sprints resolve whether NWP adds stable
  predictive skill.

Generated 2026-06-09 Onda 3E train-start sensitivity state:

- CLI: `uv run tmax onda3-train-start-sensitivity --test-years 2023,2024,2025`.
- Artifacts live under `reports/onda3-train-start-sensitivity/`.
- The experiment compares `legacy_2009_start` (`train_start = 2009-04-23`) and
  `continuous_2012_start` (`train_start = 2012-01-01`) using the Onda 3D
  binary-macro interaction surface.
- Weighted challenger MAE is 1.1726 for `legacy_2009_start` and 1.1705 for
  `continuous_2012_start`, a small 2012-start gain of 0.0021 MAE.
- Daily `any_cp_exact_pct` is 45.1642% for `legacy_2009_start` and 45.0730%
  for `continuous_2012_start`, a 2012-start loss of 0.0912 percentage points.
- Final `23:00` exact rate is 29.9270% for `legacy_2009_start` and 29.8358%
  for `continuous_2012_start`.
- Decision status is `KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION`.
- Open-Meteo/NWP is not integrated.
- Production status remains `EXPERIMENT_ONLY`.

Generated 2026-06-09 Onda 3F pooled temporal/regime state:

- CLI: `uv run tmax onda3-pooled-model-iteration --test-years 2023,2024,2025`.
- Artifacts live under `reports/onda3-pooled/`.
- The experiment trains one pooled ridge challenger per test year with
  `cp = ALL`, while retaining original CP values in line-level predictions and
  bracket/slice diagnostics.
- CP values are normalized to canonical `HH:MM` before cyclic encoding and
  before joining binary macro assignments, so `Time`-typed feature checkpoints
  do not collapse the CP signal or lose regime labels.
- Added cyclic temporal inputs: `cp_sin`, `cp_cos`, `month_sin`, `month_cos`,
  `doy_sin`, and `doy_cos`.
- Weighted challenger MAE is 1.0619, versus 1.1726 for Onda 3D/legacy Onda 3E
  and 1.1705 for continuous-2012 Onda 3E.
- Daily `any_cp_exact_pct` is 44.4343%, lower than Onda 3E's roughly 45.1%,
  while final `23:00` exact rate is 31.4781%, higher than Onda 3E's roughly
  29.9%.
- Decision status is `READY_FOR_ONDA3_AUDIT_COMPARISON`.
- Invalid requested test years with no train/test fold now block cleanly as
  `KEEP_IN_ONDA3_EXPERIMENT_REVIEW` instead of raising a schema error.
- Open-Meteo/NWP is not integrated.
- Production status remains `EXPERIMENT_ONLY`.

Generated 2026-06-09 Onda 3G audit comparison state:

- CLI: `uv run tmax onda3-audit-comparison`.
- Artifacts live under `reports/onda3-audit-comparison/`.
- The audit compares Onda 3D, Onda 3E legacy 2009-start, Onda 3E
  continuous-2012-start, and Onda 3F from persisted local-data predictions; it
  does not train a new model.
- Versus Onda 3D, Onda 3F changes MAE by -0.1107, daily `any_cp_exact_pct` by
  -0.7299 percentage points, and final `23:00` exact rate by +1.5511 percentage
  points.
- Onda 3F is the MAE winner overall and within both binary macro regimes, but
  the headline exact-bracket tradeoff means Onda 3D remains an important
  reference surface.
- Post-review hardening is included: Onda 3G recomputes all bracket columns
  from `actual`/`prediction`, requires all four canonical model surfaces, blocks
  duplicate `date_local, cp` feature joins, and defines feature top-quartile
  slices as top-25% row cardinality inside the audited prediction universe.
- Decision status is `CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION`.
- Open-Meteo/NWP is not integrated.
- Production status remains `EXPERIMENT_ONLY`.

Generated 2026-06-09 Onda 3H nested validation state:

- CLI: `uv run tmax onda3-nested-validation --test-years 2023,2024,2025 --train-start 2012-01-01`.
- Artifacts live under `reports/onda3-nested-validation/`.
- The nested harness compares Onda 3D and Onda 3F on identical outer folds:
  validation uses train years ending at `Y-2`, then the selected design is
  refit through `Y-1` before testing on `Y`.
- Validation selected Onda 3F for all three outer folds: 2023, 2024, and 2025.
- Selected test MAE by year: 2023 = 1.0399, 2024 = 1.0704, 2025 = 1.0770.
  Mean selected test MAE is 1.0624 versus 1.1705 for always using Onda 3D.
- Selected daily `any_cp_exact_pct` is 44.9315% in 2023, 43.7158% in 2024,
  and 43.8356% in 2025. Selected final `23:00` exact rate is 31.7808%,
  31.1475%, and 30.4110%, respectively.
- Post-review hardening is included: binary macro assignments are required for
  the CLI, feature selection now uses an explicit Onda 3H allowlist instead of
  the permissive generic manifest, and `cp23` metrics expose denominator fields
  before using `23:00` exact rate as a tie-break guardrail.
- Decision status is `PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS`.
- Open-Meteo/NWP is not integrated.
- Production status remains `EXPERIMENT_ONLY`.

Pre-Open-Meteo model sequence:

1. **Onda 3E train-start sensitivity - completed.** The generated result above
   keeps both train starts until nested validation because the 2012-start MAE
   gain is too small and trades off against exact-bracket performance. Spec:
   `docs/superpowers/specs/2026-06-09-onda3e-train-start-sensitivity-design.md`.
   Implementation plan:
   `docs/superpowers/plans/2026-06-09-onda3e-train-start-sensitivity.md`.
2. **Onda 3F pooled temporal/regime model - completed.** The generated result
   improves MAE materially and improves the final `23:00` exact rate, but loses
   daily `any_cp_exact`; it therefore advances to audit comparison rather than
   production. Spec:
   `docs/superpowers/specs/2026-06-09-onda3f-pooled-temporal-regime-design.md`.
   Implementation plan:
   `docs/superpowers/plans/2026-06-09-onda3f-pooled-temporal-regime.md`.
3. **Onda 3G audit comparison against Onda 3D - completed.** The generated
   result carries both Onda 3D and Onda 3F into nested validation because Onda
   3F materially improves MAE and final `23:00` exact rate, but loses daily
   `any_cp_exact`. Spec:
   `docs/superpowers/specs/2026-06-09-onda3g-audit-comparison-design.md`.
   Implementation plan:
   `docs/superpowers/plans/2026-06-09-onda3g-audit-comparison.md`.
4. **Onda 3H nested validation decision - completed.** The generated result
   promotes nested walk-forward as the model-selection harness before
   Open-Meteo/NWP integration. Onda 3F is selected by validation in all three
   outer folds, but the result remains `EXPERIMENT_ONLY` and does not unlock
   production. Spec:
   `docs/superpowers/specs/2026-06-09-onda3h-nested-validation-design.md`.
   Implementation plan:
   `docs/superpowers/plans/2026-06-09-onda3h-nested-validation.md`.

Open-Meteo integration gate:

- Open-Meteo/NWP integration remains gated by
  `open-meteo-availability-audit`, source eligibility, and nested validation.
  Every artifact remains `EXPERIMENT_ONLY`.
- The availability-first pass created source taxonomy, historical availability
  probes, CP-causal run selection, blocked-source register, and decision
  artifacts under `reports/open-meteo-availability/` and
  `reports/open-meteo-availability-live-smoke/`.
- The original Open-Meteo feature source remains
  `previous_runs_gfs_temperature`: endpoint `previous_runs`, model
  `gfs_seamless`, causal class `fixed_lead_forecast`. It is preserved in
  `data/open_meteo_features.parquet` as the GFS-only pilot artifact.
- The expanded multi-provider Open-Meteo feature table is now generated under
  `data/open_meteo_multi_provider_features.parquet`. It is a long-format,
  provider-keyed Previous Runs table, not yet a calibrated model feature set.
- Historical Weather remains blocked as reanalysis, Historical Forecast remains
  audit-only because it lacks per-row CP-causal run metadata, Forecast API is
  forward-collection only for backtest purposes, and Single Runs remains blocked
  until its endpoint/model request contract succeeds.
- Open-Meteo causal feature integration is implemented as experiment-only.
  `open-meteo-fetch` writes a raw response cache for feature-eligible sources,
  and `open-meteo-build-features` writes `data/open_meteo_features.parquet`
  only after the decision artifact allows the source.
- The daily all-CP Open-Meteo pilot under
  `reports/onda3-open-meteo-pilot-daily-all-cp/` improved same-row MAE versus
  the local-only reference by -0.2801 on the covered 2024-2025 pilot surface.
  This is a promising experiment result, not production approval.
- The Open-Meteo nested validation run under
  `reports/onda3-open-meteo-nested-validation-daily-all-cp/` selected the
  Open-Meteo-augmented Onda 3F candidate in the only valid outer fold. Test
  2025 MAE was 0.8508 versus 1.0809 for the local-only candidate on identical
  covered rows, and test 2025 daily `any_cp_exact_pct` was 51.78% versus
  46.03%. The decision is
  `PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`.
- The current Open-Meteo result is still coverage-limited: because usable
  features begin in 2023, nested validation has only one valid outer fold. The
  project must not treat this as a final model-selection verdict.
- OM-M1 multi-provider availability is now implemented. The plan-only artifacts
  live under `reports/open-meteo-multi-provider-availability/`, and the bounded
  live-smoke artifacts live under
  `reports/open-meteo-multi-provider-availability-live-smoke/`. The live smoke
  found `previous_runs` request success for `gfs_seamless`, `ecmwf_ifs025`,
  `ecmwf_aifs025_single`, `icon_seamless`, `gem_global`, and `jma_seamless`
  on the sampled 2024/2025 dates, while `single_runs` still returns HTTP 400
  and remains blocked by request contract.
- OM-M2 provider error atlas is now implemented under
  `reports/open-meteo-provider-error-atlas/`. Because the historical feature
  table currently contains only `gfs_seamless` Previous Runs rows, the first
  atlas measures NOAA/GFS only: 4,304 provider-error rows and 198 metric rows.
  Overall CP-sliced GFS Previous Runs MAE is 1.4207 C with signed bias
  -1.2018 C and exact-bracket rate 15.24%. By binary macro regime, MAE is
  1.5589 C for `macro_non_southerly` and 1.0382 C for
  `macro_southerly_flow`.
- OM-M3 historical multi-provider Previous Runs feature expansion is now
  implemented. The generated table covers 2023-01-01 through 2025-12-31,
  has 26,304 provider-keyed rows, 1,096 dates, four CPs, and six provider
  families: `NOAA_GFS`, `ECMWF_IFS`, `ECMWF_AIFS`, `DWD_ICON`, `ECCC_GEM`,
  and `JMA_GSM`. All rows remain `EXPERIMENT_ONLY`.
- The provider error atlas has been recalculated on the OM-M3 table under
  `reports/open-meteo-provider-error-atlas-multi-provider/`. The recalculated
  dataset has 18,440 non-null provider-error rows and 873 metric rows. Overall
  raw provider MAE ranks `icon_seamless` best at 1.0844 C, then `gem_global`
  at 1.1674 C, `ecmwf_ifs025` at 1.3987 C, `gfs_seamless` at 1.4207 C,
  `ecmwf_aifs025_single` at 1.7495 C, and `jma_seamless` at 1.7867 C. The
  atlas shows broad cold bias across providers, so signed-bias calibration is
  now a justified next experiment.
- OM-M4 family-deduplicated provider calibration is now implemented under
  `reports/open-meteo-provider-calibration/`. It generated 26,224 candidate
  rows across six experiment-only candidates:
  `om_gfs_previous_runs_raw`, `om_family_mean_raw`,
  `om_family_median_raw`, `om_family_inverse_mae_weighted`,
  `om_family_recent_bias_corrected`, and
  `om_family_regime_bias_corrected`. The best overall calibration-table
  candidate is `om_family_recent_bias_corrected`, with MAE 0.8225 C, signed
  bias -0.2741 C, and exact-bracket rate 38.41%. This is a calibration
  artifact, not a final model-selection decision.
- OM-M5 calibrated nested validation is now implemented under
  `reports/onda3-open-meteo-calibrated-nested-validation/`. It compares
  local-only Onda 3F, current GFS-augmented Onda 3F, raw GFS Previous Runs,
  and calibrated multi-provider candidates on identical covered rows. With the
  strict common-row requirement, only one outer fold is valid. Validation
  selects `om_family_recent_bias_corrected`; 2025 test MAE is 0.8258 C versus
  0.7630 C for current GFS-augmented Onda 3F, 1.0714 C for local-only Onda 3F,
  and 1.4227 C for raw GFS Previous Runs. Decision status is
  `KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW`, so no final model
  promotion, production, EV, pricing, shadow trading, or execution work is
  unlocked.
- OM-M6 calibrated error forensics is now implemented under
  `reports/open-meteo-forensics/`. It confirmed that
  `om_family_recent_bias_corrected` is unstable rather than uniformly bad:
  paired 2024-2025 same-row MAE was 0.7726 C versus 0.7610 C for
  `open_meteo_augmented_onda3f`, exact bracket was 40.45% versus 41.75%, and
  the critical failure was `2025|macro_non_southerly` with MAE delta
  +0.1065 C and exact delta -6.47 pp versus the augmented baseline.
- OM-M7 stabilized calibration is now implemented under
  `reports/open-meteo-provider-calibration-stabilized/`. It adds
  `om_family_month_bias_corrected` and
  `om_family_season_bias_corrected`, plus
  `open_meteo_stabilized_calibration_support_v1.csv`. All rows remain
  `EXPERIMENT_ONLY`. The new `season` candidate is the only stabilized
  candidate close enough to continue review: full calibration-table MAE is
  0.8791 C, worse than recent-bias 0.8225 C but with a less severe paired
  2024-2025 trade-off once nested predictions are compared.
- OM-M8 defensive selection is now implemented under
  `reports/onda3-open-meteo-defensive-selection/`. The selector mode
  `validation_mae_then_non_southerly_guard_then_cp23` emits
  `onda3_open_meteo_defensive_selection_guardrail_v1.csv` and blocks
  candidates that degrade validation `macro_non_southerly` versus
  `open_meteo_augmented_onda3f`. On the available strict common-row fold,
  validation still lets `om_family_recent_bias_corrected` through because its
  2024 `macro_non_southerly` validation slice looks strong; the rule therefore
  does not catch the 2025 drift failure.
- OM-M8B stabilized forensics is generated under
  `reports/open-meteo-forensics-stabilized/`, comparing
  `om_family_season_bias_corrected` to `open_meteo_augmented_onda3f` on the
  same paired 2024-2025 surface. The stabilized season candidate nearly ties
  overall MAE, 0.7619 C versus 0.7610 C, and improves exact bracket by
  +0.81 pp. However it fails the success gate because 2025 MAE worsens by
  +0.0200 C and `2025|macro_non_southerly` exact drops by -2.55 pp, even
  though the `macro_non_southerly` MAE delta stays within the +0.025 C guard.
- OM-M9 decision: `KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE`.
  Stabilized calibration is not promoted. It is better than the earlier
  recent-bias candidate for exact-bracket balance, but it does not beat the
  augmented baseline by the required overall MAE or exact-bracket gates while
  preserving `macro_non_southerly` stability. Current production status remains
  `EXPERIMENT_ONLY`.
- OM-M10 coverage/fold expansion is now implemented under
  `reports/open-meteo-coverage-expansion/`. The strict common-row audit shows
  current observed Open-Meteo coverage spans 2023-01-01 through 2025-12-31 with
  1,076 common dates and 4,304 common `(date_local, cp)` rows, producing only
  one valid outer fold. A counterfactual causal Previous Runs history beginning
  2022-01-01 would produce two valid outer folds for test years 2024 and 2025
  on 6,460 local feature-key rows. Alternate fixed leads over the current cache
  do not expand dates, and Single Runs remains blocked by request contract
  after 24/24 sampled probes returned HTTP 400. Decision:
  `COVERAGE_EXPANSION_REQUIRES_2022_HISTORY`.
- OM-M11 historical backfill feasibility and live backfill are now implemented
  without overwriting the existing Open-Meteo feature tables. The dry-run
  artifact under `reports/open-meteo-2022-backfill-feasibility/` records
  `OPEN_METEO_2022_BACKFILL_FEASIBILITY_READY`. The live 2022 Previous Runs
  backfill wrote `data/open_meteo_multi_provider_features_2022.parquet` with
  8,760 rows, 365 dates, four CPs, six provider families, and
  `OPEN_METEO_MULTI_PROVIDER_FEATURES_READY`. The existing
  `data/open_meteo_features.parquet` and
  `data/open_meteo_multi_provider_features.parquet` remain intact.
- OM-M12 two-fold nested refresh is now generated on expanded 2022-2025
  surfaces. New inputs are
  `data/open_meteo_multi_provider_features_2022_2025.parquet` with 35,064
  rows and `data/open_meteo_features_2022_2025.parquet` with 5,844 rows. The
  refreshed coverage audit under `reports/open-meteo-coverage-expansion-2022-2025/`
  records `CURRENT_COVERAGE_SUPPORTS_TWO_STRICT_FOLDS` with 1,441 common dates,
  5,764 strict common rows, and two valid outer folds. The refreshed defensive
  nested validation under `reports/onda3-open-meteo-defensive-selection-2022-2025/`
  records `PROMOTE_CALIBRATED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`:
  selected mean test MAE is 0.7824 versus 0.8244 for always using
  `open_meteo_augmented_onda3f`, 1.0574 for local-only Onda 3F, and 1.4265
  for raw GFS Previous Runs. All outputs remain `EXPERIMENT_ONLY`.
- OM-M13 expanded-surface decision review is now implemented under
  `reports/open-meteo-expanded-decision-review-2022-2025/`. It compares the
  nested-selected policy, always-season, always-recent, and always-augmented
  policies across overall, year, month, CP, binary macro regime, year-regime,
  and month-CP slices. The explicit decision is
  `PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`: the selected
  policy improves MAE to 0.7835 from 0.8239 for always-augmented and improves
  exact bracket by +1.30 pp, with no binary-macro MAE degradation. The review
  also records that `always_season` is the strongest global policy on the
  observed surface at MAE 0.7616, so the promotion is to the next experiment
  iteration, not a final baseline or production promotion.
- OM-M14 live-forward Forecast API collection is now implemented in safe
  fixture-mode under `reports/open-meteo-forward-collection/`. The new module
  `solarstorm/open_meteo/_forward_collection.py` normalizes forward Forecast
  API rows, records `available_time_utc`, computes `cp_utc`, blocks rows that
  fail `available_time_utc <= cp_utc`, rejects duplicate collection keys,
  keeps unsettled target dates as `pending`, provides a maturity transition,
  filters forward rows out of nested validation until `mature`, and builds
  endpoint/model/horizon availability audits. The CLI
  `open-meteo-forward-collection` writes raw response cache metadata,
  normalized provider-feature parquet, maturity/causality/availability audits,
  duplicate-key report, and a markdown report. The current generated smoke row
  remains `pending` and `EXPERIMENT_ONLY`.
- The OM-M14 design remains documented in
  `docs/superpowers/specs/2026-06-11-open-meteo-forecast-forward-collection-design.md`
  with its TDD implementation plan in
  `docs/superpowers/plans/2026-06-11-open-meteo-forecast-forward-collection.md`.
  It defines the unique collection key, CP-causal availability gate,
  pending-to-mature lifecycle, duplicate rejection, raw cache, normalized
  provider-feature table, and endpoint/model/horizon availability audit.

Direction lock for the next Open-Meteo wave:

1. Do not add more local handcrafted interactions until the Open-Meteo source
   question is resolved.
2. Do not call the current Open-Meteo feature set a production ensemble. The
   project now has family-deduplicated and shrinkage-calibrated experiment
   candidates, but nested validation leaves them in experiment review because
   the strict common covered surface has only one valid outer fold.
3. Preserve both Open-Meteo tables: `data/open_meteo_features.parquet` remains
   the GFS-only pilot input, while
   `data/open_meteo_multi_provider_features.parquet` is the provider-keyed
   OM-M3 input for calibration experiments.
4. Use the downloaded GitHub/quarantine projects as design references only,
   especially their Open-Meteo multi-model parsing, model-family deduplication,
   and recent signed-bias calibration patterns. Do not import their production
   or trading assumptions.
5. Treat the recalculated multi-provider atlas as the calibration baseline:
   MAE, RMSE, signed bias, exact bracket, month, CP, and binary macro regime
   slices are required in every calibration report.
6. Coverage expansion has now been materialized for 2022-2025. The next NWP
   work must be decision review and robustness on the two-fold expanded
   surface, not another calibration formula.
7. Production deployment, EV, market pricing, and execution remain on hold
   until a model passes predictive, uncertainty, causality, and coverage gates.

Sprint status:

- Sprint OM-M1: multi-provider availability and request-contract audit -
  implemented.
- Sprint OM-M2: provider error/bias atlas on causal historical rows -
  implemented first for GFS-only history, then recalculated on the OM-M3
  multi-provider table.
- Sprint OM-M3: historical multi-provider Previous Runs feature expansion -
  implemented. It wrote
  `data/open_meteo_multi_provider_features.parquet` without mutating
  `data/features.parquet` or the current GFS-only
  `data/open_meteo_features.parquet`.
- Sprint OM-M4: family-deduplicated ensemble and signed-bias calibration -
  implemented. It writes `reports/open-meteo-provider-calibration/` and keeps
  all outputs `EXPERIMENT_ONLY`.
- Sprint OM-M5: nested validation of calibrated Open-Meteo candidates against
  local-only Onda 3F and current GFS Previous Runs augmentation - implemented
  and kept in experiment review because only one strict common-row outer fold
  is valid.
- Sprint OM-M6: calibrated error forensics - implemented. It writes
  `reports/open-meteo-forensics/` and identifies year/regime drift as the
  reason calibrated candidates trail the augmented baseline.
- Sprint OM-M7A: monthly and seasonal stabilized calibration candidates -
  implemented. It writes
  `reports/open-meteo-provider-calibration-stabilized/`.
- Sprint OM-M7B: stabilized calibration support audit - implemented. It writes
  `open_meteo_stabilized_calibration_support_v1.csv` and flags support or
  adjustment risks.
- Sprint OM-M8A: defensive non-southerly selector - implemented. It writes
  `onda3_open_meteo_defensive_selection_guardrail_v1.csv` under
  `reports/onda3-open-meteo-defensive-selection/`.
- Sprint OM-M8B: stabilized nested revalidation and forensics refresh -
  implemented. It writes `reports/onda3-open-meteo-defensive-selection/` and
  `reports/open-meteo-forensics-stabilized/`.
- Sprint OM-M9: decision gate - implemented. Decision is
  `KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE`.
- Sprint OM-M10: coverage/fold expansion audit - implemented. Decision is
  `COVERAGE_EXPANSION_REQUIRES_2022_HISTORY`; current coverage has one valid
  strict common-row outer fold, while a causal Previous Runs backfill from
  2022 would create two.
- Sprint OM-M11: historical backfill feasibility and live 2022 backfill -
  implemented. It writes `reports/open-meteo-2022-backfill-feasibility/`,
  `reports/open-meteo-multi-provider-features-2022/`, and
  `data/open_meteo_multi_provider_features_2022.parquet`.
- Sprint OM-M12: two-fold nested refresh - implemented. It writes expanded
  2022-2025 feature surfaces and refreshed atlas, calibration, nested,
  forensics, and coverage artifacts under `reports/*-2022-2025/`.
- Sprint OM-M13: expanded-surface decision review - implemented. Decision is
  `PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`; artifacts
  are under `reports/open-meteo-expanded-decision-review-2022-2025/`.
- Sprint OM-M14: forward collection implementation - implemented in
  fixture-mode. It writes `reports/open-meteo-forward-collection/` and keeps
  rows out of validation until they become mature.

Next technical sprint order from current state (superseded on 2026-06-12 by
the Production Roadmap P0-P5; the OM items below are folded into P4):

1. **P0 honest evaluation harness** (see Production Roadmap P0-P5). All new
   model claims must be scored against the honest k_cp+climatology null
   before any further Open-Meteo iteration.
2. **P1 horizon hybrid model** judged by the P0 gates.
3. **OM-M15 live-forward collection scheduler** (now P4 item 1). Add the
   explicit `--live` collector/scheduler around the OM-M14 contract, with
   retry metadata and duplicate-key protection, extended with the Forecast +
   Ensemble APIs and the MetService Point Forecast API. Collected rows remain
   `pending` until labels settle.
4. **Expanded calibrated model iteration** (now folded into P1/P2). Carry the
   OM-M13 promoted path into the hybrid iteration; include both the
   nested-selected policy and `always_season` as anchor candidates.
5. **Calibration freeze.** Do not add another calibration formula until the
   P1 hybrid and forward collection identify a specific unresolved failure
   mode.
6. **Decision freeze remains active.** No production, EV, pricing, shadow
   trading, or execution work starts before the P0-P3 exit gates pass.

Detailed sprint guidance lives in
`docs/superpowers/plans/2026-06-10-open-meteo-multi-provider-calibration-sprints.md`
for OM-M1 through OM-M5 and
`docs/superpowers/plans/2026-06-10-open-meteo-coverage-expansion-next-sprints.md`
for OM-M11 onward.

## On Hold

- Financial objective functions.
- EV and market pricing.
- Position sizing.
- Shadow trading.
- Live trading.
- Polymarket API integration.
- Production deployment.
