# Onda 4 Robustness Plan

Status: implemented; v2.1 candidate rerun is GO; binary macro design review is eligible
Date: 2026-06-09

Onda 4 is the robustness and scope-control wave. It stress-tests the Onda 2
feature-null foundation before Onda 3 invests in production models.

The first real run completed on 2026-06-06 and produced
`reports/robustness/2026-06-06-robustness-report.md`. The implementation is in
place, but the foundation is not cleared for Onda 3 because R2 found
`late_warming` as a dead regime. Follow-up analysis showed this is an ontology
failure: `late_warming` is an ex-post timing event, not a causal physical
regime.

The post-Onda 2R rerun regenerated `data/features.parquet`,
`reports/2026-06-06/validated_feature_contract.json`, and the same dated
robustness report path with repaired physical regimes and R9. It remains
NO-GO, but for a different reason: R2 now finds `calm_radiative` and
`standard_nw` as dead physical regimes. This is no longer the old
`late_warming` structural error; it is a real segment-robustness blocker.

The v2.1 candidate rerun completed on 2026-06-08 against
`reports/regime-design/features_candidate_v2_1.parquet` and produced
`reports/robustness-v2_1/2026-06-08-robustness-report.md` with verdict `GO`.
This candidate copy replaces `regime_label` with
`macro_nw_continuum`/`macro_southerly_flow` from the non-production v2.1
assignment artifact. It does not overwrite `data/features.parquet` or promote
the production classifier.

This wave does not create a financial layer. Trading, EV, position sizing,
shadow decisions, and Polymarket execution remain on hold until a model proves
real predictive skill, calibrated uncertainty, and reliable stay-out behavior.

## Scope Rules

1. Model first. No financial or operational market layer is allowed before the
   predictive model gate passes.
2. Predictive skill must not be nowcasting. A result that only works after Tmax
   is already effectively known does not count as predictive value.
3. Fixed CPs are evaluation cutoffs and market-contract timestamps, not claims
   about when physical Tmax should occur.
4. METAR ingestion and feature processing are continuous. Passing a CP must not
   stop the system from ingesting new observations or updating the day state.
5. Evaluation must be stratified by CP, lead time, regime, month, and expected
   Tmax-hour buckets so a fixed CP grid does not hide non-physical behavior.
6. Late spikes are a first-class physical failure mode. Onda 4 must preserve the
   evidence needed to study cases where the market treats Tmax as settled but a
   physically plausible new Tmax can still occur.
7. Open-Meteo and other NWP sources are future model inputs for late-spike and
   uncertainty investigation, not Onda 4 trading inputs.

## Entry Checklist

- Fresh `python -m solarstorm features` output exists in `data/features.parquet`.
- Fresh `python -m solarstorm validate` artifacts exist in `reports/YYYY-MM-DD/`.
- Fresh `python -m solarstorm leaderboard` artifacts exist in `reports/leaderboard/`.
- No promoted artifact is marked superseded.
- `ruff check .` passes.
- `uv run pytest -q -m "not network"` passes.

## Required Onda 4 Deliverables

### R1: Per-Year Replication

Re-run validation one test year at a time. A feature that only works in the
pooled holdout cannot unblock Onda 3.

### R2: Regime Sensitivity

Report pass/fail by causal physical regime. The old required list
(`calm`, `transition`, `late_warming`, `foehn_nw`, `disrupted`) is superseded
for promoted semantics because `late_warming` is not a causal regime.

After Onda 2R, R2 should check the repaired physical regime family, not
post-facto timing events.

Intraday state changes are not a fifth/sixth regime family. They are potential
features or risk descriptors between already-known physical regimes. Because the
post-Onda 2R base regimes still fail R2, transition-risk modeling remains
non-blocking and on hold for Onda 3+ design.

### R3: Causal Re-Audit

Re-check validated features against the causal firewall. Any feature using
observations at or after its evaluation cutoff is a block.

### R4: Drift Trend

Measure whether feature-null skill declines over calendar time. A significant
negative trend is at least a warning and may become a block if paired with R1 or
R2 weakness.

### R5: Fresh Gate Re-Run

Validated features must still pass G1-G5 on fresh artifacts.

### R6: Anti-Nowcast Lead-Time Check

Report skill by lead-time bucket and by whether Tmax had already occurred before
the cutoff. Skill concentrated only after Tmax is already known is nowcast
behavior and must not be promoted to Onda 3.

### R7: Physical Tmax-Hour Stratification

Evaluate CP results by regime, month, and expected/observed Tmax-hour buckets.
The project must not force a fixed CP grid onto regimes whose Tmax timing is
physically variable.

Fixed 18:00 late-warming logic is deprecated. Tmax timing checks must use
train-only month/regime timing norms.

### R8: Late-Spike Evidence Pack

Produce a local artifact listing late-spike candidates: days where `k_cp` looked
settled at one or more CPs but the final Tmax increased later. This artifact is
for model research and Open-Meteo/NWP feature design, not trading.

Late warming belongs with this timing-risk family. It should become
`late_tmax_event` or a calibrated risk score, not a physical regime.

### R9: Late-Tmax Risk Baseline

Produce a separate month/regime late-Tmax timing baseline, currently audited as
`q90(tmax_hour | month, causal_physical_regime)`. This baseline is an
evaluation/risk artifact, not a causal feature unless recomputed train-only
inside a future walk-forward model harness.

## Pre-Onda 2R Run Result

Historical summary of the first 2026-06-06 run. The original date-based report
path was overwritten by the post-Onda 2R rerun; keep this table as the retained
pre-Onda 2R evidence until robustness reports are made timestamped.

| Check | Result | Status |
|-------|--------|--------|
| R1 | 8 passing years | PASS |
| R2 | `late_warming` has no passing feature | BLOCK |
| R3 | 0 causal violations | PASS |
| R4 | Mann-Kendall p=0.9015, no negative warning | PASS |
| R5 | Fresh gates re-pass | PASS |
| R6 | Skill is not nowcast-only | PASS |
| R7 | No fixed-CP artifact detected | PASS |
| R8 | Late-spike artifact produced | PASS |
| R9 | Not audited in the pre-Onda 2R run | PENDING |

Verdict: NO-GO. This result is retained as historical evidence of the old
ontology failure.

## Post-Onda 2R Rerun Result

Source report: `reports/robustness/2026-06-06-robustness-report.md`

Input hashes:

- `data/features.parquet`:
  `1b20e5b657ab2f0c58c6e177c973a0f511893e34edf519e111e3052865a7931e`
- `data/labels.parquet`:
  `bc19ebafb2f4964b54fa3a70677b5e7ad7c435b6ca817b00525bc9d5b786a468`
- `reports/2026-06-06/validated_feature_contract.json`:
  `7392ce9dc630feacd854983a97a07dfc9f42d3d10fb8dac77ce2fcfeb9d5eb4f`

| Check | Result | Status |
|-------|--------|--------|
| R1 | 8 passing years | PASS |
| R2 | `calm_radiative`, `standard_nw` have no passing feature | BLOCK |
| R3 | 0 causal violations | PASS |
| R4 | Mann-Kendall p=0.7105, no negative warning | PASS |
| R5 | Fresh gates re-pass | PASS |
| R6 | Skill is not nowcast-only | PASS |
| R7 | No fixed-CP artifact detected | PASS |
| R8 | Late-spike artifact produced, 14,892 candidates | PASS |
| R9 | Month/regime q90 late-Tmax baseline exists | PASS |

Verdict: NO-GO. Onda 3 remains blocked until R2 shows no dead causal physical
regime. The next investigation should determine whether the current
`calm_radiative` and `standard_nw` labels are underpowered, poorly separated,
or require different features/model treatment. The companion cooling-rule
experiment in `reports/regime/2026-06-06-cooling-rule-experiment.md` shows that
disallowing cooling as a standalone disruption trigger would move 13,367 rows
out of `southerly_disrupted`, so the cooling trigger should be investigated
before adding any new transition/regime category.

## Regime Ontology v2.1 Candidate Rerun Result

Source report: `reports/robustness-v2_1/2026-06-08-robustness-report.md`

Input hashes:

- `reports/regime-design/features_candidate_v2_1.parquet`:
  `b2167727b342fad8c43f17d8f14fadf03cc13d32c9b022fc53e1e44ef89afe53`
- `data/labels.parquet`:
  `bc19ebafb2f4964b54fa3a70677b5e7ad7c435b6ca817b00525bc9d5b786a468`
- `reports/2026-06-06/validated_feature_contract.json`:
  `7392ce9dc630feacd854983a97a07dfc9f42d3d10fb8dac77ce2fcfeb9d5eb4f`

| Check | Result | Status |
|-------|--------|--------|
| R1 | 8 passing years | PASS |
| R2 | No dead regimes under `macro_nw_continuum,macro_southerly_flow` | PASS |
| R3 | 0 causal violations | PASS |
| R4 | Mann-Kendall p=0.5362, increasing direction, no warning | PASS |
| R5 | Fresh gates re-pass | PASS |
| R6 | Skill is not nowcast-only | PASS |
| R7 | No fixed-CP artifact detected | PASS |
| R8 | Late-spike artifact produced, 14,892 candidates | PASS |
| R9 | Month/regime q90 late-Tmax baseline exists | PASS |

Verdict: GO. This is strong evidence for Opcao A, but it did not authorize
skipping Onda C. The corrected Onda C Regime Measurement Reset ran on
2026-06-08 as a non-production classifiability benchmark using the audited
physical meteorological feature basis. Its feature-basis audit artifacts are
`reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.csv`
and `reports/regime-classifiability/regime_classifiability_feature_basis_audit_v1.md`.
The audit included 8 approved physical features, rejected `precip_pre_cp_sum`
as constant, and did not use the forbidden unrestricted numeric fallback.

Onda C first returned the overall verdict `KEEP_IN_REGIME_DESIGN_REVIEW`. The
follow-up v2.2 sprint restored `macro_calm_radiative` as a protected macro with
2,572 assignment rows, but its R2 screen blocks the 3-macro path because
`macro_calm_radiative` has 0/92 passing R2 rows. The Onda C rerun against v2.2
records `BLOCK_ONDA_C_PROMOTION` and is retained as historical evidence for the
failed 3-macro route. Production classifier promotion and Onda 3 design review
remain separate gates. The v2.3 diagnostic then ran and records
`CALM_RADIATIVE_VALIDATION_TARGET_GAP`: calm/radiative has 2,572 assignment
rows and smallest CP support of 502 rows, but its R2 median `n_days` is 27 and
it still has 0/92 passing R2 rows. `CEXP-CALM-RADIATIVE-001` then generated
the target-only month x CP diagnostic: 48 calm/radiative cells, 20 underpowered
cells, median p50 remaining warming 3.5 C, and median p50 Tmax hour 13:00.
`CEXP-CALM-RADIATIVE-002` then screened 8 calm-specific feature hypotheses and
found 1 preliminary candidate signal, `cloud_cover_suppression`, with 4 weak
signals, 2 constants, and 1 underpowered feature. `CEXP-CALM-RADIATIVE-002B`
then validated that signal as pre-CP cloud evidence rather than proxy/artifact:
overall slope -2.89, controlled slope -1.75, controlled retention 0.605,
negative slopes in 4/4 CP cells and 25/25 supported month x CP cells, and max
proxy correlation 0.340. CEXP-003 demote/split was not triggered; this is still
not production promotion.

The later binary macro validation turns this into a design-review entry point:
`macro_southerly_flow` versus `macro_non_southerly` records
`READY_FOR_ONDA3_DESIGN_REVIEW`, with predictive assignment AUC 0.9886,
stability 0.8089, temporal stability 0.9917, and 0 dead binary macros. This
allows Onda 3 baseline-first model design, but it does not promote production.
`macro_non_southerly` remains a weak-sensitivity segment and must be modeled
with continuous features and slice diagnostics.

## Non-Scope

- Live trading.
- Shadow trading or shadow decisions.
- EV, Sharpe, drawdown, position sizing, or bankroll policy.
- Polymarket API integration.
- Production deployment.
- Open-Meteo/NWP ingestion implementation.
- Production model promotion.

## Exit Gate

Onda 3 may proceed only when the active sequence has no blocking failures. The
v2.1 candidate rerun satisfies the Onda 4 robustness criteria below, the v2.2
calm/radiative route is superseded, and the binary macro validation now clears
design review for a baseline-first Onda 3 sprint. This is not production
approval:

- R1 has enough passing years.
- R2 has no dead causal physical regime.
- R3 has zero causal violations.
- R5 re-passes G1-G5.
- R6 shows predictive skill before the answer is effectively known.
- R7 shows skill is not an artifact of fixed CP timing.
- R9 produces a separate late-Tmax risk baseline.

Warnings from R4, R8, late-Tmax timing analysis, and weak
`macro_non_southerly` R2 sensitivity must be carried into the Onda 3 model plan
as explicit modeling requirements. Onda 4 must not be made to pass by injecting
full-day outcome labels into causal feature columns.

## Onda 3 Baseline Handoff

The first Onda 3 baseline-first model run has now been generated under
`reports/onda3/`. It remains experiment-only, but it is eligible for the next
model robustness review because `onda3_decision_update_v1.csv` records
`READY_FOR_ONDA4_MODEL_RERUN`.

Initial comparison:

- train-mean null MAE: 2.8120
- ridge challenger MAE: 1.3487
- production status: `EXPERIMENT_ONLY`

The follow-up Onda 4 model review must stress-test this result before any
production claim. It must preserve the causal firewall, verify no target/proxy
columns entered the live feature manifest, check slice failures by CP/month and
binary macro, and treat uncertainty/abstention as gating evidence rather than
report decoration.

## Onda 4M Model Review Result

The active follow-up Onda 4M has now generated a model robustness review of the
experiment-only Onda 3 baseline. It is documented separately from the historical
R1-R9 feature/regime hardening wave:

- Spec:
  `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`
- Plan:
  `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`

Onda 4M uses M1-M8 model gates:

- M1 input artifact integrity.
- M2 causal manifest safety.
- M3 challenger lift over train-mean null.
- M4 temporal robustness.
- M5 CP/month/binary macro slice robustness.
- M6 uncertainty and abstention evidence.
- M7 anti-nowcast/model timing.
- M8 decision hygiene.

The planned outputs live under `reports/onda4-model/`. Every row must remain
`EXPERIMENT_ONLY`. A passing review may only authorize the next Onda 3 model
iteration; it does not authorize production, deployment, market execution, EV,
position sizing, or trading.

Generated outputs:

- `reports/onda4-model/onda4_model_input_audit_v1.csv/.md`
- `reports/onda4-model/onda4_model_gate_results_v1.csv/.md`
- `reports/onda4-model/onda4_model_slice_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_uncertainty_review_v1.csv/.md`
- `reports/onda4-model/onda4_model_decision_update_v1.csv/.md`
- `reports/onda4-model/onda4_model_robustness_report_v1.md`

Result: M1-M8 all pass. The decision update records
`READY_FOR_ONDA3_NEXT_MODEL_ITERATION`, with
`production_status = EXPERIMENT_ONLY`. This authorizes the next experimental
Onda 3 model iteration only.
