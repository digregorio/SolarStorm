# Onda 3B Next Model Iteration Report

Generated: 2026-06-09

## Decision

| decision_status | decision_rationale | production_status |
| --- | --- | --- |
| READY_FOR_ONDA4_MODEL_RERUN | Onda 3B CP-specific next model iteration completed. | EXPERIMENT_ONLY |

## Model Results

| model_name | cp | n_train | n_test | mae | beats_train_mean_null | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| train_mean_null | 20:00 | 4937 | 519 | 2.811951591985803 | False | EXPERIMENT_ONLY |
| ridge_challenger | 20:00 | 4937 | 519 | 1.3760822291051817 | True | EXPERIMENT_ONLY |
| train_mean_null | 21:00 | 4937 | 519 | 2.811951591985803 | False | EXPERIMENT_ONLY |
| ridge_challenger | 21:00 | 4937 | 519 | 1.3119629668574029 | True | EXPERIMENT_ONLY |
| train_mean_null | 22:00 | 4937 | 519 | 2.811951591985803 | False | EXPERIMENT_ONLY |
| ridge_challenger | 22:00 | 4937 | 519 | 1.1980791074677786 | True | EXPERIMENT_ONLY |
| train_mean_null | 23:00 | 4937 | 519 | 2.811951591985803 | False | EXPERIMENT_ONLY |
| ridge_challenger | 23:00 | 4937 | 519 | 1.1972739153096013 | True | EXPERIMENT_ONLY |

## Slice Diagnostics

| slice_column | slice_value | rows | mae | production_status |
| --- | --- | --- | --- | --- |
| cp | 20:00 | 519 | 1.3760822291051822 | EXPERIMENT_ONLY |
| cp | 21:00 | 519 | 1.3119629668574013 | EXPERIMENT_ONLY |
| cp | 22:00 | 519 | 1.19807910746778 | EXPERIMENT_ONLY |
| cp | 23:00 | 519 | 1.1972739153096004 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_non_southerly | 1458 | 1.2501869908525016 | EXPERIMENT_ONLY |
| binary_macro_regime_label | macro_southerly_flow | 618 | 1.3195971567363989 | EXPERIMENT_ONLY |

## Uncertainty and Abstention

| model_name | cp | residual_abs_p50 | residual_abs_p90 | abstention_rule | production_status |
| --- | --- | --- | --- | --- | --- |
| ridge_challenger | 20:00 | 1.080473382258912 | 3.1087621394342 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 21:00 | 1.0218326486417624 | 2.7299561452756658 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 22:00 | 0.9039723772665376 | 2.6685467500499027 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |
| ridge_challenger | 23:00 | 0.9122617536859075 | 2.6727240199248605 | abstain when CP or macro slice support is weak | EXPERIMENT_ONLY |

## Scope

All outputs are EXPERIMENT_ONLY.
