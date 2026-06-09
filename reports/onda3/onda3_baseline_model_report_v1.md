# Onda 3 Baseline Model Report

Generated: 2026-06-09

## Decision

| decision_status | decision_rationale | production_status |
| --- | --- | --- |
| READY_FOR_ONDA4_MODEL_RERUN | Baseline-first Onda 3 experiment completed against train-only null. | EXPERIMENT_ONLY |

## Baseline Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| train_mean_null | ALL | 19748 | 2076 | 2.811951591985803 | False | EXPERIMENT_ONLY |

## Challenger Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| ridge_challenger | ALL | 19748 | 2076 | 1.348721920474219 | True | EXPERIMENT_ONLY |

## Slice Diagnostics

| slice_column | slice_value | rows | target_mean | production_status |
| --- | --- | --- | --- | --- |
| cp | 20:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 21:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 22:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| cp | 23:00 | 5456 | 16.924486803519063 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_non_southerly | 16298 | 17.57559209718984 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_southerly_flow | 5526 | 15.004162142598625 | EXPERIMENT_ONLY |

## Uncertainty and Abstention

| model_name | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status |
| --- | --- | --- | --- | --- |
| ridge_challenger | 1.0314621789651444 | 2.981763035114538 | abstain when slice support or interval calibration fails | EXPERIMENT_ONLY |
