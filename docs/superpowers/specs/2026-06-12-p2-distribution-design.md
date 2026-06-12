# P2 Calibrated Distribution Design (EMOS/CRPS over the P1 hybrid)

Date: 2026-06-12
Status: PROPOSED (pre-registered before any P2 run)
Depends on: P0 honest evaluation harness (`solarstorm/honest_eval/`), P1
horizon hybrid model (`solarstorm/onda3/_hybrid_iteration.py`), decision
`READY_FOR_P2_DISTRIBUTION_DESIGN` in
`reports/onda3-hybrid/onda3_hybrid_decision_v1.csv`.

## Context (verified inputs)

- P1 `hybrid_om_augmented` passed H1-H4 plus the pre-registered same-row MAE
  comparison (0.726 vs 0.951) on OM-covered rows. `hybrid_local_only` passes
  H1 only: without the NWP anchor there is no proven anticipation skill.
- OM anchor coverage starts 2023, so covered walk-forward test folds are
  2024 and 2025 only (~2848 scored rows). The 2023 fold has no covered train
  rows and is skipped, as in P1.
- All P1 point predictions satisfy the physical floor by construction
  (`tmax = k_cp + max(0, rw_pred)`); the P2 distribution must satisfy the
  distributional analog: zero probability mass below `k_cp`.
- Everything remains `EXPERIMENT_ONLY`. No production, EV, pricing, shadow
  trading, or execution work is unlocked.

## Goal

Replace the P1 point forecast with a calibrated predictive distribution of
`remaining_warming = tmax_int - k_cp` (hence `Tmax = k_cp + rw`), scored by
CRPS against an honest climatological null distribution, judged by frozen
gates D1-D4 with pre-registered decision semantics.

## Canonical representation: 199 quantiles

Every predictive distribution — both candidates and the null — is
represented as a vector of `m = 199` quantiles at levels
`(i - 0.5) / 199, i = 1..199`, on the Tmax scale. One scoring path for
everything: the fair empirical-sample CRPS

```
CRPS(members, y) = mean|x_i - y| - (1/n^2) * sum_j x_(j) * (2j - n - 1)
```

(second term = 0.5 * E|X - X'| via sorted prefix identity). Rationale: no
closed-form transcription risk, uniform machinery for coverage and bracket
probabilities, numpy-only scoring. Interpolated quantile function: linear
interpolation between members at the canonical levels.

## Candidates (pre-registered; no additions after results)

1. **`dist_residual_dressing`** (non-parametric): Tmax members
   `k_cp + max(0, rw_pred_raw + e_q)` where `e_q` are the 199 empirical
   quantiles of out-of-sample residuals `rw_actual - rw_pred_raw`, fit per
   CP on the inner-calibration segment (minimum 60 residuals per CP, else
   pooled-across-CP fallback).
2. **`dist_truncnorm_emos`** (parametric NGR): `rw ~ TruncNormal(mu, sigma,
   lower=0)` with `mu = a + b * rw_pred_raw` and
   `log sigma = c + d * cp_lead_rank`; `(a, b, c, d)` fit by minimizing mean
   sampled CRPS on the inner-calibration segment (scipy Nelder-Mead; init
   `a=0, b=1, c=log(std(residuals)), d=0`; `sigma` clipped to `[0.1, 10]`).
   Members via `scipy.stats.truncnorm.ppf` at the canonical levels.
3. **`dist_climatology_null`** (the honest ruler, not a candidate):
   empirical quantiles of train-only realized `rw` per `(month, cp)` with a
   per-CP `month = 0` fallback (cells need >= 60 train rows, else fallback);
   Tmax members `k_cp + q`. Distributional analog of the P0 honest null.

`rw_pred_raw` is the unclamped ridge output of the per-fold point model; the
floor is applied to members, never to the residual fit.

## Fold discipline (walk-forward, no test leakage)

- Gating surface: OM-covered rows, point model = `hybrid_om_augmented`
  feature set; test years 2024, 2025; train = all covered years strictly
  before the test year.
- Secondary informational surface (never gating): all rows, local-only
  feature set, test years 2023-2025. Provides the uncovered-rows fallback
  view for P3 abstention design.
- Within each fold: chronological inner split of the train window — first
  80% (fit the point model), last 20% (calibration segment: residuals for
  dressing, CRPS objective for EMOS). The point model is then refit on the
  full train window to produce test-row `rw_pred_raw`. Nothing from the test
  year enters any fit, encoding, residual pool, or the null.
- **Null window change vs P0/P1 (pre-registered here, before any P2 run):**
  the null distribution refits per fold on years strictly before the test
  year, the same data window the candidates see. This removes the frozen
  <=2022 null asymmetry flagged in the P1 review and makes the ruler
  strictly harder than P0's.

## Gates D1-D4 (frozen ex ante; thresholds not editable after results)

| Gate | Name | Rule |
| --- | --- | --- |
| D1 | CRPS lift per CP | candidate mean CRPS < null mean CRPS at every CP (20/21/22/23) on the gating surface |
| D2 | Anticipation stratum | same condition on `forecast_2_plus` rows: overall and at every CP with >= 30 such rows |
| D3 | Central-interval calibration | pooled empirical coverage of the [q05, q95] interval in [85%, 95%] AND of [q25, q75] in [40%, 60%] |
| D4 | Distributional floor + integrity | zero members below `k_cp` on every row; integer-bracket probabilities sum to 1 +/- 1e-6 per row |

Strata reuse `assign_remaining_warming_strata` from P0 (realized
`actual - k_cp`: `already_seen` <= 0, `small_1` <= 1, `forecast_2_plus`
otherwise). Coverage counts `q_lo <= actual <= q_hi` with interpolated
quantiles. Both candidates are judged independently; the null is never
gated.

## Decision semantics (pre-registered)

- Any candidate fails D4 on the gating surface ->
  `KEEP_IN_P2_DISTRIBUTION_REVIEW` (instrumentation defect; fix harness, do
  not interpret skill).
- Else if >= 1 candidate passes D1+D2+D3 on the gating surface ->
  `READY_FOR_P3_ABSTENTION_DESIGN`; `promoted_candidate` = the passer with
  the lowest same-row pooled mean CRPS (both candidates score identical
  rows, so the comparison is same-row by construction; values recorded in
  the decision artifact).
- Else -> `KEEP_POINT_HYBRID_AS_REFERENCE` (the P1 point hybrid remains the
  reference; distributions added no honest value).

## Success criteria (pre-registered, not editable after results)

1. At least one candidate beats the climatological null distribution CRPS at
   every CP (D1) and on supported `forecast_2_plus` strata (D2).
2. The promoted candidate's pooled 90%/50% central-interval coverages fall
   inside the frozen D3 bounds.
3. Zero distributional floor violations and bracket-probability integrity
   (D4) — must hold by construction; the artifact must prove it.
4. The same-row CRPS comparison between the two candidates is recorded in
   the decision artifact regardless of outcome.

## Module layout

- Create `solarstorm/distribution/` package:
  - `_constants.py` — candidate/surface names, freeze line, shared statuses.
  - `_quantiles.py` — canonical levels, empirical quantiles, interpolation.
  - `_crps.py` — vectorized empirical-member CRPS.
  - `_null.py` — climatological null distribution fit/predict.
  - `_dressing.py` — residual-dressing candidate.
  - `_emos.py` — truncated-normal EMOS candidate (scipy).
  - `_coverage.py` — interval coverage + bracket probabilities + floor audit.
  - `_review.py` — gates D1-D4 + decision.
  - `_iteration.py` — fold orchestration over the P1 matrix builders.
  - `_artifacts.py` — CSV/MD writer + report.
- Modify `solarstorm/__main__.py` — add `p2-distribution-iteration` CLI.
- Modify `pyproject.toml` — declare `scipy>=1.11` explicitly (today it is
  only a transitive dependency of scikit-learn).
- Reports: `reports/p2-distribution/` only. Artifacts:
  `p2_distribution_{results,by_cp,by_stratum_cp,coverage,quantile_predictions,floor_audit,gates,decision}_v1.csv`
  (+ `.md` pairs) and `p2_distribution_report_v1.md`. Every row carries a
  `surface` column: `covered_om` (gating) or `local_all` (informational);
  gates and decision read `covered_om` rows only. Quantile predictions
  persist selected levels (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95) plus
  per-row CRPS, not all 199 members.

## Non-goals

- No Open-Meteo Ensemble API, no new providers, no new data collection (P4).
- No abstention rule or late-spike classifier (P3).
- No production, EV, pricing, shadow trading, or execution (P5, frozen).
- No mutation of P0/P1 artifacts or `data/*.parquet`.

## Guardrails

- Every generated row carries `production_status = EXPERIMENT_ONLY`; every
  report carries the freeze line.
- Walk-forward only; the inner 80/20 split is chronological; the null refits
  per fold on pre-test years.
- Any randomization uses a fixed seed (7). Tests never hit the network.
- Gate thresholds, candidate set, and decision matrix are frozen by this
  spec; record whatever happens, tune nothing.

## Test plan

TDD per `docs/superpowers/plans/2026-06-12-p2-distribution.md`: property
tests for CRPS (brute force + closed-form normal limit), null fit/fallback,
dressing floor and residual conditioning, EMOS parameter recovery on
synthetic Gaussian data, coverage/bracket/floor audits, every gate PASS and
BLOCK path, decision matrix including promoted-candidate selection and the
D4-instrumentation branch, fold orchestration leakage guards, CLI smoke test
on synthetic fixtures, all offline.
