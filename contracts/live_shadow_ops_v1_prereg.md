# Live Shadow Ops v1 Pre-Registration Contract (Phase 5.1)

**LIVE_SHADOW_OPS_VERSION = 1.0**

**Status:** Pre-registered (frozen BEFORE examining operational results)  
**Created:** 2026-06  
**Owner:** Wellington Forecasting Team

---

## 1. Purpose

This contract defines the criteria for promoting a shadow-mode forecast/decision
system to production trading. All criteria are frozen before examining any
operational results from the shadow period.

## 2. Non-Goals (Explicit Exclusions)

The following are **NOT** part of this promotion contract:

- **No automatic trading.** Shadow mode never places real orders.
- **Production default unchanged.** The current Ridge/served_v0 system remains
  the production baseline throughout the shadow period.
- **PnL-based promotion.** Promotion decisions are NOT based on market PnL,
  simulated returns, or betting performance.

## 3. Minimum Observation Window

Before any promotion evaluation:

- **Minimum days:** 30 consecutive days of shadow operation
- **Minimum CP-days:** 90 CP-day observations (e.g., 30 days x 3 CPs = 90)
- **Checkpoint coverage:** Must include CP20, CP21, CP22 (UTC)

If the observation window is not met, promotion evaluation is deferred.

## 4. Readiness Gates (Frozen)

These gates must ALL pass for the system to be considered "operationally ready":

| Gate | Threshold | Rationale |
|------|-----------|-----------|
| `completeness` | == 1.0 (100%) | All expected forecasts must be present |
| `leakage_violations` | == 0 | Zero tolerance for data leakage |
| `fallback_reasons_classified` | == 1.0 (100%) | Every fallback must have a documented reason |

**Gate values are frozen constants in `scripts/live_shadow_readiness_report.py`.**
Changing a gate threshold requires a new pre-registration contract.

## 5. Promotion Criteria (Three Separate Dimensions)

Promotion requires passing ALL three dimensions independently:

### 5.1 Readiness (Operational Capability)

- All gates in Section 4 pass
- Shadow runner produces valid JSONL output for 100% of expected dates
- No unclassified errors or silent failures

### 5.2 Predictive Quality

- MOS/EMOS-lite evaluation shows `coverage_ok == true` for all folds
- Calibration metrics (ECE, IC80 coverage) within pre-registered bounds
- No degradation in served_v0 performance during shadow period

### 5.3 Operational Capability

- NWP fetch success rate >= 95%
- Cache hit rate documented (no hard threshold, but must be reported)
- run_age_h p95 < 18 hours (NWP data reasonably fresh)
- Fallback rate < 10% for CP20-22

## 6. Evaluation Process

1. **Run readiness report:** `scripts/live_shadow_readiness_report.py`
2. **Verify gates:** All gates must show "PASS"
3. **Review metrics:** Examine fallback distribution, NWP telemetry
4. **Build promotion pack:** `scripts/live_shadow_promotion_review.py`
5. **Decision:** `KEEP_SHADOW`, `EXTEND_SHADOW`, or `PROMOTE_SERVING_DEFAULT`

The promotion pack is evidence only. It does not enable automatic trading.

## 7. Rollback Plan

If a promoted system causes issues in production:

1. Immediately revert to `served_v0` (the Ridge baseline)
2. Document the incident in postmortem
3. Shadow system returns to shadow mode until root cause fixed

## 8. Amendment Process

Changes to this contract require:

1. New contract document with version bump
2. Explicit rationale for each change
3. Sign-off from contract owner
4. Changes apply prospectively (not retroactively)

---

## Appendix A: Metric Definitions

| Metric | Definition |
|--------|------------|
| `completeness` | found_records / expected_records |
| `leakage_violations` | Count of forecasts where any NWP run_time (nwp_run_time_utc, ecmwf_selected_run_time, gfs_selected_run_time) > cp_utc - 60 min safety margin |
| `fallback_rate` | fallback_used_count / total_with_routing |
| `fallback_classified_rate` | classified / (classified + unclassified) |
| `run_age_h` | Hours between NWP run_time_utc and current time |
| `valid_time_delta_h` | Hours between forecast valid_time and target time |
| `unexpected_cp_records` | Count of CP records outside the contracted set (e.g. CP19 when only 20-23 are expected) |

## Appendix B: Related Documents

- `scripts/live_shadow_readiness_report.py` - Readiness report implementation
- `scripts/live_shadow_promotion_review.py` - Promotion review pack implementation
- `core/ops/shadow_runner.py` - Shadow runner implementation
- `contracts/phase5_preregistration.md` - Phase 5 prediction quality gates
- `contracts/phase5_amendment.md` - Phase 5 amendment process
