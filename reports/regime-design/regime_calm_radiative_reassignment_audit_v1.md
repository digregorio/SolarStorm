# Regime v2.2 Calm/Radiative Reassignment Audit - 2026-06-08

This is not a production classifier.
v2.2 restores calm/radiative from audited physical pre-CP signals.

- Assignment rows: 21824
- Calm/radiative rows: 2572

| Diagnostic | Status | Rows | Detail |
|---|---|---:|---|
| physical_thresholds | PASS | 21824 | wind_low_q25=7.125000; relh_high_q75=86.719091; dewpoint_depression_low_q25=2.181818; cloud_cover_high_q75=2.705882; temp_slope_weak_q25=0.000000 |
| calm_radiative_candidate_rows | PASS | 2572 | 2572 rows meet the v2.2 calm/radiative physical rule. |
| calm_radiative_cp_support | PASS | 502 | Smallest CP support for calm/radiative is 502 rows. |
| missing_physical_rule_inputs | WARN | 1995 | 1995 joined rows have at least one missing rule input. |
| production_status | PASS | 21824 | v2.2 assignments remain NOT_PRODUCTION. |