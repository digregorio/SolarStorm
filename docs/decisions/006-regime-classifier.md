# ADR-006: Regime Classifier

- **Date:** 2026-06-04
- **Status:** Superseded by ADR-011

## Supersession Note

The 2026-06-06 Onda 4 run showed that this ADR mixed causal physical regimes
with an ex-post outcome label. In particular, `late_warming = tmax_hour >= 18`
cannot be a causal pre-CP regime because `tmax_hour` is only known after the day
unfolds.

ADR-011 supersedes the promoted semantics. ADR-012 further quarantines this
heuristic classifier as a diagnostic baseline until Onda 2E decision records
explicitly retain, adapt, or replace each rule. This document remains
historical context for the original heuristic classifier.

## Context

Wellington Airport (NZWN) exhibits distinct meteorological regimes driven by its position between Cook Strait and the Remutaka Range. A single forecast model cannot perform equally well across calm maritime days, foehn-driven warming spikes, frontal disruptions, and evening late-warming events.

The old Wellington project attempted to segment forecasts by regime but used overfitted cluster thresholds (per-cluster offset tables) that failed out-of-sample. The lesson: regime definitions must be physically grounded and data-driven (P2), and regime-specific hypotheses must pass the same gates as any other feature (P3).

## Decision

**A 5-regime heuristic classifier with data-driven thresholds and a composite foehn score.**

Implemented in `solarstorm/eda/_regimes.py`:

| Regime        | Criteria                                                                 | Physical Interpretation                                    |
|---------------|--------------------------------------------------------------------------|------------------------------------------------------------|
| `calm`        | Default (no other regime triggers)                                       | Maritime equilibrium, low intraday variance                |
| `transition`  | `max_delta_t_per_h > 1.0` (warming rate > 1 C/h)                        | Active warming, typically post-clearance or pre-frontal   |
| `late_warming`| `tmax_hour >= 18` (Tmax occurs in evening)                               | Evening peak -- Tmax lands after checkpoint                |
| `foehn_nw`    | `foehn_score > 60.0` (NW flow strength x dewpoint depression)           | Strong NW downslope flow producing dry adiabatic warming   |
| `disrupted`   | Precipitation present OR `max_delta < -2.0` (strong cooling)            | Frontal passage, rain, post-frontal clearing               |

### Foehn Score Design

The `foehn_score` is a composite: `nw_flow_strength * dewpoint_depression`, where:
- `nw_flow_strength` = mean wind speed of observations in the NW quadrant (270-45 degrees). A 4 kt and a 22 kt northerly are meteorologically different events; direction fraction alone conflates them.
- `dewpoint_depression` = mean (T - Td) across the day.
- Threshold of 60.0 corresponds to approximately >= 15 kt NW flow AND >= 4 C dewpoint depression -- the physical floor for foehn warming.

The thresholds are calibrated on NZWN EDA, documented with physical justification, and registered as gated hypotheses (H14-H16) rather than baked in. This means the classifier itself can be refined if the data supports it.

## Alternatives Considered

1. **Direction-only foehn flag:** Flag foehn on NW wind direction alone. Rejected -- 4 kt and 22 kt northerlies produce completely different warming behavior; intensity matters.
2. **Fixed C/h rate for late_warming:** Use a warming rate threshold (> 2 C/h) instead of Tmax hour. Rejected as too brittle at the 3-hourly METAR cadence; the Tmax hour is a more stable signal.
3. **Unsupervised clustering:** K-means on meteorological variables. Rejected -- the regimes have known physical interpretations; unsupervised clustering may find noise patterns that don't generalize.

## Consequences

### Enabled
- Regime-conditional hypothesis testing: each validated hypothesis can report per-regime effect sizes.
- The classifier is itself a set of gated hypotheses (H14-H16) -- it can be refined with evidence.
- Composited `foehn_score` captures the interaction of flow strength and dryness, which direction-only flags miss.

### Prevents
- Baking regime logic into forecast models (it remains a diagnostic input, not a hard switch).
- Overfitted cluster assignments from unsupervised methods.
- The old project's pattern of per-cluster constant tables.

## References

- `solarstorm/eda/_regimes.py` -- `classify_regime()`
- `solarstorm/features/builder.py` -- Regime integration in `build_features()`
- `solarstorm/eda/_catalog.py` -- H14-H16 (regime classifier refinement hypotheses)
