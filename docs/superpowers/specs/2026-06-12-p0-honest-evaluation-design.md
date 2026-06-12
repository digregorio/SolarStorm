# P0 Honest Evaluation Harness — Design Spec

Date: 2026-06-12
Status: accepted (derived from `reports/forensic-investigation-v2.md`)
Production status of all outputs: `EXPERIMENT_ONLY`

## Problem

The forensic investigation v2 proved that the current evaluation protocol
overstates model skill:

1. The M3 gate compares challengers against the **train-mean null**
   (MAE 2.812, `solarstorm/onda3/_pooled_iteration.py:318-321`). The honest
   null for this problem — `k_cp` (max temperature already observed before the
   CP) plus the train-only climatological median of remaining warming — scores
   MAE 1.62/1.39/1.10/**0.85** at CPs 20:00-23:00 UTC and **beats Onda 3F at
   CP 23:00** (0.850 vs 1.028) while nearly tying at CP 22:00.
2. The M7 "anti-nowcast" gate is hardcoded `PASS`
   (`solarstorm/robustness/_model_review.py:159-165`) and computes nothing.
3. At CP 23:00, 26.1% of days already realized their Tmax and 62.0% have
   <= 1 C remaining, so aggregate MAE mixes trivial nowcast rows with genuine
   forecast rows.
4. 6.8-9.0% of the best candidates' predictions violate the physical floor
   `prediction >= k_cp`.
5. `k_cp` never reaches the model matrix: the Onda 3H allowlist names it, but
   `features.parquet` does not contain it, so the silent
   `if column in matrix.columns` filter drops it.

No model may be promoted, and no further model iteration may be trusted,
until evaluation is performed against the honest null with lead-stratified
metrics.

## Goal

Build a reusable honest-evaluation harness that any existing or future
prediction artifact can be scored against, and freeze its gates ex-ante
(anti-gaming discipline: thresholds are fixed in this spec, before any model
sees them).

## Scope

New package `solarstorm/honest_eval/` plus a `honest-evaluation` CLI command.
The harness evaluates an existing predictions CSV (default:
`reports/onda3-pooled/onda3_pooled_predictions_v1.csv`; any artifact with
`date_local, cp, actual, prediction` columns works) and writes artifacts under
`reports/honest-evaluation/`.

### Components

1. **k_cp long view** (`_kcp.py`): unpivot the wide
   `k_cp__cp_2000..k_cp__cp_2300` label columns into long
   `(date_local, cp, k_cp)` rows so k_cp can be joined to any per-CP frame.
2. **Honest null** (`_null.py`): fit on train rows only
   (`year <= train_end_year`): per `(month, cp)` median of
   `remaining_warming = tmax_int - k_cp`, with a per-CP global median
   fallback for unseen months. Predict `k_cp + round(median)`.
3. **Physical floor** (`_floor.py`): `apply_physical_floor` clamps
   `prediction` to `>= k_cp`; `build_floor_violation_audit` reports raw
   violation counts/rates before clamping.
4. **Lead strata** (`_strata.py`): bucket each row by realized remaining
   warming `actual - k_cp`: `already_seen` (<= 0), `small_1` (1),
   `forecast_2_plus` (>= 2). Compare model vs honest null MAE/exact per CP and
   per stratum.
5. **Persistence ablation** (`_ablation.py`): rerun
   `build_onda3_pooled_iteration` with and without the persistence block
   `{"tmax_dminus1", "slope_3h", "warming_rate_06_09"}` and report MAE delta
   per test year. Quantifies how much skill is persistence-borne.
6. **Gates + decision** (`_review.py`): see Gate policy.
7. **Artifact writer** (`_artifacts.py`): CSV + MD pairs and a markdown
   report, following the Onda 3F writer pattern.

### Gate policy (frozen ex-ante)

| Gate | Name | PASS condition |
|---|---|---|
| H1 | Per-CP honest lift | model MAE < honest-null MAE at **every** CP |
| H2 | Anticipation stratum | model MAE < honest-null MAE on `forecast_2_plus` rows, overall and at every CP with >= 30 such rows |
| H3 | Physical floor | raw violations are reported; clamped predictions have 0 violations |
| H4 | Lead degradation table | MAE by stratum x CP table exists and is non-empty for every CP |

Decision semantics:

- All gates PASS → `HONEST_EVALUATION_PASSED` (allows the next
  experiment-only iteration to cite honest skill; does NOT unlock production).
- H1 or H2 BLOCK → `BLOCK_MODEL_PROMOTION_HONEST_NULL`.
- H3/H4 failures → `KEEP_IN_HONEST_EVALUATION_REVIEW` (instrumentation bug,
  fix before reading results).

The ablation artifact is informational in P0 (no gate); its numbers feed the
P1 design and the model card.

## Non-goals

- No new model (that is P1).
- No modification of historical Onda 4M artifacts; M3/M7 stay as-is for
  reproducibility. New iterations must run `honest-evaluation` in addition.
- No probabilistic output (P2), no abstention rule change (P3), no new data
  (P4), no EV (P5).

## Expected result (pre-registered)

Applying the harness to `reports/onda3-pooled/onda3_pooled_predictions_v1.csv`
is expected to yield `BLOCK_MODEL_PROMOTION_HONEST_NULL` (H1 fails at CP
22:00/23:00). That is the honest baseline the P1 hybrid must beat.

## Guardrails

- All artifacts carry `production_status = EXPERIMENT_ONLY`.
- Null fit is train-only (`year <= train_end_year`, default 2022).
- No mutation of `data/*.parquet` or existing report directories.
- Tests must not hit the network.
- Thresholds in the gate table may not be edited after results are seen
  (ADR-012 / anti-gaming).

## Test plan

TDD per `docs/superpowers/plans/2026-06-12-p0-honest-evaluation.md`:
unit tests for unpivot, null fit/fallback/predict, floor clamp + audit,
strata assignment, gate matrix (each PASS/BLOCK path), ablation comparison
shape, CLI smoke test on synthetic fixtures.
