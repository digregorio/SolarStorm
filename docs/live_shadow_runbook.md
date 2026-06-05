# Live Shadow Ops Runbook (Phase 5.1)

Operational guide for running and monitoring the shadow forecast system.

---

## Quick Start

### 1. Run Shadow Forecasts (Single Date)

```bash
python scripts/run_shadow_ops_v1.py --date 2025-06-03
```

Output: `artifacts/shadow_ops/forecasts/2025-06-03.jsonl` (4 lines for CP20-23)

### 1a. Refresh Live METAR Before Forecasting

The historical `NZWN.csv` is not automatically fresh. For a live forecast, first
merge the latest 30-minute METAR observations into a runtime CSV:

```bash
python -m tmax ingest-live \
  --csv NZWN.csv \
  --hours 168 \
  --out-csv artifacts/state/NZWN_live_merged.csv
```

Then forecast against the refreshed CSV:

```bash
python -m tmax forecast \
  --csv artifacts/state/NZWN_live_merged.csv \
  --date 2026-06-04 \
  --cp 20 \
  --model empirical \
  --dry-run
```

Or use the wrapper:

```bash
python scripts/run_live_forecast_once.py --date 2026-06-04 --cp 20 --model empirical
```

Always inspect:
- `feature_max_ts_utc`
- `feature_gap_to_cp_min`
- `k_cp_available`

A forecast with `feature_gap_to_cp_min > 90` or `k_cp_available=false` is not
CP-ready even if it returns valid JSON. Feed freshness itself comes from the
`ingest-live` health JSON (`last_obs_ts_utc`, `staleness_minutes`, and
`max_gap_minutes_recent`).

For operational runs, prefer the wrapper because it refreshes METAR first and
fails closed when freshness telemetry is bad:

```bash
python scripts/run_live_forecast_once.py --date 2026-06-04 --cp 20 --model empirical
```

Use `--allow-stale` only for diagnostics. A successful live forecast must have
`feature_gap_to_cp_min <= 90` and `k_cp_available=true`.

### 2. Run Shadow Forecasts (Date Range)

```bash
python scripts/run_shadow_ops_v1.py --start 2025-06-01 --end 2025-06-07
```

### 3. Force Re-run (Overwrite Existing)

```bash
python scripts/run_shadow_ops_v1.py --date 2025-06-03 --force
```

### 4. Generate Readiness Report

```bash
python scripts/live_shadow_readiness_report.py --shadow-root artifacts/shadow_ops
```

Output:
- `reports/live_shadow/readiness_v1.json`
- `reports/live_shadow/readiness_v1.md`
- `reports/live_shadow/shadow_ops_weekly_v1.md`
- `reports/live_shadow/shadow_window_{start}_{end}.json` when `--start/--end` are provided
- `reports/live_shadow/shadow_window_{start}_{end}.md` when `--start/--end` are provided

### 4a. Profile Forecast Runtime

```bash
python scripts/profile_forecast_pipeline.py --date 2026-06-04 --cp 20
```

This separates CSV load, label building, empirical panel fitting, target feature
build, and empirical fit timing. Use it before changing model logic.

To sample the rich Ridge/auto panel cost without waiting for a full multi-year
run:

```bash
python scripts/profile_forecast_pipeline.py \
  --date 2026-06-04 \
  --cp 20 \
  --rich-panel-sample-days 90
```

The empirical path is the only currently fast live path. Ridge/auto still
rebuilds a rich historical training panel and refits inside the forecast call;
do not promote it until this path is cached or vectorized and profiled.

### 4b. Run Recent Holdout Value Check

After refreshing the live CSV and once recent days are `day_complete`, run the
frozen-cutoff value check:

```bash
python scripts/evaluate_recent_holdout_backtest.py \
  --base-csv NZWN.csv \
  --eval-csv artifacts/state/NZWN_live_merged.csv
```

Output:
- `reports/forecast_value/recent_holdout_v1.json`
- `reports/forecast_value/recent_holdout_v1.md`

This report compares the empirical forecast against climatology, `t_so_far`,
and D-1 persistence on the natural gap between the frozen historical CSV and
the live-updated truth. A readiness report is not a substitute for this check.

### 5. Repair a Readiness Window

Dry-run the repair plan first:

```bash
python scripts/shadow_ops_repair_window.py \
  --start 2025-06-01 \
  --end 2025-06-07 \
  --dry-run
```

Execute the repair and regenerate readiness:

```bash
python scripts/shadow_ops_repair_window.py \
  --start 2025-06-01 \
  --end 2025-06-07 \
  --with-decisions \
  --regenerate-readiness
```

Output:
- `reports/live_shadow/shadow_repair_{start}_{end}.json`
- `reports/live_shadow/shadow_repair_{start}_{end}.md`

### 6. Build Promotion Review Pack

Only run this after the frozen shadow window is complete and readiness has been
regenerated.

```bash
python scripts/live_shadow_promotion_review.py \
  --start 2025-06-01 \
  --end 2025-06-30 \
  --git-sha $(git rev-parse HEAD)
```

Output:
- `reports/live_shadow/promotion_review_v1.json`
- `reports/live_shadow/promotion_review_v1.md`

Allowed verdicts:
- `KEEP_SHADOW`
- `EXTEND_SHADOW`
- `PROMOTE_SERVING_DEFAULT`

This review pack never enables automatic trading.

---

## Daily Operations

### Morning Checklist

1. **Verify yesterday's shadow run completed:**
   ```bash
   ls -la artifacts/shadow_ops/forecasts/$(date -d yesterday +%Y-%m-%d).jsonl
   ```

2. **Check for errors:**
   ```bash
   # Use the readiness report (not wc -l) to detect incompleteness.
   # Duplicates or unexpected CPs do NOT count as coverage.
   python scripts/live_shadow_readiness_report.py \
     --shadow-root artifacts/shadow_ops \
     --start $(date -d yesterday +%Y-%m-%d) \
     --end $(date -d yesterday +%Y-%m-%d)
   ```

3. **Run readiness report (weekly):**
   ```bash
   python scripts/live_shadow_readiness_report.py \
     --start $(date -d '30 days ago' +%Y-%m-%d) \
     --end $(date -d yesterday +%Y-%m-%d)
   ```

### Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| File missing | Runner didn't execute | Run `scripts/shadow_ops_repair_window.py --start DATE --end DATE` |
| Readiness completeness < 1.0 | Missing dates, missing CPs, duplicates, or unexpected CPs | Check `missing_inventory`, then run the repair window |
| `fallback_used: true` in records | NWP fetch failed | Check network, ECMWF/GFS status |
| Readiness gate FAIL | Incomplete data or unclassified fallback | Repair the window, regenerate readiness, then inspect remaining gates |

---

## Configuration

### Shadow Runner Options

| Option | Default | Description |
|--------|---------|-------------|
| `--shadow-root` | `artifacts/shadow_ops` | Output directory |
| `--cps` | `20,21,22,23` | Checkpoint hours (UTC) |
| `--force` | `false` | Overwrite existing files |
| `--timeout` | `120` | Subprocess timeout (seconds) |

### Readiness Report Options

| Option | Default | Description |
|--------|---------|-------------|
| `--shadow-root` | `artifacts/shadow_ops` | Input directory |
| `--start` | (none) | Start date filter |
| `--end` | (none) | End date filter |
| `--out-root` | `reports/live_shadow` | Output directory |
| `--git-sha` | `unknown` | Git SHA for report |

### Repair Window Options

| Option | Default | Description |
|--------|---------|-------------|
| `--shadow-root` | `artifacts/shadow_ops` | Input/output shadow directory |
| `--out-root` | `reports/live_shadow` | Repair report output directory |
| `--start` | required | Start date |
| `--end` | required | End date |
| `--dry-run` | `false` | Write the repair plan without executing forecasts |
| `--with-decisions` | `false` | Regenerate dry-run decision artifacts after forecasts |
| `--regenerate-readiness` | `false` | Re-run readiness report after repair |
| `--force` | `false` | Force rerun selected dates |

### Promotion Review Options

| Option | Default | Description |
|--------|---------|-------------|
| `--shadow-root` | `artifacts/shadow_ops` | Input shadow directory |
| `--out-root` | `reports/live_shadow` | Promotion pack output directory |
| `--start` | required | Frozen window start date |
| `--end` | required | Frozen window end date |
| `--mos-report` | `reports/serving/mos_emos_lite_v0.json` | Predictive-quality evidence |
| `--git-sha` | `unknown` | Git SHA for traceability |

---

## Output Formats

### Forecast JSONL Schema

Each line in `forecasts/{date}.jsonl` contains:

```json
{
  "run_id": "uuid",
  "date_local": "2025-06-03",
  "cp_utc": "2025-06-03T20:00:00+00:00",
  "prob_dist": {"18": 0.3, "19": 0.5, "20": 0.2},
  "model_version": "phase3-ridge-band-v1.0",
  "routing": {
    "model_route": "ecmwf",
    "served_model": "ridge",
    "fallback_used": false,
    "fallback_reason": null,
    "ecmwf_cache_hit": true,
    "ecmwf_fetch_status": "success",
    "run_age_h": 6.5,
    "valid_time_delta_h": 12.0
  },
  "p50_int": 19,
  "ic80_low_int": 17,
  "ic80_high_int": 21
}
```

### Readiness Report Metrics

See `contracts/live_shadow_ops_v1_prereg.md` for metric definitions and gate thresholds.

---

## Scheduling (Recommended)

For automated daily execution via cron:

```cron
# Run shadow forecasts at 00:30 UTC daily (after NWP cycles available)
30 0 * * * cd /path/to/Wellington && python scripts/run_shadow_ops_v1.py --date $(date -d yesterday +%Y-%m-%d)

# Generate weekly readiness report (Monday 01:00 UTC)
0 1 * * 1 cd /path/to/Wellington && python scripts/live_shadow_readiness_report.py --start $(date -d '30 days ago' +%Y-%m-%d) --end $(date -d yesterday +%Y-%m-%d)

# Repair the weekly window after the report exposes missing inventory
15 1 * * 1 cd /path/to/Wellington && python scripts/shadow_ops_repair_window.py --start $(date -d '30 days ago' +%Y-%m-%d) --end $(date -d yesterday +%Y-%m-%d) --with-decisions --regenerate-readiness

# Build a monthly promotion pack without changing serving or trading
0 2 1 * * cd /path/to/Wellington && python scripts/live_shadow_promotion_review.py --start $(date -d '30 days ago' +%Y-%m-%d) --end $(date -d yesterday +%Y-%m-%d) --git-sha $(git rev-parse HEAD)
```

---

## Incident Response

If shadow system produces unexpected results:

1. **Stop shadow runner** (if scheduled)
2. **Document the issue** in postmortem
3. **Identify root cause** (NWP, cache, schema validation)
4. **Fix and re-run** affected dates with `scripts/shadow_ops_repair_window.py`
5. **Re-generate readiness report** to verify fix

---

## Related Documents

- `contracts/live_shadow_ops_v1_prereg.md` - Promotion criteria
- `core/ops/shadow_runner.py` - Implementation
- `scripts/live_shadow_readiness_report.py` - Report generator
- `scripts/shadow_ops_repair_window.py` - Repair loop for missing readiness windows
- `scripts/live_shadow_promotion_review.py` - Read-only promotion review pack
