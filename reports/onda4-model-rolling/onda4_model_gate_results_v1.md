# onda4_model_gate_results_v1

| gate_id | gate_name | gate_status | detail | production_status |
| --- | --- | --- | --- | --- |
| M1 | Input artifact integrity | PASS | missing_or_empty=0 | EXPERIMENT_ONLY |
| M2 | Causal manifest safety | PASS | included_blocked_target_or_proxy=0 | EXPERIMENT_ONLY |
| M3 | Challenger lift | PASS | null_mae=2.9522; challenger_mae=1.2026; lift=1.7496; challenger_failures=0 | EXPERIMENT_ONLY |
| M4 | Temporal robustness | PASS | rolling_temporal_diagnostics; test_years=2023,2024,2025 | EXPERIMENT_ONLY |
| M5 | Slice robustness | PASS | low_support_slices=0 | EXPERIMENT_ONLY |
| M6 | Uncertainty and abstention | PASS | p50=1.1292; p90=2.8582; has_rule=True | EXPERIMENT_ONLY |
| M7 | Anti-nowcast/model timing | PASS | target_proxy_columns_blocked_by_manifest | EXPERIMENT_ONLY |
| M8 | Decision hygiene | PASS | onda3_decision=READY_FOR_ONDA4_MODEL_RERUN | EXPERIMENT_ONLY |
