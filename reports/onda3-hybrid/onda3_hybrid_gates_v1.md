# onda3_hybrid_gates_v1

| gate_id | gate_name | gate_status | gate_detail | production_status | model_name |
| --- | --- | --- | --- | --- | --- |
| H1 | Per-CP honest lift | PASS | model MAE is below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_local_only |
| H2 | Anticipation stratum | BLOCK | model does not beat honest null on every supported CP | EXPERIMENT_ONLY | hybrid_local_only |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_local_only |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_local_only |
| H1 | Per-CP honest lift | BLOCK | model MAE is not below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H2 | Anticipation stratum | BLOCK | model does not beat honest null on every supported CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_local_only_covered_rows |
| H1 | Per-CP honest lift | PASS | model MAE is below honest-null MAE at every CP | EXPERIMENT_ONLY | hybrid_om_augmented |
| H2 | Anticipation stratum | PASS | model beats honest null on supported forecast_2_plus CP rows | EXPERIMENT_ONLY | hybrid_om_augmented |
| H3 | Physical floor | PASS | raw violations reported=0; clamped violations=0 | EXPERIMENT_ONLY | hybrid_om_augmented |
| H4 | Lead degradation table | PASS | lead degradation table exists for every CP | EXPERIMENT_ONLY | hybrid_om_augmented |
