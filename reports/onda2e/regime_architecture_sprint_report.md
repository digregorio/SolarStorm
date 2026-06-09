# Regime Architecture Sprint Report - 2026-06-07

This report tests whether a fixed four-regime ontology is sufficient or whether Wellington needs month/season-aware regime structure.

## Artifacts

- `regime_cluster_sweep_by_month_season.csv`: 80 rows
- `regime_cluster_stability_by_year_bootstrap.csv`: 240 rows
- `regime_cluster_profiles.csv`: 320 rows
- `regime_cluster_physical_interpretation.csv`: 320 rows
- `regime_cluster_outcome_audit.csv`: 80 rows

## Interpretation Rule

A lower BIC/AIC or higher silhouette is not enough to promote a regime. A candidate also needs power, year stability, physical interpretability, and Onda 4 robustness.

## Best K By Approximate BIC

| Stratum | k | n rows | smallest cluster | eta2 Tmax anomaly |
|---|---:|---:|---:|---:|
| month=1 | 6 | 1623 | 162 | 0.270 |
| month=10 | 6 | 1595 | 159 | 0.338 |
| month=11 | 6 | 1580 | 146 | 0.313 |
| month=12 | 6 | 1705 | 187 | 0.217 |
| month=2 | 6 | 1514 | 147 | 0.365 |
| month=3 | 6 | 1727 | 176 | 0.289 |
| month=4 | 6 | 1608 | 172 | 0.360 |
| month=5 | 6 | 1695 | 204 | 0.358 |
| month=6 | 6 | 1558 | 204 | 0.269 |
| month=7 | 6 | 1535 | 146 | 0.438 |
| month=8 | 6 | 1576 | 127 | 0.398 |
| month=9 | 6 | 1544 | 139 | 0.388 |
| season=DJF | 6 | 4842 | 487 | 0.279 |
| season=JJA | 6 | 4669 | 480 | 0.372 |
| season=MAM | 6 | 5030 | 614 | 0.347 |
| season=SON | 6 | 4719 | 457 | 0.351 |

## Physical Interpretation Sample

| Stratum | k | cluster | n | family | signature | readiness |
|---|---:|---:|---:|---|---|---|
| month=1 | 2 | 0 | 572 | southerly_disrupted_candidate | southerly_flow;windy;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 2 | 1 | 1051 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 3 | 0 | 442 | southerly_disrupted_candidate | southerly_flow;windy;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 3 | 1 | 613 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 3 | 2 | 568 | mixed_or_transition | easterly_component | design_evidence_only |
| month=1 | 4 | 0 | 344 | southerly_disrupted_candidate | southerly_flow;windy;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 4 | 1 | 550 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 4 | 2 | 356 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 4 | 3 | 373 | southerly_disrupted_candidate | southerly_flow;windy | design_evidence_only |
| month=1 | 5 | 0 | 227 | southerly_disrupted_candidate | southerly_flow;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 5 | 1 | 503 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 5 | 2 | 236 | southerly_disrupted_candidate | southerly_flow;windy;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 5 | 3 | 395 | nw_or_foehn_candidate | northerly_nw_flow | design_evidence_only |
| month=1 | 5 | 4 | 262 | southerly_disrupted_candidate | southerly_flow;windy | design_evidence_only |
| month=1 | 6 | 0 | 162 | southerly_disrupted_candidate | southerly_flow;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 6 | 1 | 263 | southerly_disrupted_candidate | southerly_flow;windy;moist_cloudy_or_rain | design_evidence_only |
| month=1 | 6 | 2 | 400 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 6 | 3 | 307 | nw_or_foehn_candidate | northerly_nw_flow | design_evidence_only |
| month=1 | 6 | 4 | 204 | nw_or_foehn_candidate | northerly_nw_flow;windy | design_evidence_only |
| month=1 | 6 | 5 | 287 | southerly_disrupted_candidate | southerly_flow | design_evidence_only |