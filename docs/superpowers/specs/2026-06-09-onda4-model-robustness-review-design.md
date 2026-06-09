# Onda 4 Model Robustness Review Design

## Status

Accepted for implementation planning on 2026-06-09.

The first Onda 3 baseline-first model run generated experiment-only artifacts
under `reports/onda3/` and records
`decision_status = READY_FOR_ONDA4_MODEL_RERUN`. Onda 4 may now proceed as a
model robustness review of that candidate. This is not production approval, not
deployment approval, and not permission to resume market execution.

## Problem

The original Onda 4 robustness wave stress-tested the Onda 2 feature-null and
regime foundation before model work. That historical wave remains useful, but
the project now has a new object to validate: the Onda 3 baseline model result.

The first Onda 3 run reports:

- train-mean null MAE: 2.8120
- ridge challenger MAE: 1.3487
- decision status: `READY_FOR_ONDA4_MODEL_RERUN`
- production status: `EXPERIMENT_ONLY`

That result is promising but insufficient by itself. The model could still be
overfit to a single split, dependent on weak slices, hiding failures in
`macro_non_southerly`, using unsafe feature columns, lacking calibrated
uncertainty, or improving MAE while failing abstention/stay-out behavior.

Onda 4 must therefore become the model robustness review that decides whether
the Onda 3 baseline candidate can remain active for the next modeling wave, must
return to Onda 3 experiment review, or must be blocked by causal/slice/uncertainty
evidence.

## Goals

1. Validate Onda 3 model artifacts without mutating `data/features.parquet` or
   production classifiers.
2. Recompute a model robustness surface from the Onda 3 reports and, where
   necessary, the source feature/label artifacts.
3. Gate the model on causal manifest safety, challenger-vs-null lift, temporal
   stability, slice coverage, uncertainty/abstention evidence, anti-nowcast
   checks, and clean decision semantics.
4. Produce machine-readable and markdown artifacts under
   `reports/onda4-model/`.
5. Update ADR-012, roadmap, robustness plan, model card, and changelog so the
   project state is explicit: Onda 4 model review is the next wave, production
   remains blocked.
6. Close the milestone only with verification green and a clean working tree.

## Non-Goals

- Do not promote any production model.
- Do not add market execution, EV, position sizing, shadow trading, or
  Polymarket integration.
- Do not introduce NWP/Open-Meteo ingestion in this review.
- Do not redesign regimes or revive the v2.2/v2.3 calm/radiative loop.
- Do not relax the causal firewall or allow full-day target/proxy features as
  live model inputs.
- Do not overwrite Onda 3 artifacts; Onda 4 reads them and writes separate
  review artifacts.

## Entry Evidence

Required inputs:

- `reports/onda3/onda3_feature_manifest_v1.csv`
- `reports/onda3/onda3_design_matrix_audit_v1.csv`
- `reports/onda3/onda3_baseline_results_v1.csv`
- `reports/onda3/onda3_challenger_results_v1.csv`
- `reports/onda3/onda3_slice_diagnostics_v1.csv`
- `reports/onda3/onda3_uncertainty_abstention_v1.csv`
- `reports/onda3/onda3_decision_update_v1.csv`
- `reports/onda3/onda3_baseline_model_report_v1.md`
- `data/features.parquet`
- `data/labels.parquet`
- optional binary macro assignments:
  `reports/regime-design/regime_binary_macro_assignments_v1.csv`

The review must block if the Onda 3 decision is not
`READY_FOR_ONDA4_MODEL_RERUN` or if Onda 3 artifacts are missing.

## Model Robustness Gates

Onda 4 model review uses a separate M-series gate set so it does not overload
the historical R1-R9 regime/feature-null meanings.

| Gate | Name | Blocking condition |
|---|---|---|
| M1 | Input artifact integrity | Missing required Onda 3 artifact or unreadable schema. |
| M2 | Causal manifest safety | Any included Onda 3 feature has blocked target/proxy leakage class. |
| M3 | Challenger lift | Challenger does not beat train-mean null by positive MAE delta. |
| M4 | Temporal robustness | Year/split replication shows fewer than the minimum passing test years or unstable lift. |
| M5 | Slice robustness | CP, month, or binary macro slice has catastrophic support/MAE weakness. |
| M6 | Uncertainty/abstention | No empirical uncertainty row, invalid interval metrics, or no abstention rule. |
| M7 | Anti-nowcast/model timing | Candidate relies on target/proxy/timing columns or skill is concentrated where the answer is effectively known. |
| M8 | Decision hygiene | Any output claims production readiness, deployment, financial execution, or mutates production data. |

Initial thresholds:

- positive lift: challenger MAE must be lower than null MAE;
- minimum test years with positive lift: 1 for the first review, because the
  current Onda 3 run uses one test year;
- catastrophic slice support: fewer than 30 rows in a reported slice;
- catastrophic slice weakness: slice MAE cannot be computed or exceeds the null
  MAE by more than 20 percent;
- uncertainty evidence: p50 and p90 absolute residuals must be finite and p90
  must be greater than or equal to p50;
- decision hygiene: every Onda 4 model artifact must keep
  `production_status = EXPERIMENT_ONLY`.

These thresholds are intentionally conservative and visible. Future model
families may tighten them, but this first review must not invent hidden pass
criteria after seeing results.

## Architecture

Add a dedicated model-review layer under `solarstorm/robustness/`:

```text
reports/onda3/*.csv
        |
        v
solarstorm.robustness._model_review
        |
        +--> input artifact audit
        +--> causal manifest audit
        +--> model lift and temporal checks
        +--> slice/uncertainty/abstention checks
        +--> decision hygiene checks
        |
        v
reports/onda4-model/*.csv
reports/onda4-model/*.md
```

The implementation should not retrain a new model in the first pass. It should
review and, where useful, recompute diagnostics from the Onda 3 artifact
surface. A later Onda 4 model review may add rolling split refits once the
baseline harness exposes multiple folds directly.

## Artifacts

Planned outputs:

- `reports/onda4-model/onda4_model_input_audit_v1.csv/.md`
- `reports/onda4-model/onda4_model_gate_results_v1.csv/.md`
- `reports/onda4-model/onda4_model_slice_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_uncertainty_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_decision_update_v1.csv/.md`
- `reports/onda4-model/onda4_model_robustness_report_v1.md`

Decision statuses:

- `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`
- `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`
- `BLOCK_MODEL_PROMOTION`

`READY_FOR_ONDA3_NEXT_MODEL_ITERATION` means the experiment can proceed to the
next model iteration. It still does not mean production readiness.

## Documentation Updates

The implementation must update:

- `ROADMAP.md`
- `docs/decisions/012-evidence-to-decision-gate.md`
- `docs/onda4_robustness_plan.md`
- `docs/regime_model_card.md`
- `CHANGELOG.md`

Each update must state:

- Onda 3 baseline artifacts exist and remain experiment-only;
- Onda 4 model robustness review is the next active wave;
- production, deployment, and financial execution remain blocked;
- the review reads Onda 3 artifacts and writes under `reports/onda4-model/`;
- the milestone closes only after verification and clean tree.

## Acceptance Criteria

- Onda 4 model review has a dedicated spec and implementation plan.
- Documentation reflects the decision to proceed from Onda 3 baseline to Onda 4
  model robustness review.
- The plan includes TDD steps for input audit, gate evaluation, artifact writer,
  CLI, docs, verification, and clean-tree closure.
- No document claims production readiness, deployment readiness, or financial
  execution.
- The implementation plan keeps Onda 4 model review separate from historical
  R1-R9 regime robustness.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Onda 4 is mistaken for production approval. | Every artifact uses `EXPERIMENT_ONLY` and decision text forbids deployment. |
| Historical R1-R9 semantics become overloaded. | Use M1-M8 model-specific gates for this review. |
| A single split gives false confidence. | M4 records split/year limitations and can return experiment review instead of promotion. |
| Slice failures are hidden by aggregate MAE. | M5 requires CP/month/binary macro slice review. |
| Uncertainty is decorative. | M6 blocks missing or invalid uncertainty/abstention evidence. |
| The tree becomes dirty after generated reports. | Milestone closure requires cleanup, verification, commit, and clean `git status`. |

## Decision

Proceed with Onda 4 as a model robustness review of the experiment-only Onda 3
baseline result. The first implementation should add a small, auditable review
surface, generate Onda 4 model artifacts, and update documentation before any
new model family or production-facing work begins.
