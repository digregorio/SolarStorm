# P1 Horizon Hybrid Model — Design Spec

Date: 2026-06-12
Status: accepted (derived from `reports/forensic-investigation-v2.md`)
Depends on: P0 honest evaluation harness
(`docs/superpowers/specs/2026-06-12-p0-honest-evaluation-design.md`)
Production status of all outputs: `EXPERIMENT_ONLY`

## Problem

Forensic v2 located the project's two real signal sources and showed the
current models use neither correctly:

1. **Late CPs are a nowcast problem.** The trivial null
   `k_cp + climatological remaining warming` scores 0.850 MAE at CP 23:00 and
   beats Onda 3F (1.028) there — yet `k_cp` never reaches the Onda 3F design
   matrix (`features.parquet` lacks it; the allowlist filter drops it
   silently).
2. **Early CPs are a forecast problem.** Open-Meteo policies score
   0.76-0.78 MAE vs 1.62 for the trivial null at CP 20:00 — but they emit one
   prediction per day repeated across all four CPs
   (`open_meteo_expanded_policy_slice_metrics_v1.csv` shows identical per-CP
   metrics), discarding intraday information exactly where it dominates.
3. The target `tmax_int` mixes already-observed warming with future warming,
   so models waste capacity re-learning what the thermometer already said, and
   6.8-9.0% of predictions violate `prediction >= k_cp`.

## Goal

One experiment-only model iteration that:

- predicts `remaining_warming = tmax_int - k_cp` instead of `tmax_int`;
- reconstructs `tmax_prediction = k_cp + max(0, rw_prediction)` so the
  physical floor holds by construction;
- conditions every CP row on all information available at that CP (k_cp and
  local features vary per CP) and blends the NWP anchor with a lead-aware
  interaction so NWP weight decays as the day progresses;
- is judged exclusively by the P0 honest harness (gates H1-H4), per CP and
  per remaining-warming stratum, on identical covered rows.

## Design

New module `solarstorm/onda3/_hybrid_iteration.py` and CLI
`onda3-hybrid-model-iteration` writing `reports/onda3-hybrid/`.

### Matrix construction (`build_hybrid_matrix`)

Inputs: `features.parquet`, `labels.parquet`, binary macro assignments CSV,
and optionally `data/open_meteo_features_2022_2025.parquet`.

1. Join the k_cp long view (P0 `build_kcp_long`) on `(date_local, cp)`;
   require non-null `k_cp` and `tmax_int`; add target
   `remaining_warming = tmax_int - k_cp` and feature `k_cp`.
2. Join Open-Meteo daily-anchor columns on `(date_local, cp)` with a
   uniqueness check (duplicate keys raise). Derived NWP features:
   - `om_anchor_max` = `om_prev_d1_day_max_c` (NWP-predicted day max);
   - `om_anchor_delta` = `om_anchor_max - k_cp` (NWP-implied remaining
     warming — recomputed per CP, this is what makes the NWP signal
     CP-aware);
   - `cp_lead_rank` = 3,2,1,0 for CPs 20:00,21:00,22:00,23:00;
   - `om_anchor_delta_x_lead` = `om_anchor_delta * cp_lead_rank / 3.0`
     (lead-decaying NWP weight, learnable by the ridge).
3. Reuse `add_pooled_temporal_features` (cyclic cp/month/doy) and the binary
   macro interaction builder from Onda 3F.

### Candidates (evaluated on identical covered rows)

| Candidate | Features | Rows |
|---|---|---|
| `hybrid_local_only` | Onda 3F numeric set + `k_cp` | all rows with k_cp |
| `hybrid_om_augmented` | local set + `om_anchor_max`, `om_anchor_delta`, `om_anchor_delta_x_lead` | rows with non-null OM anchor |

Both ridge (`_ridge_predict`), walk-forward per test year (train = years
before the test year), `target_column = "remaining_warming"`, prediction
clamped: `rw_pred_clamped = max(0, rw_pred)`,
`tmax_prediction = k_cp + rw_pred_clamped`. All error metrics are computed on
the Tmax scale against `tmax_int`.

The `hybrid_local_only` candidate is also evaluated on the OM-covered subset
so the OM lift is a same-row comparison (the OM-M5/M13 discipline).

### Judgement

For every candidate, run the P0 honest comparison (model vs honest null per
CP and per stratum) and the P0 gate matrix H1-H4. Decision:

- `hybrid_om_augmented` passes H1+H2 on covered rows →
  `READY_FOR_P2_DISTRIBUTION_DESIGN`.
- only `hybrid_local_only` passes → `KEEP_HYBRID_LOCAL_AS_REFERENCE`.
- neither passes → `KEEP_IN_ONDA3_EXPERIMENT_REVIEW`.

Success criteria (pre-registered, not editable after results):

1. `hybrid_local_only` must close the CP 22:00/23:00 gap: MAE <= honest null
   at every CP (H1).
2. `hybrid_om_augmented` must beat the honest null on `forecast_2_plus`
   rows at every CP with support (H2) and beat `hybrid_local_only` same-row
   overall MAE.
3. Zero physical-floor violations (H3 holds by construction; the artifact
   must prove it).

## Non-goals

- No probabilistic distribution, CRPS or EMOS (P2).
- No abstention/late-spike classifier (P3).
- No new data sources, providers or calibration formulas (P4); the OM input
  is the existing gated GFS pilot table
  `data/open_meteo_features_2022_2025.parquet`.
- No production, EV, pricing, shadow trading, or execution.

## Guardrails

- All artifacts `production_status = EXPERIMENT_ONLY`.
- Train-only fitting per fold; no information from the test year enters
  encoding, imputation, or the null.
- Do not overwrite existing report directories; write only
  `reports/onda3-hybrid/`.
- Tests must not hit the network.

## Test plan

TDD per `docs/superpowers/plans/2026-06-12-p1-horizon-hybrid-model.md`:
matrix join correctness (k_cp, rw target, OM anchor delta per CP, duplicate
OM keys raise), clamp/floor reconstruction, fold runner metrics on Tmax
scale, same-row OM comparison, decision matrix, CLI smoke test on synthetic
fixtures.
