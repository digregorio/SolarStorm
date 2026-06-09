# Hypothesis Validation Results — 2026-06-05

| id | feature | cp | regime | effect_size | ci_lo | ci_hi | p_value | fdr | passes | gates | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | slope_3h | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H1 | slope_3h | 21:00 | all | 0.1111 | 0.0878 | 0.1350 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H1 | slope_3h | 22:00 | all | 0.0553 | 0.0398 | 0.0692 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H1 | slope_3h | 23:00 | all | 0.0420 | 0.0348 | 0.0491 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H2 | hours_to_expected_peak | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H2 | hours_to_expected_peak | 21:00 | all |  |  |  |  | N | N |  | rejected |
| H2 | hours_to_expected_peak | 22:00 | all |  |  |  |  | N | N |  | rejected |
| H2 | hours_to_expected_peak | 23:00 | all |  |  |  |  | N | N |  | rejected |
| H3 | regime_label | 20:00 | all | 0.0143 | -0.0023 | 0.0303 | 0.040300 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H3 | regime_label | 21:00 | all | 0.0485 | 0.0363 | 0.0617 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H3 | regime_label | 22:00 | all | 0.0196 | 0.0111 | 0.0286 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H3 | regime_label | 23:00 | all | 0.0139 | 0.0088 | 0.0191 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H4 | dewpoint_depression | 20:00 | all | -0.0060 | -0.0133 | 0.0011 | 0.944400 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H4 | dewpoint_depression | 21:00 | all | 0.0139 | 0.0079 | 0.0201 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H4 | dewpoint_depression | 22:00 | all | -0.0003 | -0.0045 | 0.0042 | 0.557900 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H4 | dewpoint_depression | 23:00 | all | 0.0035 | 0.0007 | 0.0063 | 0.006400 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H5 | tmax_dminus1 | 20:00 | all | -0.0047 | -0.0112 | 0.0010 | 0.938400 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H5 | tmax_dminus1 | 21:00 | all | 0.0018 | -0.0000 | 0.0035 | 0.018800 | Y | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H5 | tmax_dminus1 | 22:00 | all | -0.0003 | -0.0007 | -0.0000 | 0.978500 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H5 | tmax_dminus1 | 23:00 | all | -0.0002 | -0.0003 | 0.0000 | 0.944700 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H6 | tmin_delta_tmax | 20:00 | all | 0.0968 | 0.0723 | 0.1226 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H6 | tmin_delta_tmax | 21:00 | all | 0.1082 | 0.0902 | 0.1253 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H6 | tmin_delta_tmax | 22:00 | all | 0.0246 | 0.0123 | 0.0368 | 0.000300 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H6 | tmin_delta_tmax | 23:00 | all | 0.0433 | 0.0359 | 0.0509 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H7 | intraday_regime_change | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H7 | intraday_regime_change | 21:00 | all |  |  |  |  | N | N |  | rejected |
| H7 | intraday_regime_change | 22:00 | all |  |  |  |  | N | N |  | rejected |
| H7 | intraday_regime_change | 23:00 | all |  |  |  |  | N | N |  | rejected |
| H8 | wind_dir_change_s_to_n | 20:00 | all | 0.0000 | -0.0000 | 0.0000 | 0.629800 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H8 | wind_dir_change_s_to_n | 21:00 | all | -0.0000 | -0.0000 | 0.0000 | 0.996700 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H8 | wind_dir_change_s_to_n | 22:00 | all | 0.0000 | -0.0000 | 0.0000 | 0.694100 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H8 | wind_dir_change_s_to_n | 23:00 | all | 0.0000 | 0.0000 | 0.0000 | 0.018800 | Y | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H9 | day_sequence_pattern | 20:00 | all | -0.0156 | -0.0209 | -0.0102 | 1.000000 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H9 | day_sequence_pattern | 21:00 | all | -0.0006 | -0.0051 | 0.0039 | 0.611800 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H9 | day_sequence_pattern | 22:00 | all | -0.0056 | -0.0081 | -0.0029 | 1.000000 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H9 | day_sequence_pattern | 23:00 | all | -0.0008 | -0.0029 | 0.0013 | 0.776800 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H10 | precip_disruption | 20:00 | all | 0.1437 | 0.1143 | 0.1729 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H10 | precip_disruption | 21:00 | all | 0.1557 | 0.1328 | 0.1769 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H10 | precip_disruption | 22:00 | all | 0.0440 | 0.0303 | 0.0581 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H10 | precip_disruption | 23:00 | all | 0.0433 | 0.0350 | 0.0517 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H11 | tmax_hour_by_regime_month | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H11 | tmax_hour_by_regime_month | 21:00 | all |  |  |  |  | N | N |  | rejected |
| H11 | tmax_hour_by_regime_month | 22:00 | all |  |  |  |  | N | N |  | rejected |
| H11 | tmax_hour_by_regime_month | 23:00 | all |  |  |  |  | N | N |  | rejected |
| H12 | cloud_cover_suppression | 20:00 | all | 0.0546 | 0.0356 | 0.0745 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H12 | cloud_cover_suppression | 21:00 | all | 0.0864 | 0.0727 | 0.1010 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H12 | cloud_cover_suppression | 22:00 | all | 0.0042 | -0.0027 | 0.0125 | 0.140600 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H12 | cloud_cover_suppression | 23:00 | all | 0.0235 | 0.0204 | 0.0267 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H13 | pressure_trend_3h | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H13 | pressure_trend_3h | 21:00 | all | -0.0239 | -0.0972 | 0.0067 | 0.770100 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H13 | pressure_trend_3h | 22:00 | all | -0.0288 | -0.0743 | 0.0017 | 0.952500 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H13 | pressure_trend_3h | 23:00 | all | -0.0176 | -0.0469 | 0.0022 | 0.945200 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H14 | foehn_score | 20:00 | all | -0.0156 | -0.0215 | -0.0092 | 1.000000 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H14 | foehn_score | 21:00 | all | 0.0088 | 0.0026 | 0.0158 | 0.003500 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H14 | foehn_score | 22:00 | all | -0.0055 | -0.0107 | 0.0002 | 0.975700 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H14 | foehn_score | 23:00 | all | 0.0069 | 0.0025 | 0.0115 | 0.001700 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H15 | late_warming_anomaly | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H15 | late_warming_anomaly | 21:00 | all |  |  |  |  | N | N |  | rejected |
| H15 | late_warming_anomaly | 22:00 | all |  |  |  |  | N | N |  | rejected |
| H15 | late_warming_anomaly | 23:00 | all |  |  |  |  | N | N |  | rejected |
| H16 | regime_score_argmax | 20:00 | all | 0.0143 | -0.0023 | 0.0303 | 0.040300 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H16 | regime_score_argmax | 21:00 | all | 0.0485 | 0.0363 | 0.0617 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H16 | regime_score_argmax | 22:00 | all | 0.0196 | 0.0111 | 0.0286 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H16 | regime_score_argmax | 23:00 | all | 0.0139 | 0.0088 | 0.0191 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H17 | warming_rate_06_09 | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H17 | warming_rate_06_09 | 21:00 | all | 0.1111 | 0.0878 | 0.1350 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H17 | warming_rate_06_09 | 22:00 | all | 0.0553 | 0.0398 | 0.0692 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H17 | warming_rate_06_09 | 23:00 | all | 0.0420 | 0.0348 | 0.0491 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H18 | nocturnal_plateau_flag | 20:00 | all | 0.0000 | -0.0000 | 0.0000 | 0.629800 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H18 | nocturnal_plateau_flag | 21:00 | all | -0.0000 | -0.0000 | 0.0000 | 0.996700 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H18 | nocturnal_plateau_flag | 22:00 | all | 0.0000 | -0.0000 | 0.0000 | 0.694100 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H18 | nocturnal_plateau_flag | 23:00 | all | 0.0000 | 0.0000 | 0.0000 | 0.018800 | Y | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H19 | sst_maritime_cap | 20:00 | all |  |  |  |  | N | N |  | BLOCKED |
| H19 | sst_maritime_cap | 21:00 | all |  |  |  |  | N | N |  | BLOCKED |
| H19 | sst_maritime_cap | 22:00 | all |  |  |  |  | N | N |  | BLOCKED |
| H19 | sst_maritime_cap | 23:00 | all |  |  |  |  | N | N |  | BLOCKED |
| H20 | dewpoint_collapse_rate_3h | 20:00 | all |  |  |  |  | N | N |  | rejected |
| H20 | dewpoint_collapse_rate_3h | 21:00 | all | 0.0549 | 0.0355 | 0.0737 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H20 | dewpoint_collapse_rate_3h | 22:00 | all | 0.0181 | 0.0058 | 0.0308 | 0.002600 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H20 | dewpoint_collapse_rate_3h | 23:00 | all | 0.0280 | 0.0206 | 0.0359 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H21 | prefrontal_warming_window | 20:00 | all | 0.0000 | -0.0000 | 0.0000 | 0.629800 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H21 | prefrontal_warming_window | 21:00 | all | -0.0004 | -0.0011 | 0.0004 | 0.835300 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H21 | prefrontal_warming_window | 22:00 | all | 0.0002 | -0.0023 | 0.0027 | 0.438700 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H21 | prefrontal_warming_window | 23:00 | all | -0.0001 | -0.0016 | 0.0015 | 0.525400 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H22 | nw_sector_not_foehn | 20:00 | all | 0.0012 | 0.0001 | 0.0027 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H22 | nw_sector_not_foehn | 21:00 | all | 0.0001 | -0.0008 | 0.0011 | 0.452500 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H22 | nw_sector_not_foehn | 22:00 | all | 0.0003 | -0.0003 | 0.0010 | 0.127700 | N | N | G1:OK G2:OK G3:OK G4:NOWCAST_SUSPECT G5:OK | rejected |
| H22 | nw_sector_not_foehn | 23:00 | all | -0.0000 | -0.0004 | 0.0003 | 0.602100 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H23 | cloud_base_transparency | 20:00 | all | -0.0000 | -0.0092 | 0.0095 | 0.498400 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H23 | cloud_base_transparency | 21:00 | all | 0.0326 | 0.0252 | 0.0389 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |
| H23 | cloud_base_transparency | 22:00 | all | -0.0097 | -0.0136 | -0.0055 | 1.000000 | N | N | G1:KILL G2:OK G3:OK G4:NOWCAST_SUSPECT G5:STAY_OUT | rejected |
| H23 | cloud_base_transparency | 23:00 | all | 0.0168 | 0.0148 | 0.0190 | 0.000100 | Y | Y | G1:OK G2:OK G3:OK G4:OK G5:OK | validated |