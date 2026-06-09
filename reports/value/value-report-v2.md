# SolarStorm Value Report v2 - Onda 2 Feature-Null Evidence

Generated: 2026-06-05

This report uses fresh artifacts generated after the Wave 3 validation fixes.
It supersedes `value-report-v1.md`, which remains marked as non-decisionable.
This is model-foundation evidence only. It does not authorize shadow decisions,
live trading, EV calculation, market pricing, or real-money position sizing.
Those layers remain on hold until a production model proves predictive skill,
calibrated uncertainty, and stay-out behavior.

## Artifact Lineage

| Artifact | Path |
|---|---|
| Feature table | `data/features.parquet` |
| Feature coverage | `reports/2026-06-05/feature_coverage.json` |
| Hypothesis results | `reports/2026-06-05/hypothesis_results.json` |
| Validated contract | `reports/2026-06-05/validated_feature_contract.json` |
| Leaderboard | `reports/leaderboard/2026-06-05T1413Z-leaderboard.json` |
| Leaderboard alias | `reports/leaderboard/latest-leaderboard.json` |

## Validation Summary

| Metric | Value |
|---|---:|
| Hypotheses tested | 88 |
| Validated | 33 |
| Rejected | 55 |
| Blocked | 4 |
| Computable feature columns | 22 |
| Blocked feature columns | 1 |

All 33 validated entries beat `calibrated_cp_mean_rw`, the train-only calibrated
remaining-warming null selected inside the walk-forward validation loop.

Validated entries by CP:

| CP | Count |
|---|---:|
| 20:00 | 4 |
| 21:00 | 11 |
| 22:00 | 7 |
| 23:00 | 11 |

## Best Validated Effects

| ID | Feature | CP | Effect | CI low | CI high | Best null | Null MAE |
|---|---|---:|---:|---:|---:|---|---:|
| H10 | `precip_disruption` | 21:00 | 0.1557 | 0.1328 | 0.1769 | `calibrated_cp_mean_rw` | 1.4390 |
| H10 | `precip_disruption` | 20:00 | 0.1437 | 0.1143 | 0.1729 | `calibrated_cp_mean_rw` | 1.6474 |
| H17 | `warming_rate_06_09` | 21:00 | 0.1111 | 0.0878 | 0.1350 | `calibrated_cp_mean_rw` | 1.3086 |
| H1 | `slope_3h` | 21:00 | 0.1111 | 0.0878 | 0.1350 | `calibrated_cp_mean_rw` | 1.3086 |
| H6 | `tmin_delta_tmax` | 21:00 | 0.1082 | 0.0902 | 0.1253 | `calibrated_cp_mean_rw` | 1.4390 |
| H6 | `tmin_delta_tmax` | 20:00 | 0.0968 | 0.0723 | 0.1226 | `calibrated_cp_mean_rw` | 1.6474 |
| H12 | `cloud_cover_suppression` | 21:00 | 0.0864 | 0.0727 | 0.1010 | `calibrated_cp_mean_rw` | 1.3633 |
| H17 | `warming_rate_06_09` | 22:00 | 0.0553 | 0.0398 | 0.0692 | `calibrated_cp_mean_rw` | 1.1050 |
| H1 | `slope_3h` | 22:00 | 0.0553 | 0.0398 | 0.0692 | `calibrated_cp_mean_rw` | 1.1050 |
| H20 | `dewpoint_collapse_rate_3h` | 21:00 | 0.0549 | 0.0355 | 0.0737 | `calibrated_cp_mean_rw` | 1.3086 |

## Recent Baseline Leaderboard

Window: 2026-05-06 to 2026-06-04.

| CP | Best recent null | MAE | RMSE | Bracket match | Fallback |
|---|---|---:|---:|---:|---:|
| 20:00 | `empirical_conditional` | 1.4286 | 2.0000 | 0.3214 | 0.2500 |
| 21:00 | `empirical_conditional` | 1.4643 | 2.0959 | 0.3571 | 0.2143 |
| 22:00 | `empirical_conditional` | 1.2500 | 1.9365 | 0.3571 | 0.2143 |
| 23:00 | `empirical_conditional` | 1.1786 | 1.8028 | 0.3571 | 0.1429 |

## Recent Feature-Null Rows

Lowest recent MAE rows from `latest-leaderboard.json`:

| Feature | CP | MAE | n | Corr diff |
|---|---:|---:|---:|---:|
| `cloud_cover_suppression` | 23:00 | 0.7308 | 26 | 0.0000 |
| `cloud_base_transparency` | 23:00 | 0.7308 | 26 | 0.0000 |
| `tmin_delta_tmax` | 23:00 | 0.7500 | 28 | 0.0231 |
| `warming_rate_06_09` | 23:00 | 0.7857 | 28 | 0.0001 |
| `slope_3h` | 23:00 | 0.7857 | 28 | 0.0001 |
| `dewpoint_collapse_rate_3h` | 23:00 | 0.7857 | 28 | -0.0016 |
| `regime_score_argmax` | 23:00 | 0.8214 | 28 | 0.0000 |
| `foehn_score` | 23:00 | 0.8214 | 28 | 0.0000 |
| `dewpoint_collapse_rate_3h` | 22:00 | 0.8929 | 28 | 0.0318 |
| `precip_disruption` | 22:00 | 0.9286 | 28 | 0.0200 |

## Onda 4 Robustness Handoff

Status: ready to enter Onda 4 robustness hardening, not ready for financial or
market-operation work.

Reasons:

- Fresh validation artifacts now exist and are not marked superseded.
- The validated contract records `best_null_name` and `best_null_mae`.
- The validation best null is calibrated and train-only.
- The leaderboard has fresh timestamped artifacts plus `latest-*` aliases.
- The Onda 4 scope is now robustness hardening: per-year replication, regime
  sensitivity, drift, causal re-audit, anti-nowcast lead-time checks,
  physical Tmax-hour stratification, and late-spike evidence.
- CI-critical checks (`ruff check .`, non-network pytest) pass locally.

Residual constraints:

- Onda 4 must not run in financial/shadow mode.
- Feature generation is slow on the current dataset and took several minutes in
  the validation run; future continuous-update work should monitor runtime.
- Onda 3 model promotion is still separate and remains blocked until the Onda 4
  robustness report has no blocking failures.
- CPs are evaluation cutoffs, not fixed physical Tmax timing. Onda 4 must test
  whether apparent skill survives regime/month/Tmax-hour stratification and is
  not merely nowcasting.
- Late-spike cases must be preserved for future modeling, especially when
  Open-Meteo/NWP inputs are investigated.
