# ADR-005: Multi-CP Design

- **Date:** 2026-06-04
- **Status:** Accepted

## Context

Polymarket NZWN Tmax contracts settle at known UTC checkpoint hours. For Wellington (UTC+12/UTC+13), the Polymarket daily contracts use UTC 20:00, 21:00, 22:00, and 23:00 as checkpoints. These correspond to 08:00-11:00 NZST or 09:00-12:00 NZDT -- the local morning window.

A forecaster must produce predictions at each checkpoint independently. This is not a time-series forecast with one target; it is four parallel forecasts with different information sets (later checkpoints have more intraday observations). The checkpoints are not interchangeable -- a feature valid at 23:00 UTC is causally invalid at 20:00 UTC.

The fixed CP set is a contractual/evaluation grid, not a claim that Tmax timing
is fixed. Regime and month can shift the physically plausible Tmax hour. Onda 4
must therefore evaluate skill by lead time and Tmax-hour buckets, not only by
the fixed CP labels.

## Decision

**Independent evaluation per CP with best-null-per-CP comparison, plus
physical-time stratification.**

`CP_SET_UTC = ("20:00", "21:00", "22:00", "23:00")` is the contractual checkpoint set, defined in `solarstorm/_config.py`. CP hours are interpreted as **UTC** (METAR convention), mapped to local dates via `cp_to_utc()` in `solarstorm/data/_calendar.py`.

For Wellington, UTC CPs 20:00-23:00 fall on UTC date D-1 and correspond to local morning on date D. The calendar function tries both UTC date D and D-1 to ensure the CP lands on the correct local date.

Each label row gets per-CP columns: `k_cp__cp_2000`, `k_cp__cp_2100`, `k_cp__cp_2200`, `k_cp__cp_2300` -- the maximum `tmp_c_int` observed strictly before that CP on that day.

The validation harness (`validate_hypotheses()`) evaluates each hypothesis independently against each CP. The best baseline null can differ per CP (e.g., persistence may be best at early CPs, dminus1 at later ones). G5 (`_g5_per_cp`) enforces that a validated feature must beat the best null for its specific CP.

For robustness, CP evaluation must be separated from continuous data updates.
The system should keep ingesting and processing METAR observations after a CP
has passed; that later processing updates the day state and late-spike evidence,
but it cannot be used to score predictions made at an earlier CP.

Late spikes are a special risk class: days where `k_cp` appears settled but a
new Tmax occurs later. They are central to future model design because they are
where a merely average forecast and a genuinely predictive physical model
diverge.

## Alternatives Considered

1. **Single operational CP (23:00 only):** Evaluate only the latest CP. Rejected -- earlier CPs are where predictive value is highest (more remaining warming to forecast), and the Polymarket contract structure explicitly defines multiple CPs.
2. **Pooled CP evaluation:** Average performance across all CPs. Rejected -- masks CP-specific behavior and allows a feature that only works at late CPs (when `k_cp` is already close to Tmax) to appear effective on average.
3. **Dynamic CP selection:** Let the model choose which CP to forecast. Rejected -- violates the contractual structure; each CP is a separate Polymarket market.
4. **CP-only physical evaluation:** Treat CP labels as sufficient physical timing. Rejected -- this can reward nowcasting and hide regimes/months where Tmax occurs outside the fixed morning grid.

## Consequences

### Enabled
- CP-specific feature validation: a feature that helps at 20:00 UTC (early morning, lots of warming left) is not penalized if it adds no value at 23:00 UTC (when `k_cp` is near Tmax).
- The best-null-per-CP pattern in the leaderboard (`best_null_for_cp()`).
- Operational clarity: each CP has its own validated feature set.
- Continuous METAR updates can support day-state tracking without contaminating
  earlier CP evaluation.
- Onda 4 can test whether skill is predictive or merely an artifact of being
  close to the answer.

### Prevents
- Conflating information sets across CPs (the causal firewall is enforced per-CP).
- A single "average" null baseline masking CP-specific weakness.
- Treating fixed CP timestamps as physical Tmax timing.
- Stopping data processing after a CP just because that evaluation cutoff has
  passed.

## References

- `solarstorm/_config.py` -- `CP_SET_UTC`, `CP_OPERATIONAL`
- `solarstorm/data/_calendar.py` -- `cp_to_utc()`
- `solarstorm/data/_labels.py` -- Per-CP k_cp column generation
- `solarstorm/eda/_validate.py` -- Per-CP walk-forward loop
- `solarstorm/baselines/_ladder.py` -- `best_null_for_cp()`
