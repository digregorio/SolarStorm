# ADR-011: Regime Ontology Repair

- **Date:** 2026-06-06
- **Status:** Accepted
- **Supersedes:** ADR-006 for promoted regime semantics

## Context

The first Onda 4 robustness run returned NO-GO because R2 found
`late_warming` as a dead regime. Follow-up analysis showed this was not a normal
model weakness. It was an ontology error.

The current `regime_label` is computed from a causal pre-CP observation slice.
For NZWN, CP20-CP23 are local morning cutoffs. A label defined as
`tmax_hour >= 18` cannot be observed in a morning-only slice. Therefore
`late_warming` is structurally impossible as a causal regime.

The newer EDA in `research/regime_clustering_report.md` also indicates that
local weather states are better represented as physical morning regimes, while
late Tmax timing is a cross-cutting outcome/risk.

## Decision

`late_warming` is no longer a promoted ex-ante regime. It is an ex-post timing
event and a future risk target.

The project now separates three concepts:

1. **Causal physical regime**
   A weather-state label inferred only from observations available at the CP.
   This may be used as a feature, segment, or conditioning variable.
2. **Evaluation segment**
   A post-facto slice used to audit performance. This can include outcome
   labels, but must never be used as a model feature.
3. **Late Tmax / late spike risk**
   A probabilistic event target describing whether Tmax occurs later than the
   normal timing window for the relevant month and physical regime.

Intraday changes in the observed day state are not a fourth concept of
regime. They are possible features or risk descriptors between already-known
physical regimes. SolarStorm must not introduce an `A -> B` transition regime
until the base regimes A and B are themselves empirically clear and robust.

The promoted Onda 2R regime family is:

- `southerly_disrupted`
- `standard_nw`
- `strong_nw_foehn`
- `calm_radiative`

These names are frozen in `docs/regime_model_card.md`. They must be derived
from causal morning features, not from final Tmax timing.

This repaired family is still a baseline ontology under ADR-012. Onda 2E must
decide, with artifact-backed evidence, which rules are retained, adapted,
rejected, or replaced before regime-dependent model work resumes.

## Late Tmax Definition

The old fixed rule:

```text
late_warming = tmax_hour >= 18
```

is deprecated.

The new target must be relative to month and physical regime:

```text
late_tmax_event =
  tmax_hour > q90_train(tmax_hour | month, physical_regime)
```

or an equivalent preregistered train-only threshold. A continuous companion
feature may be:

```text
late_tmax_anomaly =
  tmax_hour - median_train(tmax_hour | month, physical_regime)
```

All thresholds must be learned on the training window only inside the
walk-forward loop.

## Explicit Rejections

The project must not fix the Onda 4 NO-GO by overwriting causal `regime_label`
with a full-day `late_warming` label. That would inject future information into
a feature column and would make H3-style validation dishonest.

A causal proxy for late Tmax may be built, but it must be treated as a risk
score or probability, not as a hard physical regime.

Likewise, a proxy for clearing, wind rotation, or regime-like intraday
alteration may be investigated as a feature, but not promoted as a new regime
category while R2 still blocks on the base physical regime family.

## Consequences

- ADR-006 remains historical context but is superseded for promoted regime
  semantics.
- Onda 3 remains blocked until the post-Onda 2R Onda 4 rerun has no dead
  physical regime. The 2026-06-06 rerun still blocks on `calm_radiative` and
  `standard_nw`.
- Onda 4 R2 must check dead physical regimes, not outcome timing events.
- Late warming becomes part of a late-Tmax / late-spike risk package, tied to
  month, regime, and lead time.
- Intraday state-change work remains downstream of base-regime validation.
- ADR-012 requires a decision register before any repaired regime rule can be
  treated as production climatological truth.

## Required Follow-Up

Onda 2R implementation follow-up:

1. Freeze a reproducible regime EDA artifact and model card. Done.
2. Implement causal physical regime labels. Done.
3. Add train-only month/regime Tmax timing norms. Done for R9 audit; future
   model features must still compute timing priors train-only inside
   walk-forward.
4. Revalidate affected features. Done on regenerated 2026-06-06 artifacts.
5. Rerun Onda 4 with updated R2/R7/R8/R9 semantics. Done; verdict remains
   NO-GO due physical-regime R2 weakness.

## References

- `update.txt`
- `research/regime_clustering_report.md`
- `research/run_regime_transition_eda.py`
- `reports/robustness/2026-06-06-robustness-report.md`
- `docs/decisions/006-regime-classifier.md`
- `docs/decisions/012-evidence-to-decision-gate.md`
