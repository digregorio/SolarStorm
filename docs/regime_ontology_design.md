# Regime Ontology Design

Status: implemented for Onda 2R
Date: 2026-06-06

This document defines the new regime ontology after the Onda 4 NO-GO.

## Core Separation

SolarStorm now separates weather-state regimes from Tmax timing outcomes.

| Layer | Meaning | Can be feature? | Example |
|-------|---------|-----------------|---------|
| Causal physical regime | Weather state inferable before CP | Yes | `strong_nw_foehn` |
| Evaluation segment | Post-facto audit slice | No | final `tmax_hour_bucket` |
| Timing risk target | Event/probability to predict | As target or train-only prior only | `late_tmax_event` |

Intraday state changes sit in the feature/risk layer, not in the regime
ontology. A day may show clearing, rotation, cooling, renewed NW flow, or other
changes in characteristics after the first CP, but those are not new regimes.
They are evidence that may later inform a risk model between already-defined
physical regimes.

## Deprecated Concept

The old rule is deprecated:

```text
late_warming = tmax_hour >= 18
```

It fails for two reasons:

1. `tmax_hour` is not available at morning CPs.
2. `18:00` is not a physical constant for Wellington. Normal Tmax timing varies
   by month and physical regime.

`late_warming` must not be restored as a hard ex-ante regime.

## Implemented Physical Regimes

Onda 2R froze the causal regime model card. The implemented family is:

| Regime | Physical meaning | Expected evidence |
|--------|------------------|-------------------|
| `southerly_disrupted` | Southerly change, frontal cooling, rain, rising pressure | S/SE vector wind, precip/cooling, pressure rise |
| `standard_nw` | Normal N/NW flow, warmer maritime pattern | N/NW vector wind, moderate speed, stable pressure |
| `strong_nw_foehn` | Strong dry NW flow, foehn-like | strong NW vector wind, high dewpoint depression |
| `calm_radiative` | Weak wind / radiation-led morning | low wind, weak advection, radiative warming |

The current model card is `docs/regime_model_card.md`. These labels are
implemented, but the post-Onda 2R robustness rerun still blocks Onda 3 because
`calm_radiative` and `standard_nw` have no passing feature in R2.

The 2026-06-06 trigger audit and cooling-rule experiment show that the current
`southerly_disrupted` label is dominated by the `min_delta_t_per_h < -2.0`
cooling rule. If cooling is not allowed as a standalone disruption trigger,
13,367 rows would move from `southerly_disrupted` into `standard_nw`,
`strong_nw_foehn`, or `calm_radiative`. This is diagnostic evidence only; it
does not change the production classifier.

## Late Tmax Target

Late Tmax should be defined relative to train-only timing norms:

```text
late_tmax_event =
  tmax_hour > q90_train(tmax_hour | month, physical_regime)
```

Acceptable alternatives:

```text
late_tmax_event =
  tmax_hour > median_train(tmax_hour | month, physical_regime) + delta_hours
```

or a continuous target:

```text
late_tmax_anomaly =
  tmax_hour - median_train(tmax_hour | month, physical_regime)
```

Onda 4 R9 audits a separate month/regime q90 late-Tmax baseline. Any predictive
feature using this timing information must compute the threshold inside the
walk-forward training window.

## Feature Rules

Allowed:

- causal physical regime at CP;
- train-only historical timing priors;
- calibrated probability of `late_tmax_event`;
- late-spike candidate artifacts for research.

Not allowed:

- full-day `tmax_hour` in a CP feature;
- full-day `late_warming` override of `regime_label`;
- global fixed `18:00` thresholds in validation;
- creating a transition regime before the base physical regimes are validated;
- using ex-post evaluation labels as model inputs.

## Onda 4 Impact

R2 is now:

```text
No dead causal physical regime.
```

R7 should become:

```text
Skill is not a fixed-CP artifact under month/regime Tmax timing norms.
```

R8 remains:

```text
Late-spike evidence pack is produced.
```

Add R9:

```text
Late-Tmax risk baseline exists and is evaluated separately from deterministic
Tmax MAE.
```

## References

- `docs/decisions/011-regime-ontology-repair.md`
- `docs/onda2r_regime_ontology_repair_plan.md`
- `docs/regime_model_card.md`
- `reports/regime/2026-06-06-regime-clustering-report.md`
- `research/regime_clustering_report.md`
- `update.txt`
