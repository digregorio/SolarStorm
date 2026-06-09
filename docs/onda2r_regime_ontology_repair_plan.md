# Onda 2R Regime Ontology Repair Plan

Status: implemented in code and regenerated artifacts; Onda 4 R2 still blocks
Date: 2026-06-06

Onda 2R repairs the regime ontology before any Onda 3 model work. The goal is
to replace superficial hardcoded regimes with causal physical regimes and to
move late warming into a separate timing-risk target.

## Why This Exists

The 2026-06-06 Onda 4 run returned NO-GO because `late_warming` was treated as
a dead regime. The root cause is structural:

- `regime_label` is causal and computed before CP.
- `late_warming = tmax_hour >= 18` is only known after the day unfolds.
- Therefore `late_warming` cannot be a causal regime.

The correct fix is not to inject full-day labels into `regime_label`. The fix is
to separate physical weather state from late-Tmax outcome risk.

## Scope

### R0: Freeze EDA Evidence

- Promote `research/regime_clustering_report.md` into a versioned report under
  `reports/regime/`.
- Record feature set, window, data hashes, clustering method, K-selection
  metrics, and limitations.
- Treat the existing GMM/K=4 result as candidate evidence, not yet production
  truth.

### R1: Redefine Causal Physical Regimes

Candidate regime family:

- `southerly_disrupted`
- `standard_nw`
- `strong_nw_foehn`
- `calm_radiative`

Final names and the current deterministic heuristic are recorded in
`docs/regime_model_card.md`. The labels are now implemented in
`solarstorm/eda/_regimes.py` and exposed through `features.parquet`.

### R2: Separate Ex-Post Evaluation Labels

Add explicit post-facto labels only for evaluation and analysis, for example:

- `late_tmax_event`
- `late_spike_event`
- `tmax_hour_bucket`

These labels must not appear as model features unless transformed into
train-only historical priors.

### R3: Train-Only Tmax Timing Norms

Replace fixed `18:00` late-warming logic with train-only month/regime timing
norms:

```text
late_tmax_event = tmax_hour > q90_train(tmax_hour | month, physical_regime)
```

The Onda 4 audit now produces a separate month/regime q90 late-Tmax baseline
for R9. Any future predictive feature using these norms must compute them
inside the walk-forward training window. No global full-sample timing threshold
can be used for model validation.

### R4: Revalidate Affected Features

Features depending on the old regime ontology return to quarantine until
revalidated:

- `regime_label`
- `regime_score_argmax`
- `tmax_hour_by_regime_month`
- `late_warming_anomaly`
- any future month/regime timing feature

Features independent of the old regime labels may remain provisionally useful,
but Onda 4 must be rerun after the repaired feature set is produced.

The 2026-06-06 post-Onda 2R validation produced 28 validated pooled entries, 60
rejected entries, and 4 blocked entries. All validated contract entries are
pooled (`regime=all`), so they still require R2 segment robustness before Onda 3.

### R5: Rerun Onda 4

Update Onda 4 checks:

- R2: no dead causal physical regime.
- R7: no fixed-CP artifact under month/regime Tmax-hour norms.
- R8: late-spike evidence remains produced.
- New R9: late-Tmax risk baseline exists and is evaluated separately from
  deterministic Tmax MAE.

## Non-Scope

- Onda 3 model training.
- Open-Meteo/NWP ingestion implementation.
- Polymarket API, EV, position sizing, shadow trading, or live execution.
- Hardcoding full-day outcome labels into causal feature columns.

## Exit Gate

Onda 2R repair work is complete when:

1. ADR-006 is superseded by the new regime ontology.
2. Causal physical regimes exist in `features.parquet`.
3. Late Tmax is represented as a timing-risk target, not a regime.
4. Affected features are revalidated or explicitly rejected.
5. Onda 4 reruns without structural R2 failure.

Items 1-4 are implemented in code, documentation, and regenerated artifacts.
Item 5 is partially satisfied: the structural `late_warming` R2 failure is gone,
but the post-Onda 2R R2 gate still blocks on dead physical regimes
`calm_radiative` and `standard_nw`. Until that segment-robustness failure is
resolved, Onda 3 remains blocked.

## Post-Rerun Trigger Audit

Artifact: `reports/regime/2026-06-06-regime-trigger-audit.md`

The audit reconstructs the current classifier triggers on the regenerated
`features.parquet` without changing labels or gates. It shows that
`southerly_disrupted` is not being dominated by light precipitation in the
current artifact:

- `cooling` primary trigger: 16,382 rows.
- `southerly` primary trigger: 926 rows.
- `precip_trigger`: 0 rows.

Therefore, a precipitation-threshold change is not the first corrective move.
The next investigation should focus on whether the `min_delta_t_per_h < -2.0`
rule is too broad for morning CP slices and whether it is stealing otherwise
standard NW/foehn/radiative cases.

## Cooling-Rule Experiment

Artifact: `reports/regime/2026-06-06-cooling-rule-experiment.md`

The experiment simulates candidate trigger variants from the audit evidence
without changing `solarstorm/eda/_regimes.py`, `features.parquet`, validation,
or R2 gates.

When cooling is not allowed to be the sole disruption trigger, the simulated
distribution changes materially:

- `southerly_disrupted`: 17,308 rows currently; 3,941 rows under the candidate
  variants.
- `standard_nw`: 2,466 rows currently; 11,036 rows under the candidate variants.
- `strong_nw_foehn`: 1,309 rows currently; 4,055 rows under the candidate
  variants.
- `calm_radiative`: 625 rows currently; 2,676 rows under the candidate
  variants.

The largest simulated moves are from `southerly_disrupted` to `standard_nw`
(8,570 rows), `strong_nw_foehn` (2,746 rows), and `calm_radiative` (2,051
rows). This supports a targeted cooling-rule investigation before any new
regime taxonomy is promoted.

## Intraday State Changes

A change in wind, clearing, cooling, or warming during the day is not a new
regime label. It is a change in the day's observed characteristics and may
later become a risk/state feature between already-defined physical regimes.

Because the base regimes still fail R2, SolarStorm must not yet model
`A -> B` transition risk as if regimes A and B were already settled. The
sequence/risk layer should remain on hold until the physical regime ontology is
clear enough to pass robustness.
