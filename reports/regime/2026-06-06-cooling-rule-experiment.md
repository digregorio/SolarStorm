# Cooling Rule Experiment - 2026-06-06

Offline diagnostic only. This does not change the production regime classifier, labels, or R2 gates.

Variants:

- `current`: current `regime_label` as stored in the feature artifact.
- `south_gated_cooling`: cooling can support disruption only with southerly evidence.
- `no_cooling_only_trigger`: cooling is ignored as a standalone disruption trigger.

Rows simulated: 65472

| Variant | Candidate regime | Rows | Share |
|---------|------------------|------|-------|
| current | southerly_disrupted | 17308 | 0.793 |
| current | standard_nw | 2466 | 0.113 |
| current | strong_nw_foehn | 1309 | 0.060 |
| current | calm_radiative | 625 | 0.029 |
| current | insufficient | 116 | 0.005 |
| no_cooling_only_trigger | standard_nw | 11036 | 0.506 |
| no_cooling_only_trigger | strong_nw_foehn | 4055 | 0.186 |
| no_cooling_only_trigger | southerly_disrupted | 3941 | 0.181 |
| no_cooling_only_trigger | calm_radiative | 2676 | 0.123 |
| no_cooling_only_trigger | insufficient | 116 | 0.005 |
| south_gated_cooling | standard_nw | 11036 | 0.506 |
| south_gated_cooling | strong_nw_foehn | 4055 | 0.186 |
| south_gated_cooling | southerly_disrupted | 3941 | 0.181 |
| south_gated_cooling | calm_radiative | 2676 | 0.123 |
| south_gated_cooling | insufficient | 116 | 0.005 |

## Reclassification Moves

| Variant | From | To | Rows |
|---------|------|----|------|
| no_cooling_only_trigger | southerly_disrupted | standard_nw | 8570 |
| no_cooling_only_trigger | southerly_disrupted | strong_nw_foehn | 2746 |
| no_cooling_only_trigger | southerly_disrupted | calm_radiative | 2051 |
| south_gated_cooling | southerly_disrupted | standard_nw | 8570 |
| south_gated_cooling | southerly_disrupted | strong_nw_foehn | 2746 |
| south_gated_cooling | southerly_disrupted | calm_radiative | 2051 |