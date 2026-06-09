# Regime Classifiability Feature Basis Audit - 2026-06-08

This audit is EXPERIMENT_ONLY and does not promote a production classifier.

- Basis mode: physical
- Included approved physical features: 8
- Forbidden numeric fallback attempted: False
- Valid for physical regime decisions: True

## Included Features

| Feature | Source | Missing Rate | Variance |
|---|---|---:|---|
| cloud_cover_score_mean | obs.skyc1 | 0.0895 | usable |
| dewpoint_depression_mean | obs.dw_depression_c_int or tmp-dwp | 0.0034 | usable |
| drct_cos_mean | obs.drct | 0.0033 | usable |
| drct_sin_mean | obs.drct | 0.0033 | usable |
| qnh_hpa_mean | obs.alti | 0.0033 | usable |
| relh_mean | obs.relh | 0.0038 | usable |
| sknt_mean | obs.sknt | 0.0033 | usable |
| temp_slope_pre_cp | obs.tmp_c_int | 0.0049 | usable |

## Rejected Features

| Feature | Leakage Class | Reason |
|---|---|---|
| cp | excluded_identifier | excluded by leakage class excluded_identifier |
| current_regime_label | excluded_quarantined_label | excluded by leakage class excluded_quarantined_label |
| date_local | excluded_identifier | excluded by leakage class excluded_identifier |
| month | excluded_identifier | excluded by leakage class excluded_identifier |
| n_pre_cp_obs | excluded_model_feature | excluded by leakage class excluded_model_feature |
| precip_pre_cp_sum | causal_input | excluded by variance status constant |
| remaining_warming | excluded_outcome | excluded by leakage class excluded_outcome |
| season | excluded_identifier | excluded by leakage class excluded_identifier |
| tmax_anomaly | excluded_outcome | excluded by leakage class excluded_outcome |