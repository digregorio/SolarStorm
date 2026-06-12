# Honest Evaluation Report (P0)

Generated: 2026-06-12

All outputs remain EXPERIMENT_ONLY.

No production, EV, pricing, shadow trading, or execution work is unlocked.

## Decision

| decision_status | decision_rationale | production_status |
| --- | --- | --- |
| BLOCK_MODEL_PROMOTION_HONEST_NULL | Frozen P0 honest-evaluation gates H1-H4 applied ex ante. | EXPERIMENT_ONLY |

## Gates H1-H4

| gate_id | gate_name | gate_status | gate_detail | production_status |
| --- | --- | --- | --- | --- |
| H1 | Per-CP honest lift | BLOCK | model MAE is not below honest-null MAE at every CP | EXPERIMENT_ONLY |
| H2 | Anticipation stratum | BLOCK | model does not beat honest null on every supported CP | EXPERIMENT_ONLY |
| H3 | Physical floor | PASS | raw violations reported=359; clamped violations=0 | EXPERIMENT_ONLY |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY |

## Model vs Honest Null by CP

| cp | n_rows | model_mae | null_mae | model_exact_rate | null_exact_rate | model_beats_null | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20:00 | 1096 | 1.137 | 1.589 | 0.286 | 0.216 | true | EXPERIMENT_ONLY |
| 21:00 | 1096 | 1.054 | 1.364 | 0.316 | 0.234 | true | EXPERIMENT_ONLY |
| 22:00 | 1096 | 1.028 | 1.084 | 0.319 | 0.285 | true | EXPERIMENT_ONLY |
| 23:00 | 1096 | 1.028 | 0.831 | 0.315 | 0.372 | false | EXPERIMENT_ONLY |

## Model vs Honest Null by Stratum x CP

| rw_stratum | cp | n_rows | model_mae | null_mae | model_exact_rate | null_exact_rate | model_beats_null | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| already_seen | 20:00 | 144 | 1.461 | 2.514 | 0.174 | 0.000 | true | EXPERIMENT_ONLY |
| already_seen | 21:00 | 154 | 1.265 | 2.149 | 0.247 | 0.000 | true | EXPERIMENT_ONLY |
| already_seen | 22:00 | 186 | 1.174 | 1.882 | 0.280 | 0.000 | true | EXPERIMENT_ONLY |
| already_seen | 23:00 | 279 | 1.072 | 1.000 | 0.287 | 0.000 | false | EXPERIMENT_ONLY |
| forecast_2_plus | 20:00 | 808 | 1.096 | 1.448 | 0.303 | 0.293 | true | EXPERIMENT_ONLY |
| forecast_2_plus | 21:00 | 759 | 1.041 | 1.254 | 0.324 | 0.337 | true | EXPERIMENT_ONLY |
| forecast_2_plus | 22:00 | 635 | 1.049 | 0.926 | 0.329 | 0.452 | false | EXPERIMENT_ONLY |
| forecast_2_plus | 23:00 | 409 | 1.171 | 1.545 | 0.276 | 0.000 | true | EXPERIMENT_ONLY |
| small_1 | 20:00 | 144 | 1.042 | 1.458 | 0.306 | 0.000 | true | EXPERIMENT_ONLY |
| small_1 | 21:00 | 183 | 0.931 | 1.158 | 0.339 | 0.000 | true | EXPERIMENT_ONLY |
| small_1 | 22:00 | 275 | 0.881 | 0.909 | 0.324 | 0.091 | true | EXPERIMENT_ONLY |
| small_1 | 23:00 | 408 | 0.856 | 0.000 | 0.373 | 1.000 | false | EXPERIMENT_ONLY |

## Physical Floor Audit

| cp | n_rows | n_raw_violations | raw_violation_pct | n_clamped_violations | clamped_violation_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| ALL | 4384 | 359 | 8.189 | 0 | 0.000 | EXPERIMENT_ONLY |
| 20:00 | 1096 | 28 | 2.555 | 0 | 0.000 | EXPERIMENT_ONLY |
| 21:00 | 1096 | 48 | 4.380 | 0 | 0.000 | EXPERIMENT_ONLY |
| 22:00 | 1096 | 98 | 8.942 | 0 | 0.000 | EXPERIMENT_ONLY |
| 23:00 | 1096 | 185 | 16.880 | 0 | 0.000 | EXPERIMENT_ONLY |

## Persistence Ablation

| test_year | n_train | n_test | full_mae | ablated_mae | mae_delta_ablated_minus_full | ablated_features | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 16824 | 1460 | 1.116 | 1.451 | 0.335 | tmax_dminus1,slope_3h,warming_rate_06_09 | EXPERIMENT_ONLY |
| 2024 | 18284 | 1464 | 1.104 | 1.428 | 0.323 | tmax_dminus1,slope_3h,warming_rate_06_09 | EXPERIMENT_ONLY |
| 2025 | 19748 | 1460 | 1.108 | 1.364 | 0.256 | tmax_dminus1,slope_3h,warming_rate_06_09 | EXPERIMENT_ONLY |

## Honest Null Table (train-only)

| month | cp | rw_median | n_train_rows | production_status |
| --- | --- | --- | --- | --- |
| 0 | 20:00 | 3.000 | 4187 | EXPERIMENT_ONLY |
| 1 | 20:00 | 3.000 | 355 | EXPERIMENT_ONLY |
| 2 | 20:00 | 4.000 | 309 | EXPERIMENT_ONLY |
| 3 | 20:00 | 3.000 | 341 | EXPERIMENT_ONLY |
| 4 | 20:00 | 2.500 | 332 | EXPERIMENT_ONLY |
| 5 | 20:00 | 2.000 | 342 | EXPERIMENT_ONLY |
| 6 | 20:00 | 2.000 | 331 | EXPERIMENT_ONLY |
| 7 | 20:00 | 2.000 | 338 | EXPERIMENT_ONLY |
| 8 | 20:00 | 2.000 | 351 | EXPERIMENT_ONLY |
| 9 | 20:00 | 3.000 | 360 | EXPERIMENT_ONLY |
| 10 | 20:00 | 3.000 | 371 | EXPERIMENT_ONLY |
| 11 | 20:00 | 3.000 | 361 | EXPERIMENT_ONLY |
| 12 | 20:00 | 3.000 | 396 | EXPERIMENT_ONLY |
| 0 | 21:00 | 2.000 | 4188 | EXPERIMENT_ONLY |
| 1 | 21:00 | 3.000 | 355 | EXPERIMENT_ONLY |
| 2 | 21:00 | 3.000 | 309 | EXPERIMENT_ONLY |
| 3 | 21:00 | 3.000 | 341 | EXPERIMENT_ONLY |
| 4 | 21:00 | 2.000 | 332 | EXPERIMENT_ONLY |
| 5 | 21:00 | 2.000 | 342 | EXPERIMENT_ONLY |
| 6 | 21:00 | 2.000 | 331 | EXPERIMENT_ONLY |
| 7 | 21:00 | 2.000 | 339 | EXPERIMENT_ONLY |
| 8 | 21:00 | 2.000 | 351 | EXPERIMENT_ONLY |
| 9 | 21:00 | 2.000 | 360 | EXPERIMENT_ONLY |
| 10 | 21:00 | 2.000 | 371 | EXPERIMENT_ONLY |
| 11 | 21:00 | 2.000 | 361 | EXPERIMENT_ONLY |
| 12 | 21:00 | 2.000 | 396 | EXPERIMENT_ONLY |
| 0 | 22:00 | 2.000 | 4189 | EXPERIMENT_ONLY |
| 1 | 22:00 | 2.000 | 355 | EXPERIMENT_ONLY |
| 2 | 22:00 | 2.000 | 310 | EXPERIMENT_ONLY |
| 3 | 22:00 | 2.000 | 341 | EXPERIMENT_ONLY |
| 4 | 22:00 | 2.000 | 332 | EXPERIMENT_ONLY |
| 5 | 22:00 | 2.000 | 342 | EXPERIMENT_ONLY |
| 6 | 22:00 | 1.000 | 331 | EXPERIMENT_ONLY |
| 7 | 22:00 | 2.000 | 339 | EXPERIMENT_ONLY |
| 8 | 22:00 | 2.000 | 351 | EXPERIMENT_ONLY |
| 9 | 22:00 | 2.000 | 360 | EXPERIMENT_ONLY |
| 10 | 22:00 | 2.000 | 371 | EXPERIMENT_ONLY |
| 11 | 22:00 | 2.000 | 361 | EXPERIMENT_ONLY |
| 12 | 22:00 | 2.000 | 396 | EXPERIMENT_ONLY |
| 0 | 23:00 | 1.000 | 4189 | EXPERIMENT_ONLY |
| 1 | 23:00 | 1.000 | 355 | EXPERIMENT_ONLY |
| 2 | 23:00 | 1.000 | 310 | EXPERIMENT_ONLY |
| 3 | 23:00 | 1.000 | 341 | EXPERIMENT_ONLY |
| 4 | 23:00 | 1.000 | 332 | EXPERIMENT_ONLY |
| 5 | 23:00 | 1.000 | 342 | EXPERIMENT_ONLY |
| 6 | 23:00 | 1.000 | 331 | EXPERIMENT_ONLY |
| 7 | 23:00 | 1.000 | 339 | EXPERIMENT_ONLY |
| 8 | 23:00 | 1.000 | 351 | EXPERIMENT_ONLY |
| 9 | 23:00 | 1.000 | 360 | EXPERIMENT_ONLY |
| 10 | 23:00 | 1.000 | 371 | EXPERIMENT_ONLY |
| 11 | 23:00 | 1.000 | 361 | EXPERIMENT_ONLY |
| 12 | 23:00 | 1.000 | 396 | EXPERIMENT_ONLY |
