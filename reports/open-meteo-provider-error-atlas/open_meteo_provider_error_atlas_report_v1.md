# Open-Meteo Provider Error Atlas

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

This report measures raw causal provider prediction error. It does not train, blend, calibrate, or approve production use.

## Metrics

| endpoint | model | provider_family | slice_type | slice_name | n_rows | mae | rmse | signed_bias | exact_bracket_pct | warm_bias_pct | cold_bias_pct | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label | macro_non_southerly | 3162 | 1.558886780518659 | 1.79237615212732 | -1.3980392156862746 | 10.942441492726122 | 9.013282732447818 | 89.75332068311197 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label | macro_southerly_flow | 1142 | 1.0381786339754817 | 1.26324852963925 | -0.6583187390542907 | 27.145359019264447 | 21.62872154115587 | 76.5323992994746 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_non_southerly|20:00 | 788 | 1.5577411167512691 | 1.7905313563495797 | -1.389720812182741 | 10.786802030456853 | 9.263959390862944 | 89.59390862944161 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_non_southerly|21:00 | 790 | 1.5611392405063291 | 1.7967516399592356 | -1.4003797468354426 | 11.012658227848101 | 9.113924050632912 | 89.62025316455696 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_non_southerly|22:00 | 790 | 1.55873417721519 | 1.7914494520472817 | -1.399493670886076 | 11.012658227848101 | 8.987341772151899 | 89.74683544303798 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_non_southerly|23:00 | 794 | 1.557934508816121 | 1.7907683784874102 | -1.4025188916876574 | 10.957178841309824 | 8.690176322418136 | 90.05037783375315 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_southerly_flow|20:00 | 288 | 1.0458333333333332 | 1.2758983763085 | -0.6875000000000001 | 27.430555555555557 | 20.833333333333336 | 77.08333333333334 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_southerly_flow|21:00 | 286 | 1.0328671328671328 | 1.2470945253848063 | -0.6531468531468532 | 26.923076923076923 | 21.328671328671327 | 76.92307692307693 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_southerly_flow|22:00 | 286 | 1.0395104895104894 | 1.2679894332356254 | -0.6555944055944056 | 26.923076923076923 | 21.678321678321677 | 76.57342657342657 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | binary_macro_regime_label_cp | macro_southerly_flow|23:00 | 282 | 1.0343971631205673 | 1.2617251501852251 | -0.6365248226950355 | 27.30496453900709 | 22.69503546099291 | 75.53191489361703 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | cp | 20:00 | 1076 | 1.420724907063197 | 1.6684169867379341 | -1.2017657992565054 | 15.241635687732341 | 12.360594795539033 | 86.2453531598513 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | cp | 21:00 | 1076 | 1.420724907063197 | 1.6684169867379341 | -1.2017657992565054 | 15.241635687732341 | 12.360594795539033 | 86.2453531598513 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | cp | 22:00 | 1076 | 1.420724907063197 | 1.6684169867379341 | -1.2017657992565054 | 15.241635687732341 | 12.360594795539033 | 86.2453531598513 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | cp | 23:00 | 1076 | 1.420724907063197 | 1.6684169867379341 | -1.2017657992565054 | 15.241635687732341 | 12.360594795539033 | 86.2453531598513 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-01 | 124 | 1.283870967741936 | 1.51870063307527 | -0.6387096774193566 | 19.35483870967742 | 32.25806451612903 | 61.29032258064516 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-02 | 112 | 1.421428571428572 | 1.6763054614240207 | -0.9071428571428564 | 21.428571428571427 | 21.428571428571427 | 78.57142857142857 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-03 | 124 | 1.5129032258064512 | 1.5958615834552787 | -1.3193548387096772 | 3.225806451612903 | 9.67741935483871 | 90.32258064516128 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-04 | 120 | 1.356666666666666 | 1.5380723866797255 | -1.016666666666667 | 13.333333333333334 | 16.666666666666664 | 80.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-05 | 124 | 1.4967741935483876 | 1.767447585571333 | -1.23225806451613 | 16.129032258064516 | 6.451612903225806 | 93.54838709677419 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-06 | 120 | 1.260000000000001 | 1.4879516121164693 | -1.0066666666666666 | 23.333333333333332 | 13.333333333333334 | 86.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-07 | 124 | 1.1096774193548387 | 1.3569415324842287 | -1.0903225806451613 | 29.03225806451613 | 3.225806451612903 | 87.09677419354838 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-08 | 124 | 1.1322580645161289 | 1.3448827746013245 | -0.9516129032258064 | 22.58064516129032 | 22.58064516129032 | 77.41935483870968 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-09 | 120 | 1.403333333333333 | 1.5785013990068781 | -1.2766666666666664 | 3.3333333333333335 | 10.0 | 90.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-10 | 124 | 1.1806451612903226 | 1.3798083083319719 | -1.1225806451612899 | 22.58064516129032 | 6.451612903225806 | 93.54838709677419 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-11 | 120 | 1.6866666666666663 | 2.040424792373719 | -1.4866666666666652 | 13.333333333333334 | 13.333333333333334 | 83.33333333333334 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2023-12 | 120 | 2.0966666666666662 | 2.5113741258522193 | -1.7433333333333323 | 10.0 | 10.0 | 90.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-01 | 48 | 2.575000000000001 | 3.0469930532685296 | -1.9749999999999996 | 16.666666666666664 | 25.0 | 75.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-02 | 116 | 1.8206896551724137 | 2.0621381605274296 | -1.7724137931034485 | 13.793103448275861 | 6.896551724137931 | 93.10344827586206 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-03 | 124 | 1.4806451612903222 | 1.719058256814638 | -1.3451612903225794 | 9.67741935483871 | 16.129032258064516 | 83.87096774193549 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-04 | 120 | 1.5966666666666667 | 1.819432145844778 | -1.3766666666666671 | 10.0 | 13.333333333333334 | 83.33333333333334 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-05 | 124 | 1.1612903225806457 | 1.377234255146301 | -0.9161290322580647 | 22.58064516129032 | 22.58064516129032 | 77.41935483870968 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-06 | 120 | 1.063333333333333 | 1.2172373091006814 | -0.9633333333333325 | 26.666666666666668 | 10.0 | 90.0 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-07 | 124 | 0.9612903225806456 | 1.1155788313840758 | -0.7741935483870969 | 22.58064516129032 | 16.129032258064516 | 80.64516129032258 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-08 | 124 | 1.3129032258064508 | 1.5183819911233603 | -1.2806451612903218 | 16.129032258064516 | 3.225806451612903 | 90.32258064516128 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-09 | 120 | 1.336666666666665 | 1.4741099009232659 | -1.3233333333333317 | 6.666666666666667 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-10 | 124 | 1.4645161290322588 | 1.6303571744035215 | -1.3612903225806463 | 3.225806451612903 | 6.451612903225806 | 93.54838709677419 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-11 | 120 | 1.3833333333333335 | 1.531992167081803 | -1.3100000000000003 | 6.666666666666667 | 3.3333333333333335 | 96.66666666666667 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2024-12 | 124 | 1.7225806451612893 | 1.9543169749837608 | -1.6322580645161282 | 12.903225806451612 | 9.67741935483871 | 90.32258064516128 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2025-01 | 124 | 1.0064516129032253 | 1.3602656287082917 | -0.6387096774193545 | 29.03225806451613 | 25.806451612903224 | 67.74193548387096 | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month | 2025-02 | 112 | 1.8357142857142852 | 2.1157572099436583 | -0.814285714285714 | 14.285714285714285 | 28.57142857142857 | 71.42857142857143 | EXPERIMENT_ONLY |

## Support Warnings

| endpoint | model | provider_family | slice_type | slice_name | n_rows | minimum_rows | warning | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
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
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2025-02|20:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2025-02|21:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2025-02|22:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
| previous_runs | gfs_seamless | NOAA_GFS | month_cp | 2025-02|23:00 | 28 | 30 | low_support_for_calibration | EXPERIMENT_ONLY |
