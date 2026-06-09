# Onda C Regime Classifiability Design

Status: approved for implementation planning
Date: 2026-06-08

## Goal

Run a non-production scientific validation wave after Opcao A/v2.1 to decide
whether the two-macro regime surface is structurally classifiable, stable, and
topologically coherent enough to become the basis for future Onda 3 model work.

Onda C is required before Onda 3. The v2.1 Onda 4 `GO` is strong evidence that
Opcao A removed the immediate dead-regime blocker, but it does not prove that
the regime ontology is the best scientific structure.

## Current Evidence

Opcao A generated Regime Ontology v2.1 as a non-production candidate:

- 21,824 assignment rows, all `production_status = NOT_PRODUCTION`.
- `macro_nw_continuum`: 15,879 assignment rows.
- `macro_southerly_flow`: 5,945 assignment rows.
- 351 residual rows absorbed from `macro_light_marine_or_residual`.
- 0 invalid absorption targets.
- `regime_candidate_v2_v21_comparison.csv` records
  `READY_FOR_FULL_ONDA4_RERUN`, with 0 v2.1 dead macros.
- `reports/robustness-v2_1/2026-06-08-robustness-report.md` records Onda 4
  candidate verdict `GO`.

This evidence validates the two-macro candidate as a useful screening surface.
It does not answer whether distance-softmax assignments are the right backend,
whether two macros are topologically separable, or whether a train-only
probabilistic method would discover the same structure.

## Decision

Implement Onda C as a classifiability benchmark, not as model training. Onda C
compares:

- `distance_softmax_v2`: the existing v2 assignment surface, with the residual
  macro still present.
- `distance_softmax_v21`: the Opcao A/v2.1 assignment surface, with residual
  rows absorbed into protected physical macros.
- `train_only_gmm`: Gaussian mixture assignments fitted only on train folds and
  projected onto test folds.
- `som_topological`: topology-preserving map diagnostics fitted only on train
  folds and projected onto test folds.
- `michelangeli_stability`: classifiability and stability diagnostics inspired
  by weather-regime literature, using resampling/fold stability and separation
  checks rather than production inference.

Onda C may recommend keeping v2.1, revising it, or replacing the assignment
backend. It must not create production classifiers, Onda 3 models, model
weights, pickles/joblibs, or deployment artifacts.

## Scope

Onda C builds:

- a dedicated classifiability module;
- schema-checked non-production artifacts;
- a CLI command to run the benchmark;
- a Markdown report with decision recommendation;
- documentation updates preserving the order Opcao A -> Onda C -> Onda 3.

## Non-Scope

- No Onda 3 model training.
- No production classifier promotion.
- No overwrite of `data/features.parquet`.
- No external data ingestion.
- No financial, EV, market, execution, shadow/live, or deployment work.
- No serialized production model artifact.

## Inputs

Required inputs:

- `reports/regime-design/features_candidate_v2_1.parquet`
- `reports/regime-design/regime_candidate_assignments_v2.csv`
- `reports/regime-design/regime_candidate_assignments_v2_1.csv`
- `reports/onda2e/regime_design_candidate_v2.csv`
- `reports/regime-design/regime_candidate_v2_v21_comparison.csv`

The benchmark must fail fast if:

- input assignments are not non-production;
- v2.1 assignments do not have `candidate_version = v2.1`;
- `causal_window` is present and contains values other than `valid < CP`;
- protected macros `macro_nw_continuum` and `macro_southerly_flow` are absent;
- duplicate assignment keys would make method comparisons ambiguous.

## Output Artifacts

All outputs live under `reports/regime-classifiability/`.

### `regime_classifiability_assignments_v1.csv`

Required columns:

```text
method,candidate_version,date_local,cp,macro_regime_label,subtype_label,
assigned_label,assigned_component,assignment_confidence,assignment_margin,
assignment_entropy,distance_to_centroid,topological_x,topological_y,
train_fold,test_fold,production_status
```

### `regime_classifiability_metrics_v1.csv`

Required columns:

```text
method,candidate_version,macro_regime_label,cp,
n_train,n_test,n_assigned,n_low_confidence,
coverage_share,low_confidence_share,mean_entropy,mean_margin,
silhouette_score,davies_bouldin_score,calinski_harabasz_score,
purity_vs_v21,nmi_vs_v21,ari_vs_v21,
temporal_stability,fold_stability,dead_regime_flag,
production_status
```

### `regime_classifiability_comparison_v1.csv`

Required columns:

```text
method,candidate_version,
macro_count,dead_regimes,protected_regression_flag,
coverage_share,low_confidence_share,mean_entropy,mean_margin,
classifiability_score,stability_score,interpretability_score,
decision_update,production_status,notes
```

Allowed decisions:

- `READY_FOR_ONDA3_DESIGN_REVIEW`
- `KEEP_IN_REGIME_DESIGN_REVIEW`
- `BLOCK_ONDA_C_PROMOTION`

`READY_FOR_ONDA3_DESIGN_REVIEW` does not mean production. It only means the
regime surface may feed Onda 3 design/spec work.

### `regime_classifiability_diagnostics_v1.csv`

Required columns:

```text
diagnostic_item,status,detail,n_rows,production_status
```

Required diagnostics:

- non-production status guardrail;
- no Onda 3 training artifact produced;
- train/test leakage check;
- causal-window check;
- duplicate method/date/CP assignment check;
- protected macros present;
- v2/v2.1 comparison loaded;
- residual absorption acknowledged.

### `regime_classifiability_report_v1.md`

The report must summarize methods, diagnostics, metrics, decision, and next
allowed action. It must explicitly state that Onda C is non-production and that
Onda 3 remains blocked unless Onda C returns
`READY_FOR_ONDA3_DESIGN_REVIEW`.

## Gate

Onda C can return `READY_FOR_ONDA3_DESIGN_REVIEW` only when:

- all critical diagnostics pass;
- no production artifact is created;
- v2.1 remains aligned with 0 dead macros and no protected regression;
- protected macros do not disappear in alternative diagnostics;
- train-only GMM/SOM/Michelangeli checks do not materially contradict v2.1;
- v2.1 classifiability/stability is top-ranked or statistically
  indistinguishable from the best alternative.

If an alternative method is materially better, Onda C returns
`KEEP_IN_REGIME_DESIGN_REVIEW` and records the replacement backend candidate.
If leakage, production artifacts, dead protected regimes, or accidental Onda 3
training are detected, Onda C returns `BLOCK_ONDA_C_PROMOTION`.

## Testing

Required tests:

- schemas for all outputs;
- non-production guardrails;
- no model artifact files are written;
- GMM/SOM fit only on train folds and project onto test folds;
- bad `causal_window` fails;
- missing protected macros fail;
- v2.1 comparison snapshot with 0 dead macros is consumed;
- report states Onda C comes before Onda 3.

## Documentation Updates

The sprint must update:

- `ROADMAP.md`
- `docs/decisions/012-evidence-to-decision-gate.md`
- `docs/regime_model_card.md`
- `docs/onda4_robustness_plan.md`

All must preserve this sequence: Opcao A evidence passed, Onda C comes next,
Onda 3 waits for Onda C decision.
