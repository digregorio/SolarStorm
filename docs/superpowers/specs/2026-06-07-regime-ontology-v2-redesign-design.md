# Regime Ontology v2 Redesign Design

Status: approved for implementation planning
Date: 2026-06-07

## Goal

Redesign the SolarStorm regime ontology so regime evidence from Onda 2E can be
used without collapsing k=6 local structure into underpowered flat global
families. The output must be a non-production `Regime Ontology v2` candidate
that can be validated against Onda 4 R2 before any Onda 3 model work resumes.

## Context

The current regime stack has two different failures.

First, the Onda 2R heuristic classifier is degenerate. The current
`southerly_disrupted` label absorbs 17,308 of 21,824 feature rows, and the
trigger audit shows 16,382 of those rows are caused by `cooling` rather than a
physical southerly or precipitation trigger. The cooling-rule diagnostic shows
that removing cooling as a standalone trigger redistributes 8,570 rows to
`standard_nw`, 2,746 to `strong_nw_foehn`, and 2,051 to `calm_radiative`.

Second, the Onda 2E candidate v1 solves the old heuristic dominance only by
creating a new flat-family problem. The EDA sweep supports k=6 in each of the
16 month/season strata, but the candidate interpretation compresses 96 local
clusters into 4 global families:

- `candidate_nw_or_foehn`: 15,638 assignment rows and R2 PASS.
- `candidate_southerly_disrupted`: 5,835 assignment rows and R2 PASS.
- `candidate_mixed_or_transition`: 320 assignment rows and R2 DEAD.
- `candidate_maritime_cloudy`: 31 assignment rows and R2 DEAD.

The failure point is therefore not simply "wrong k". It is the projection from
local weather-state structure into a flat global ontology. `mixed_or_transition`
is a boundary state, not a stable macro-regime. `maritime_cloudy` is too sparse
as a global family in v1.

## Scientific Basis

This design follows four principles from the weather-regime literature:

- Michelangeli, Vautard, and Legras (1995) compare recurrent weather regimes
  with quasi-stationary regimes and emphasize reproducibility of regime
  structure, not only variance reduction.
- Kidson (2000) defines New Zealand synoptic types as a fine weather-type layer
  that can be grouped into broader weather regimes. This supports a hierarchy
  rather than a single flat label set.
- Christiansen (2007) shows that estimating the number of atmospheric
  circulation regimes with clustering is nontrivial and should be tested
  against surrogate or validation procedures rather than accepted from one
  criterion.
- Falkena et al. (2022) show that regime assignment can be probabilistic,
  which is useful when observations are close to transition boundaries.

References:

- Michelangeli et al. 1995:
  https://doi.org/10.1175/1520-0469(1995)052<1237:WRRAQS>2.0.CO;2
- Kidson 2000:
  https://doi.org/10.1002/(sici)1097-0088(20000315)20:3<299::aid-joc474>3.0.co;2-b
- Christiansen 2007:
  https://doi.org/10.1175/JCLI4107.1
- Falkena et al. 2022:
  https://arxiv.org/abs/2206.11576

## Design Decision

Implement `Regime Ontology v2` as a hybrid hierarchy with probabilistic latent
components:

1. **Macro regime**
   A small, causal, discrete top-level label used for Onda 4 R2 and other gates.
   Macro regimes must have enough support to be validated by CP and year.

2. **Latent component / subtype**
   A local weather-state node preserving the k=5/k=6 month/season evidence.
   Subtypes are not required to be globally present. Sparse subtypes collapse
   to their macro regime for gate evaluation, but their assignment probability
   must remain available for diagnosis and future features.

3. **Soft assignment signals**
   Component probabilities, macro-family probabilities, entropy, margin,
   confidence, distance, and nearest alternatives. These are experimental
   evidence and future feature candidates, not production labels.

The top-level macro labels for the first v2 sprint are:

- `macro_nw_continuum`
- `macro_southerly_flow`
- `macro_light_marine_or_residual`
- `macro_insufficient`

The first three are evaluated by R2. `macro_insufficient` remains an exclusion
or audit label and must not be counted as a meteorological regime pass/fail.

The subtype layer is derived from Onda 2E candidate centroids and physical
signatures. Initial subtype names should be data-backed, for example:

- `subtype_standard_nw`
- `subtype_foehn_nw`
- `subtype_prefrontal_nw`
- `subtype_frontal_southerly`
- `subtype_postfrontal_southerly`
- `subtype_calm_radiative`
- `subtype_maritime_cloudy`
- `subtype_transition_low_confidence`

`subtype_transition_low_confidence` is allowed only as a subtype or audit flag.
It must never become a macro regime.

The first sprint may compute probabilities with a deterministic distance-softmax
over v2 centroids if a full train-only GMM is too large for the first delivery.
The assignment schema must nevertheless be compatible with a future GMM:
`component_probabilities`, `family_probabilities`, `component_argmax`,
`component_entropy`, and `component_margin` are required outputs. A later GMM
implementation may replace the distance-softmax backend without changing the
artifact contract.

## Scope

The sprint builds a non-production v2 regime design path:

- diagnose why v1 dead families are dead;
- define a v2 candidate schema with macro, subtype, and soft assignment fields;
- generate candidate v2 assignments from existing local artifacts;
- validate v1 versus v2 under the same R2 screening scope;
- register foundation experiment results for v2;
- update ADR-012 only with evidence from generated artifacts.

## Non-Scope

- No Onda 3 model training.
- No production classifier promotion.
- No overwrite of `data/features.parquet`.
- No external data ingestion.
- No relaxation of Onda 4 gates.
- No use of `tmax_int`, `tmax_hour`, `tmax_anomaly`, `remaining_warming`, or
  other outcome fields for assignment.
- No promotion of `late_warming`, `mixed_or_transition`, or intraday
  state-change labels as macro regimes.

## Required Artifacts

The sprint should generate these artifacts:

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
- updated `reports/foundation-experiments/foundation_experiment_results_v1.csv`
  if v2 result rows are added.

All generated v2 rows must use `production_status = NOT_PRODUCTION` for regime
candidate artifacts or `production_status = EXPERIMENT_ONLY` for foundation
experiment results.

## Candidate v2 Schema

`regime_design_candidate_v2.csv` must include:

| Column | Meaning |
|---|---|
| `candidate_version` | Always `v2`. |
| `candidate_id` | Stable v2 candidate row ID. |
| `source_candidate_ids` | Semicolon-separated v1 candidate IDs used. |
| `source_strategy` | `macro_merge`, `subtype_preserve`, `dead_family_absorb`, or `low_confidence_subtype`. |
| `macro_regime_label` | One of the v2 macro labels. |
| `subtype_label` | Local subtype label. |
| `latent_component_id` | Stable local component/subtype identifier. |
| `component_family_prior` | Macro family prior used by assignment, if any. |
| `stratum_type` | `month`, `season`, or `global`. |
| `stratum_value` | Month number, season name, or `all`. |
| `n_source_rows` | Sum of source candidate support rows. |
| `mean_interpretability_score` | Mean score from source candidates. |
| `physical_signature` | Semicolon-separated physical signals. |
| `wind_dir_deg_mean` | Candidate centroid wind direction mean. |
| `wind_speed_mean` | Candidate centroid wind speed mean. |
| `qnh_hpa_mean` | Candidate centroid QNH mean. |
| `relh_mean` | Candidate centroid relative humidity mean. |
| `dewpoint_depression_mean` | Candidate centroid dewpoint depression mean. |
| `precip_pre_cp_sum_mean` | Candidate centroid pre-CP precipitation mean. |
| `cloud_cover_score_mean` | Candidate centroid cloud-cover score mean. |
| `temp_slope_pre_cp_mean` | Candidate centroid pre-CP temperature slope mean. |
| `dominant_current_regime` | Diagnostic only. |
| `design_rationale` | Short reason this row exists. |
| `causal_inputs` | Semicolon-separated causal assignment inputs. |
| `production_status` | Always `NOT_PRODUCTION`. |
| `next_gate_action` | Required next validation action. |

## Assignment v2 Schema

`regime_candidate_assignments_v2.csv` must include:

| Column | Meaning |
|---|---|
| `date_local` | Local date. |
| `cp` | Checkpoint. |
| `macro_regime_label` | Top-level v2 macro label. |
| `subtype_label` | Local subtype label. |
| `candidate_regime_label` | Alias for `macro_regime_label` when calling current R2 helpers. |
| `source_candidate_id` | v2 candidate used for assignment. |
| `component_argmax` | Highest-probability latent component. |
| `component_probabilities` | JSON object of component probabilities. |
| `family_probabilities` | JSON object of macro-family probabilities. |
| `component_entropy` | Entropy of the component distribution. |
| `component_margin` | Probability gap between top-1 and top-2 components. |
| `nearest_alternative_macro` | Second-best macro label. |
| `distance_to_candidate` | Standardized distance to selected v2 candidate. |
| `distance_to_alternative` | Standardized distance to nearest alternative. |
| `assignment_confidence` | Confidence derived from distance margin. |
| `low_confidence_flag` | True when assignment is boundary-like. |
| `causal_window` | Always `valid < CP`. |
| `production_status` | Always `NOT_PRODUCTION`. |

## Assignment Policy

Assignments must use only causal pre-CP inputs already used by Onda 2E:

- circular wind direction components;
- wind speed;
- QNH or pressure proxy;
- relative humidity;
- dewpoint depression;
- pre-CP precipitation;
- cloud cover score;
- pre-CP temperature slope.

The algorithm may reuse the current centroid-distance pattern, but it must
return macro, subtype, and probability diagnostics. It must explicitly prevent
v1 rare families from becoming top-level macro regimes unless they have enough
support and pass R2.

Probability policy:

- Compute component scores from standardized causal-input distances.
- Convert scores to probabilities with a stable softmax over negative distance.
- Sum component probabilities by `macro_regime_label` to produce
  `family_probabilities`.
- Set `macro_regime_label` to the highest-probability family for compatibility
  with existing R2 helpers.
- Flag low confidence when entropy is high or the top-1/top-2 margin is small.
- Never turn high entropy into a macro regime called `mixed` or `transition`.

Initial mapping policy:

- v1 `candidate_nw_or_foehn` maps to `macro_nw_continuum` with NW/foehn
  subtypes.
- v1 `candidate_southerly_disrupted` maps to `macro_southerly_flow` with
  frontal/postfrontal subtypes.
- v1 `candidate_maritime_cloudy` maps to a subtype inside
  `macro_light_marine_or_residual` unless diagnostics prove enough support for
  an independent macro.
- v1 `candidate_mixed_or_transition` maps to low-confidence subtype evidence or
  the nearest physical macro; it is not a macro regime.

## Validation Policy

The v2 validation must compare v1 and v2 under the same scope:

- same `features.parquet`;
- same `labels.parquet`;
- same CP set;
- same test starts;
- same hypothesis set;
- no mutation of source features.

The comparison table must include:

- `candidate_version`;
- `macro_regime_label`;
- `assignment_rows`;
- `r2_rows`;
- `r2_pass_rows`;
- `r2_dead_status`;
- `protected_regression_flag`;
- `low_confidence_share`;
- `mean_component_entropy`;
- `mean_component_margin`;
- `smallest_cp_support`;
- `decision_update`.

The v2 design may advance to a full Onda 4 rerun only if:

1. every evaluated v2 macro regime has at least one passing R2 row;
2. no v1 passing physical macro becomes dead;
3. no macro has support below the agreed minimum power threshold;
4. low-confidence assignments are reported and do not hide dead families;
5. the report states that this is still not a production classifier.

Passing this v2 screening does not unblock Onda 3 directly. It only permits a
full Onda 4 rerun against the candidate feature copy.

## Parallel Sprint Shape

The sprint can be parallelized safely:

- Agent A owns diagnostics:
  `solarstorm/onda2e/_regime_repair_diagnostics.py` and
  `tests/test_regime_repair_diagnostics.py`.
- Agent B owns v2 candidate generation:
  `solarstorm/onda2e/_regime_candidate_revision.py` and
  `tests/test_regime_candidate_revision.py`.
- Agent C owns foundation result acceptance for v2:
  `solarstorm/onda2e/_foundation_experiment_results.py` and
  `tests/test_foundation_experiment_results.py`.
- The main integration path owns comparative validation, CLI wiring, generated
  artifacts, and documentation.

## Error Handling

The CLI must fail fast when:

- required candidate v1/v2 columns are missing;
- any assignment row has a null macro or subtype label;
- any v2 candidate artifact uses production status other than `NOT_PRODUCTION`;
- any assignment artifact uses a causal window other than `valid < CP`;
- v2 produces zero support for a required macro;
- v2 removes a previously evaluated family instead of explicitly merging or
  demoting it;
- R2 comparison cannot be computed.

## Acceptance Criteria

The redesign sprint is successful when:

1. v2 artifacts are generated and every row remains non-production.
2. A v1 vs v2 comparison explicitly shows whether dead-family count improved.
3. `candidate_maritime_cloudy` and `candidate_mixed_or_transition` are no
   longer treated as unsupported macro regimes.
4. The report explains whether v2 is ready for a full Onda 4 rerun.
5. ADR-012 records the result without promoting production.
6. `uv run ruff check .` passes.
7. `uv run pytest -q -m "not network"` passes.

## Sources

Local evidence:

- `reports/regime/2026-06-06-regime-trigger-audit.md`
- `reports/regime/2026-06-06-cooling-rule-experiment.md`
- `reports/onda2e/regime_design_candidate_v1.csv`
- `reports/regime-design/regime_candidate_assignments_v1.csv`
- `reports/regime-design/regime_candidate_r2_validation.csv`
- `reports/regime-design/regime_candidate_validation_report.md`

Scientific references:

- Michelangeli, P. A., Vautard, R., and Legras, B. 1995. Weather regimes:
  recurrence and quasi stationarity. Journal of the Atmospheric Sciences.
- Kidson, J. W. 2000. An analysis of New Zealand synoptic types and their use
  in defining weather regimes. International Journal of Climatology.
- Christiansen, B. 2007. Atmospheric Circulation Regimes: Can Cluster Analysis
  Provide the Number? Journal of Climate.
- Falkena et al. 2022. A Bayesian Approach to Atmospheric Circulation Regime
  Assignment.
