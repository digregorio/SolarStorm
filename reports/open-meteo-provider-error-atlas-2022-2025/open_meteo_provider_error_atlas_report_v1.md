# Open-Meteo Provider Error Atlas

Generated: 2026-06-11

production_status: EXPERIMENT_ONLY

This report measures raw causal provider prediction error. It does not train, blend, calibrate, or approve production use.

## Metrics

| endpoint | model | provider_family | slice_type | slice_name | n_rows | mae | rmse | signed_bias | exact_bracket_pct | warm_bias_pct | cold_bias_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label | macro_non_southerly | 933 | 2.002786709539121 | 2.3259107172294993 | -1.9661307609860665 | 9.110396570203644 | 3.751339764201501 | 95.39121114683816 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label | macro_southerly_flow | 335 | 1.0441791044776119 | 1.3722625396081978 | -0.7140298507462688 | 34.32835820895522 | 26.56716417910448 | 71.04477611940298 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_non_southerly|20:00 | 232 | 1.9974137931034481 | 2.3246245525557083 | -1.9603448275862068 | 9.482758620689655 | 3.8793103448275863 | 95.25862068965517 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_non_southerly|21:00 | 232 | 2.0094827586206896 | 2.3298105591183393 | -1.9732758620689652 | 9.051724137931034 | 3.4482758620689653 | 95.6896551724138 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_non_southerly|22:00 | 234 | 2.0034188034188034 | 2.3262713645528246 | -1.9666666666666663 | 8.974358974358974 | 3.8461538461538463 | 95.2991452991453 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_non_southerly|23:00 | 235 | 2.000851063829787 | 2.3229658225565775 | -1.964255319148936 | 8.936170212765958 | 3.829787234042553 | 95.31914893617022 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_southerly_flow|20:00 | 85 | 1.0729411764705885 | 1.3968872959716754 | -0.748235294117647 | 32.94117647058823 | 25.882352941176475 | 71.76470588235294 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_southerly_flow|21:00 | 85 | 1.0400000000000005 | 1.3731029694476242 | -0.7129411764705883 | 34.11764705882353 | 27.058823529411764 | 70.58823529411765 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_southerly_flow|22:00 | 83 | 1.0337349397590365 | 1.358862032767266 | -0.7012048192771083 | 34.93975903614458 | 26.506024096385545 | 71.08433734939759 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | binary_macro_regime_label_cp | macro_southerly_flow|23:00 | 82 | 1.0292682926829273 | 1.359070701152706 | -0.6926829268292682 | 35.36585365853659 | 26.82926829268293 | 70.73170731707317 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | cp | 20:00 | 317 | 1.7495268138801259 | 2.1161538827600666 | -1.6353312302839116 | 15.772870662460567 | 9.779179810725552 | 88.95899053627761 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | cp | 21:00 | 317 | 1.7495268138801259 | 2.1161538827600666 | -1.6353312302839116 | 15.772870662460567 | 9.779179810725552 | 88.95899053627761 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | cp | 22:00 | 317 | 1.7495268138801259 | 2.1161538827600666 | -1.6353312302839116 | 15.772870662460567 | 9.779179810725552 | 88.95899053627761 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | cp | 23:00 | 317 | 1.7495268138801259 | 2.1161538827600666 | -1.6353312302839116 | 15.772870662460567 | 9.779179810725552 | 88.95899053627761 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-02 | 44 | 2.572727272727273 | 2.9000000000000004 | -2.554545454545456 | 9.090909090909092 | 9.090909090909092 | 90.9090909090909 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-03 | 124 | 2.4387096774193564 | 2.9072767437098457 | -2.4193548387096784 | 19.35483870967742 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-04 | 120 | 1.5433333333333332 | 1.8245547402037576 | -1.51 | 16.666666666666664 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-05 | 124 | 1.2741935483870965 | 1.4704618541519974 | -1.0548387096774194 | 19.35483870967742 | 16.129032258064516 | 83.87096774193549 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-06 | 120 | 0.8399999999999999 | 0.9535897091167318 | -0.4066666666666668 | 20.0 | 30.0 | 66.66666666666666 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-07 | 124 | 0.9774193548387097 | 1.1292303973603353 | -0.6935483870967741 | 22.58064516129032 | 22.58064516129032 | 77.41935483870968 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-08 | 124 | 1.180645161290322 | 1.5439789401873119 | -1.135483870967741 | 35.483870967741936 | 12.903225806451612 | 83.87096774193549 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-09 | 120 | 1.9166666666666685 | 2.2015903342811076 | -1.9166666666666685 | 10.0 | 0.0 | 93.33333333333333 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-10 | 124 | 1.6387096774193552 | 1.8085816934646561 | -1.6322580645161295 | 12.903225806451612 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-11 | 120 | 2.9366666666666634 | 3.078365367095552 | -2.9366666666666634 | 0.0 | 0.0 | 100.0 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month | 2025-12 | 124 | 2.464516129032259 | 2.7019706070367095 | -2.3290322580645153 | 3.225806451612903 | 6.451612903225806 | 93.54838709677419 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|20:00 | 11 | 2.5727272727272728 | 2.9 | -2.5545454545454542 | 9.090909090909092 | 9.090909090909092 | 90.9090909090909 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|21:00 | 11 | 2.5727272727272728 | 2.9 | -2.5545454545454542 | 9.090909090909092 | 9.090909090909092 | 90.9090909090909 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|22:00 | 11 | 2.5727272727272728 | 2.9 | -2.5545454545454542 | 9.090909090909092 | 9.090909090909092 | 90.9090909090909 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|23:00 | 11 | 2.5727272727272728 | 2.9 | -2.5545454545454542 | 9.090909090909092 | 9.090909090909092 | 90.9090909090909 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-03|20:00 | 31 | 2.4387096774193546 | 2.9072767437098466 | -2.4193548387096775 | 19.35483870967742 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-03|21:00 | 31 | 2.4387096774193546 | 2.9072767437098466 | -2.4193548387096775 | 19.35483870967742 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-03|22:00 | 31 | 2.4387096774193546 | 2.9072767437098466 | -2.4193548387096775 | 19.35483870967742 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-03|23:00 | 31 | 2.4387096774193546 | 2.9072767437098466 | -2.4193548387096775 | 19.35483870967742 | 3.225806451612903 | 96.7741935483871 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-04|20:00 | 30 | 1.5433333333333334 | 1.8245547402037574 | -1.5100000000000002 | 16.666666666666664 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-04|21:00 | 30 | 1.5433333333333334 | 1.8245547402037574 | -1.5100000000000002 | 16.666666666666664 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-04|22:00 | 30 | 1.5433333333333334 | 1.8245547402037574 | -1.5100000000000002 | 16.666666666666664 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-04|23:00 | 30 | 1.5433333333333334 | 1.8245547402037574 | -1.5100000000000002 | 16.666666666666664 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-05|20:00 | 31 | 1.2741935483870968 | 1.470461854151997 | -1.0548387096774192 | 19.35483870967742 | 16.129032258064516 | 83.87096774193549 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-05|21:00 | 31 | 1.2741935483870968 | 1.470461854151997 | -1.0548387096774192 | 19.35483870967742 | 16.129032258064516 | 83.87096774193549 | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-05|22:00 | 31 | 1.2741935483870968 | 1.470461854151997 | -1.0548387096774192 | 19.35483870967742 | 16.129032258064516 | 83.87096774193549 | EXPERIMENT_ONLY |

## Support Warnings

| endpoint | model | provider_family | slice_type | slice_name | n_rows | minimum_rows | warning | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|20:00 | 11 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|21:00 | 11 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|22:00 | 11 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_aifs025_single | ECMWF_AIFS | month_cp | 2025-02|23:00 | 11 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2024-02|20:00 | 26 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2024-02|21:00 | 26 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2024-02|22:00 | 26 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2024-02|23:00 | 26 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2025-02|20:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2025-02|21:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2025-02|22:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | ecmwf_ifs025 | ECMWF_IFS | month_cp | 2025-02|23:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-01|20:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-01|21:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-01|22:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-01|23:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-02|20:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-02|21:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-02|22:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2024-02|23:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2025-02|20:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2025-02|21:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2025-02|22:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gem_global | ECCC_GEM | month_cp | 2025-02|23:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2022-02|20:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2022-02|21:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2022-02|22:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2022-02|23:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2023-02|20:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2023-02|21:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2023-02|22:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2023-02|23:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-01|20:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-01|21:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-01|22:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-01|23:00 | 12 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-02|20:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-02|21:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-02|22:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2024-02|23:00 | 29 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
