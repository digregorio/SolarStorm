# Regime Binary Macro Classifiability and Stability Report - 2026-06-09

This report documents classifiability and stability metrics for the binary macro candidate.
Status: `EXPERIMENT_ONLY`; evaluated on theapproved physical feature basis.

## Method Comparison

| Method | Candidate Version | Macros | Dead | Low Conf Share | Silhouette | Predictive AUC-ROC | Stability (Fold) | Temporal Stability | Decision Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `distance_softmax_binary` | binary_v1 | 2 | 0 | 0.0000 | 0.0445 | 0.9886 | 0.8089 | 0.9917 | `READY_FOR_ONDA3_DESIGN_REVIEW` |
| `train_only_gmm` | binary_v1 | 2 | 0 | 0.0430 | 0.2049 | 0.0000 | 0.1340 | 0.9692 | `KEEP_IN_REGIME_DESIGN_REVIEW` |
| `som_topological` | binary_v1 | 2 | 0 | 0.0000 | 0.0460 | 0.0000 | 0.7855 | 0.9921 | `KEEP_IN_REGIME_DESIGN_REVIEW` |
| `michelangeli_stability` | binary_v1 | 2 | 0 | 0.0000 | 0.0460 | 0.0000 | 0.7855 | 0.9921 | `KEEP_IN_REGIME_DESIGN_REVIEW` |

## Target Verification Thresholds

- **Predictive Separability (AUC-ROC)**: >= 0.80
- **Stability (Fold)**: >= 0.7
- **Low Confidence Share**: <= 0.5

## Validation Status Conclusion

Binary macro candidate validated (apto para design review com ressalva). R2 passed for both macros, but macro_non_southerly has weak sensitivity (passes 3/92 hypothesis rows vs 47/92 for macro_southerly_flow). Stability score: 0.8089 (>= 0.7). Predictive classifiability (AUC-ROC): 0.9886 (>= 0.80).
