# SolarStorm Baseline Leaderboard — 2026-06-05
Window: 2026-05-06 to 2026-06-04

## CP=20:00 (best null: empirical_conditional)
- L0 persistence: MAE=2.36  RMSE=2.95  bias=-2.36  BM=0.11    n=28
- L1 dminus1: MAE=1.57  RMSE=2.10  bias=-0.14  BM=0.18    n=28
- L2 climatology_doy: MAE=1.64  RMSE=2.22  bias=-0.29  BM=0.29    n=28
- L4 empirical_conditional: MAE=1.43  RMSE=2.00  bias=-1.00  BM=0.32  fallback=25%  n=28

## CP=21:00 (best null: empirical_conditional)
- L0 persistence: MAE=2.25  RMSE=2.76  bias=-2.25  BM=0.11    n=28
- L1 dminus1: MAE=1.57  RMSE=2.10  bias=-0.14  BM=0.18    n=28
- L2 climatology_doy: MAE=1.64  RMSE=2.22  bias=-0.29  BM=0.29    n=28
- L4 empirical_conditional: MAE=1.46  RMSE=2.10  bias=-1.04  BM=0.36  fallback=21%  n=28

## CP=22:00 (best null: empirical_conditional)
- L0 persistence: MAE=1.82  RMSE=2.31  bias=-1.82  BM=0.14    n=28
- L1 dminus1: MAE=1.57  RMSE=2.10  bias=-0.14  BM=0.18    n=28
- L2 climatology_doy: MAE=1.64  RMSE=2.22  bias=-0.29  BM=0.29    n=28
- L4 empirical_conditional: MAE=1.25  RMSE=1.94  bias=-0.32  BM=0.36  fallback=21%  n=28

## CP=23:00 (best null: empirical_conditional)
- L0 persistence: MAE=1.32  RMSE=1.78  bias=-1.32  BM=0.25    n=28
- L1 dminus1: MAE=1.57  RMSE=2.10  bias=-0.14  BM=0.18    n=28
- L2 climatology_doy: MAE=1.64  RMSE=2.22  bias=-0.29  BM=0.29    n=28
- L4 empirical_conditional: MAE=1.18  RMSE=1.80  bias=-0.61  BM=0.36  fallback=14%  n=28

## Segments
### disrupted
- persistence (): MAE=1.67  n=3
- dminus1 (): MAE=1.33  n=3
- climatology_doy (): MAE=2.00  n=3
- empirical_conditional (): MAE=0.33  n=3
### foehn_nw
- persistence (): MAE=1.67  n=6
- persistence (): MAE=1.80  n=5
- persistence (): MAE=1.40  n=5
- persistence (): MAE=0.83  n=6
- dminus1 (): MAE=1.50  n=6
- dminus1 (): MAE=1.60  n=5
- dminus1 (): MAE=1.60  n=5
- dminus1 (): MAE=1.67  n=6
- climatology_doy (): MAE=3.00  n=6
- climatology_doy (): MAE=3.40  n=5
- climatology_doy (): MAE=3.40  n=5
- climatology_doy (): MAE=3.00  n=6
- empirical_conditional (): MAE=2.33  n=6
- empirical_conditional (): MAE=2.60  n=5
- empirical_conditional (): MAE=3.00  n=5
- empirical_conditional (): MAE=2.00  n=6
### transition
- persistence (): MAE=2.68  n=19
- persistence (): MAE=2.35  n=23
- persistence (): MAE=1.91  n=23
- persistence (): MAE=1.45  n=22
- dminus1 (): MAE=1.63  n=19
- dminus1 (): MAE=1.57  n=23
- dminus1 (): MAE=1.57  n=23
- dminus1 (): MAE=1.55  n=22
- climatology_doy (): MAE=1.16  n=19
- climatology_doy (): MAE=1.26  n=23
- climatology_doy (): MAE=1.26  n=23
- climatology_doy (): MAE=1.27  n=22
- empirical_conditional (): MAE=1.32  n=19
- empirical_conditional (): MAE=1.22  n=23
- empirical_conditional (): MAE=0.87  n=23
- empirical_conditional (): MAE=0.95  n=22

## Gates
### CP=20:00
- **L0_persistence**: 2/5 passed
  - X G1: KILL — model_mae=2.3571 vs best_null_mae=1.4286
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=20:00: loses to null → stay_out
- **L1_dminus1**: 2/5 passed
  - X G1: KILL — model_mae=1.5714 vs best_null_mae=1.4286
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=20:00: loses to null → stay_out
- **L2_climatology_doy**: 2/5 passed
  - X G1: KILL — model_mae=1.6429 vs best_null_mae=1.4286
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=20:00: loses to null → stay_out
- **L4_empirical_conditional**: 3/5 passed
  - X G1: KILL — model_mae=1.4286 vs best_null_mae=1.4286
  - + G2: OK — fallback_rate=0.2500
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - + G5: OK — CP=20:00: beats null
### CP=21:00
- **L0_persistence**: 2/5 passed
  - X G1: KILL — model_mae=2.2500 vs best_null_mae=1.4643
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=21:00: loses to null → stay_out
- **L1_dminus1**: 2/5 passed
  - X G1: KILL — model_mae=1.5714 vs best_null_mae=1.4643
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=21:00: loses to null → stay_out
- **L2_climatology_doy**: 2/5 passed
  - X G1: KILL — model_mae=1.6429 vs best_null_mae=1.4643
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=21:00: loses to null → stay_out
- **L4_empirical_conditional**: 3/5 passed
  - X G1: KILL — model_mae=1.4643 vs best_null_mae=1.4643
  - + G2: OK — fallback_rate=0.2143
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - + G5: OK — CP=21:00: beats null
### CP=22:00
- **L0_persistence**: 2/5 passed
  - X G1: KILL — model_mae=1.8214 vs best_null_mae=1.2500
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=22:00: loses to null → stay_out
- **L1_dminus1**: 2/5 passed
  - X G1: KILL — model_mae=1.5714 vs best_null_mae=1.2500
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=22:00: loses to null → stay_out
- **L2_climatology_doy**: 2/5 passed
  - X G1: KILL — model_mae=1.6429 vs best_null_mae=1.2500
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=22:00: loses to null → stay_out
- **L4_empirical_conditional**: 3/5 passed
  - X G1: KILL — model_mae=1.2500 vs best_null_mae=1.2500
  - + G2: OK — fallback_rate=0.2143
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - + G5: OK — CP=22:00: beats null
### CP=23:00
- **L0_persistence**: 2/5 passed
  - X G1: KILL — model_mae=1.3214 vs best_null_mae=1.1786
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=23:00: loses to null → stay_out
- **L1_dminus1**: 2/5 passed
  - X G1: KILL — model_mae=1.5714 vs best_null_mae=1.1786
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=23:00: loses to null → stay_out
- **L2_climatology_doy**: 2/5 passed
  - X G1: KILL — model_mae=1.6429 vs best_null_mae=1.1786
  - + G2: OK — fallback_rate=0.0000
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - X G5: STAY_OUT — CP=23:00: loses to null → stay_out
- **L4_empirical_conditional**: 3/5 passed
  - X G1: KILL — model_mae=1.1786 vs best_null_mae=1.1786
  - + G2: OK — fallback_rate=0.1429
  - + G3: OK — p50_mode_share=0.0000
  - X G4: NOWCAST_SUSPECT — morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate
  - + G5: OK — CP=23:00: beats null

## Baseline+Feature Nulls
- feature slope_3h (CP=22:00): MAE=0.96  n=28  corr_diff=0.0166
- feature slope_3h (CP=23:00): MAE=0.79  n=28  corr_diff=0.0001
- feature regime_label (CP=21:00): MAE=1.43  n=28  corr_diff=-0.0323
- feature regime_label (CP=22:00): MAE=1.04  n=28  corr_diff=0.0000
- feature regime_label (CP=23:00): MAE=0.82  n=28  corr_diff=0.0000
- feature dewpoint_depression (CP=21:00): MAE=1.29  n=28  corr_diff=-0.0035
- feature dewpoint_depression (CP=23:00): MAE=0.82  n=28  corr_diff=0.0000
- feature tmin_delta_tmax (CP=20:00): MAE=1.11  n=28  corr_diff=0.0048
- feature tmin_delta_tmax (CP=21:00): MAE=1.14  n=28  corr_diff=-0.0116
- feature tmin_delta_tmax (CP=22:00): MAE=1.07  n=28  corr_diff=-0.0307
- feature tmin_delta_tmax (CP=23:00): MAE=0.75  n=28  corr_diff=0.0231
- feature precip_disruption (CP=20:00): MAE=1.71  n=28  corr_diff=0.0073
- feature precip_disruption (CP=21:00): MAE=1.29  n=28  corr_diff=0.0227
- feature precip_disruption (CP=22:00): MAE=0.93  n=28  corr_diff=0.0200
- feature precip_disruption (CP=23:00): MAE=1.00  n=28  corr_diff=0.0120
- feature cloud_cover_suppression (CP=20:00): MAE=0.96  n=25  corr_diff=-0.0119
- feature cloud_cover_suppression (CP=21:00): MAE=1.12  n=26  corr_diff=0.0123
- feature cloud_cover_suppression (CP=23:00): MAE=0.73  n=26  corr_diff=0.0000
- feature foehn_score (CP=21:00): MAE=1.25  n=28  corr_diff=-0.0525
- feature foehn_score (CP=23:00): MAE=0.82  n=28  corr_diff=0.0000
- feature regime_score_argmax (CP=21:00): MAE=1.43  n=28  corr_diff=-0.0323
- feature regime_score_argmax (CP=22:00): MAE=1.04  n=28  corr_diff=0.0000
- feature regime_score_argmax (CP=23:00): MAE=0.82  n=28  corr_diff=0.0000
- feature warming_rate_06_09 (CP=22:00): MAE=0.96  n=28  corr_diff=0.0166
- feature warming_rate_06_09 (CP=23:00): MAE=0.79  n=28  corr_diff=0.0001
- feature dewpoint_collapse_rate_3h (CP=22:00): MAE=0.89  n=28  corr_diff=0.0318
- feature dewpoint_collapse_rate_3h (CP=23:00): MAE=0.79  n=28  corr_diff=-0.0016
- feature nw_sector_not_foehn (CP=20:00): MAE=1.50  n=28  corr_diff=0.0000
- feature cloud_base_transparency (CP=21:00): MAE=1.08  n=26  corr_diff=0.0000
- feature cloud_base_transparency (CP=23:00): MAE=0.73  n=26  corr_diff=0.0000


Best null varies by CP. 16 aggregated baseline results across 4 CPs.