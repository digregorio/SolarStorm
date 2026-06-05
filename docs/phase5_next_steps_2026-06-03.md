# Phase 5.1+ Next Steps - Shadow Ops and Promotion Path

Created: 2026-06-03

This plan starts the next project phase after the Shadow Ops readiness patch.
The goal is to move from small reviewer fixes to measurable operational
progress, without enabling automatic trading.

## Wave 0 - Close Phase 5.1

Scope: consolidate Shadow Ops v1 and commit the base.

Deliverables:
- `core/ops/schemas.py`
- `core/ops/shadow_runner.py`
- `scripts/run_shadow_ops_v1.py`
- `scripts/live_shadow_readiness_report.py`
- `contracts/live_shadow_ops_v1_prereg.md`
- `docs/live_shadow_runbook.md`
- unit tests for schema, runner, readiness, and forecast-decision linkage

Gates:
- full suite green
- `git diff --check` clean
- `compileall` clean
- readiness counts only contracted CPs
- leakage uses the causal cutoff `cp_utc - 60min`
- anomaly metrics are visible: `unexpected_cp_records`, `duplicate_cp_records`
- local artifacts and logs are excluded from the commit

## Wave 1 - Shadow Decisions

Objective: extend the forecast runner into a forecast -> decision shadow chain,
while keeping production defaults and real trading unchanged.

Deliverables:
- `ShadowRunnerConfig.with_decisions`
- `core/ops/decision_runner.py` or a narrow extension of `shadow_runner.py`
- `scripts/run_shadow_ops_v1.py --with-decisions`
- `artifacts/shadow_ops/decisions/{date}.jsonl`
- mandatory linkage fields: `forecast_run_id`, `forecast_file`,
  `forecast_model_version`
- readiness odds status by date and CP

Tests:
- decision consumes the forecast JSON probability distribution exactly
- forecast date/CP mismatch fails
- unavailable odds still produce an auditable decision artifact
- decision JSONL is idempotent and repairable
- `--with-decisions` cannot place live orders

## Wave 2 - Live Shadow Window

Objective: collect 7-14 days of live shadow data before any promotion review.

Deliverables:
- `reports/live_shadow/readiness_v1.json`
- `reports/live_shadow/readiness_v1.md`
- `reports/live_shadow/shadow_ops_weekly_v1.md`
- missing date/CP inventory
- fallback distribution by CP and model
- NWP fetch/cache summary by endpoint

Metrics:
- `completeness`
- `leakage_violations`
- `fallback_rate`
- `residual_served_rate_cp20_22`
- `ecmwf_fetch_success`, `gfs_fetch_success`
- `ecmwf_cache_repair`, `gfs_cache_repair`
- `run_age_h_p50`, `run_age_h_p95`
- `valid_time_delta_h_mean`
- `odds_available`, `odds_unavailable`
- `unexpected_cp_records`, `duplicate_cp_records`

## Wave 3 - Shadow Ops Production Loop

Objective: turn readiness reports into a repairable operating loop. The system
must be able to measure a window, identify missing dates/CPs, repair the
affected dates, and regenerate readiness without manual JSONL inspection.

Deliverables:
- `scripts/shadow_ops_repair_window.py`
- `reports/live_shadow/shadow_window_{start}_{end}.json`
- `reports/live_shadow/shadow_window_{start}_{end}.md`
- `reports/live_shadow/shadow_repair_{start}_{end}.json`
- `reports/live_shadow/shadow_repair_{start}_{end}.md`
- runbook commands for measure -> repair -> measure

Tests:
- whole missing dates appear in `missing_inventory`
- partial missing CPs are repaired by date
- dry-run writes a plan without invoking forecasts
- repair execution calls the runner only for planned dates
- explicit readiness windows write stable `shadow_window_*` artifacts

Gates:
- full suite green
- `compileall` clean
- `git diff --check` clean
- no automatic trading activation
- `--with-decisions` remains dry-run only

## Wave 4 - Promotion Review

Objective: decide whether residual serving can become the operational serving
default. This is not approval for automatic trading.

Deliverables:
- `scripts/live_shadow_promotion_review.py`
- `reports/live_shadow/promotion_review_v1.json`
- `reports/live_shadow/promotion_review_v1.md`
- checklist against `contracts/live_shadow_ops_v1_prereg.md`
- one of: `KEEP_SHADOW`, `EXTEND_SHADOW`, `PROMOTE_SERVING_DEFAULT`
- explicit `read_only_no_trading_change` status

Promotion gates:
- leakage = 0
- completeness = 1.0 over the frozen window
- all fallback reasons classified
- residual served rate and fallback rate reported without tuning
- minimum 30 consecutive days
- minimum 90 CP20-22 observations
- NWP fetch success rate >= 0.95
- run_age_h p95 < 18h
- CP20-22 fallback rate < 0.10
- MOS/EMOS evidence available and promotion-ready
- no JSON contract regression
- no automatic trading activation

Tests:
- short windows return `EXTEND_SHADOW`
- readiness failures return `KEEP_SHADOW`
- missing predictive-quality evidence returns `EXTEND_SHADOW`
- promotion requires every readiness and promotion check to pass
- JSON/MD promotion pack exposes verdict and no-trading status

## Parallel Agents

- Agent A: implement `--with-decisions` and decision JSONL.
- Agent B: readiness and promotion reports.
- Agent C: contract, runbook, plan, changelog.
- Agent D: QA, negative tests, full suite, diff-check, compileall, staging audit.

Execution rule: agents may work in parallel within a wave, but commits should
remain small and ordered. Close Wave 0 first, then build Wave 1. Wave 2 starts
only after the runner is stable. Wave 3 starts once the readiness dashboard has
an actionable missing inventory. Wave 4 starts only after live shadow data
exists over a frozen review window.

## Wave 4.1 - Operational Value Audit

Objective: stop treating shadow artifacts as proof of value. A forecast is
operationally useful only if it consumes fresh 30-minute METAR data, reports
freshness telemetry, and finishes inside a known latency budget.

Delivered/required:
- `python -m tmax` entrypoint for operational commands
- `scripts/run_live_forecast_once.py` refreshes live METAR before forecasting
- `ingest-live --out-csv` writes a forecast-consumable IEM-style CSV with
  `valid` and `metar`
- forecast JSON exposes `feature_max_ts_utc`, `feature_gap_to_cp_min`, and
  `k_cp_available`
- `build_empirical_panel_fast()` avoids the old multi-minute empirical panel
  rebuild
- `scripts/profile_forecast_pipeline.py` profiles load, labels, empirical
  panel, target CP features, and optional rich Ridge panel samples

Current evidence:
- With stale `NZWN.csv`, the 2026-06-04 CP20 empirical forecast emitted JSON but
  had `feature_gap_to_cp_min=9870` and `k_cp_available=false`; this is not live
  usable.
- After `ingest-live`, CP20 for 2026-06-04 had `feature_gap_to_cp_min=30`,
  `k_cp_available=true`, p50=15, IC80=[12,17].
- The empirical preprocessing profile on the refreshed CSV was roughly:
  load observations 1.15s, labels 2.38s, fast empirical panel 0.33s,
  climatology 0.01s, empirical fit 0.05s, target CP features 0.02s.
- `forecast --model auto --no-nwp-probe` timed out at 45s before the rich-panel
  reduction; auto/ridge must remain blocked until measured and optimized.

Wave 4.2 must prove predictive value before more promotion machinery:
- recent rolling backtest using only data available before each CP
- report MAE/RPS/Brier by CP for empirical, Ridge, residual, and climatology
- CP-readiness-stratified performance (`feature_gap_to_cp_min <= 30/60/90`)
- value-null baseline: climatology and persistence/T-so-far
- no promotion unless the candidate beats the null baselines on fresh-data
  windows with predeclared gates

## Wave 4.2 - Recent Holdout Value Check

Objective: use the real gap between the frozen historical CSV and live-updated
truth as an immediate forecast-vs-truth check.

Delivered:
- `scripts/evaluate_recent_holdout_backtest.py`
- `reports/forecast_value/recent_holdout_v1.json`
- `reports/forecast_value/recent_holdout_v1.md`
- empirical training now ignores `day_complete=false` rows when that column is
  present

Run:

```bash
python scripts/evaluate_recent_holdout_backtest.py \
  --base-csv NZWN.csv \
  --eval-csv artifacts/state/NZWN_live_merged.csv
```

Current result:
- train frozen at `2026-05-27`, the last `day_complete` date in `NZWN.csv`
- holdout `2026-05-28..2026-06-03`, 7 complete days, 28 CP cells
- verdict `NULL_NOT_BEATEN`
- empirical MAE `2.3214`
- best null by MAE `dminus1`, MAE `2.0000`
- empirical fallback_marginal rate `0.9286`
- empirical IC80 coverage `0.7143` on this tiny holdout

Interpretation:
- This is not enough N for promotion, but it is enough to reject any claim that
  the current empirical path has demonstrated concrete predictive value.
- The conditional empirical model is mostly falling back to monthly marginals,
  so the CP signal is barely being used in the recent gap.
- Next work should prioritize a larger rolling-origin value report and a simple
  persistence-aware baseline before more promotion/readiness machinery.

Expanded checks:
- `reports/forecast_value/recent_holdout_2026-05-01_2026-06-03.*`:
  train_end `2026-04-30`, 34 complete days, 136 CP cells, verdict
  `NULL_NOT_BEATEN`; empirical MAE `1.5882` vs best null climatology MAE
  `1.4706`; fallback_marginal rate `0.8676`.
- `reports/forecast_value/recent_holdout_2026-04-01_2026-06-03.*`:
  train_end `2026-03-31`, 64 complete days, 256 CP cells, verdict
  `NULL_NOT_BEATEN`; empirical MAE `1.7930` vs best null D-1 MAE `1.5156`;
  fallback_marginal rate `0.7852`.

Immediate implication:
- The current empirical forecaster is not merely under-proven; on recent
  frozen-cutoff windows it is worse than trivial null baselines in MAE and
  bracket match.
- Promotion work remains blocked. The next model work must start from value
  baselines and failure rows, not from serving/readiness polish.
