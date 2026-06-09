# Wellington Climatology Thesis Atlas - Design

Date: 2026-06-06
Status: Superseded as source-of-truth by `reports/onda2e/thesis_atlas_v1.md`; retained as design context

## Purpose

Onda 2E creates a data-first climatology atlas for Wellington Airport before
SolarStorm continues feature engineering or model work. The atlas is not a
feature factory. The official EDA base is now
`reports/onda2e/thesis_atlas_v1.md`, which adopts 251 climatology theses. The
implementation must parse that file, audit pertinence/testability, and execute
EDA from those thesis IDs.

ADR-012 adds a stricter requirement: the atlas is not an archive. Every
resolved EDA result must become a registered decision before it can affect
regimes, features, model inputs, Onda 4 reruns, or Onda 3 planning.

The immediate reason is the repeated discovery that promoted concepts were
shallow:

- `late_warming` was treated as a regime even though it is an ex-post timing
  outcome.
- the physical regimes were promoted before the regime evidence was deep enough
  to survive R2.
- the current `southerly_disrupted` class is dominated by a cooling rule that
  has not yet been climatologically explained.

Onda 2E exists to prevent the next round of trial-and-error around wind, cloud,
pressure, rain, cooling, clearing, foehn, late spikes, and Tmax timing.

## Non-Goals

- Do not create 251 features.
- Do not train Onda 3 models.
- Do not tune the production regime classifier.
- Do not relax Onda 4 R2.
- Do not create a financial, EV, Polymarket, or trading layer.
- Do not treat old Wellington reports as truth; they are thesis sources only.
- Do not promote any thesis into `features.parquet` without a later feature
  design and walk-forward validation path.
- Do not let EDA artifacts sit unused. Each resolved thesis must become a
  decision, rejection, block, adaptation, regime-design item, feature-candidate
  item, or quarantined baseline.

## Core Objects

### Thesis

A thesis is a falsifiable meteorological claim about Wellington Tmax behavior.
It may later inspire a feature, segment, label, diagnostic, or blocked-data
requirement, but it is not itself a feature.

Each thesis must have:

- `id`: stable ID, for example `WCT-WIND-014`.
- `domain`: one of the atlas domains below.
- `claim`: precise natural-language statement.
- `physical_rationale`: why the claim may be true in Wellington.
- `observable_evidence`: METAR/label fields needed to test it.
- `causal_availability`: whether evidence exists by each CP.
- `target_relation`: what it claims to affect, such as remaining warming,
  Tmax hour, late spike, model error, or regime membership.
- `strata`: required splits, usually month/season, CP, lead time, wind sector,
  and candidate regime.
- `test_plan`: descriptive and statistical checks.
- `leakage_risk`: what would make the test dishonest.
- `status`: `candidate`, `supported`, `rejected`, `blocked`, or `unresolved`.
- `decision_note`: short explanation of the current status.
- `artifact_refs`: links to plots, tables, or markdown evidence.

### Atlas

The atlas is the collection of theses plus generated evidence. It should make
the local climatology inspectable before feature work resumes.

Required outputs:

- thesis registry JSONL/CSV for machine use;
- markdown index grouped by domain/status;
- domain reports with plots/tables;
- blocked-data register;
- promotion queue listing only supported theses that may deserve feature design;
- rejection register so failed ideas do not keep returning in new words;
- regime design queue for theses that can repair or replace the current
  heuristic regime ontology;
- quarantined-baseline register for old rules kept only as diagnostic
  comparators.

## Thesis Domains

Onda 2E should cover these domains densely enough that the project can explain
what it knows and what it does not know.

| Domain | Purpose |
|--------|---------|
| `REGIME` | Rebuild physical regime understanding from data instead of names. |
| `COOLING` | Separate radiative, frontal, southerly, precipitation, maritime, and artifact cooling. |
| `WIND` | Study direction, vector rotation, persistence, speed, and NW/N/NE/S/SE sectors. |
| `FOEHN_DRYING` | Test dry NW/N flow, dewpoint collapse, and false foehn sectors. |
| `RAIN_CLEARING` | Study precipitation timing, post-rain clearing, recovery, and suppression. |
| `CLOUD` | Evaluate METAR cloud cover/base-height proxies and their limits. |
| `PRESSURE` | Study pressure tendency, pre-frontal windows, post-frontal stabilization, and clearing. |
| `HUMIDITY` | Study dewpoint depression, humidity recovery, and maritime caps. |
| `TMAX_TIMING` | Learn month/regime Tmax-hour norms and late Tmax definitions. |
| `LATE_SPIKE` | Explain days where apparent settled markets can still flip. |
| `CP_LEAD_TIME` | Identify which phenomena are observable at CP20-CP23 and which are not. |
| `DATA_QUALITY` | Audit METAR cadence, SPECI-like intervals, missing data, and rounding artifacts. |
| `INTERACTION` | Test combined phenomena such as wind + pressure + cloud or rain + clearing. |

The adopted volume is 251 theses from `reports/onda2e/thesis_atlas_v1.md`.
Coverage, testability, and evidence quality matter more than the count.

## Evidence Levels

Each thesis must be assigned one evidence level:

| Level | Meaning | Allowed Next Step |
|-------|---------|-------------------|
| `E0_candidate` | Plausible claim, not yet tested. | Run atlas diagnostics only. |
| `E1_descriptive` | Tables/plots show a stable pattern. | Keep studying; no feature promotion yet. |
| `E2_causal_available` | Pattern is visible before at least one CP without leakage. | Eligible for feature design. |
| `E3_walkforward_signal` | Later validation shows predictive value against nulls. | Eligible for model input. |
| `blocked_external_data` | Requires unavailable data such as SST/NWP/cloud product. | Keep blocked; do not approximate silently. |
| `rejected` | Data contradicts or fails to support the claim. | Do not reintroduce without new evidence. |

Onda 2E itself only needs to reach E0-E2. E3 belongs to later feature validation.

## Evidence-to-Decision Gate

Every domain EDA report must update or propose updates to the Onda 2E decision
register. Allowed decision statuses are:

| Decision status | Meaning |
|---|---|
| `SUPPORTED` | Data supports the thesis descriptively. |
| `REJECTED` | Data contradicts or fails to support the thesis. |
| `ADAPTED` | Original thesis was too crude, but data produced a better formulation. |
| `BLOCKED` | Missing data, leakage risk, or insufficient power prevents resolution. |
| `PROMOTED_TO_REGIME_DESIGN` | Evidence can influence replacement regime ontology. |
| `PROMOTED_TO_FEATURE_CANDIDATE` | Evidence is causal-available and may enter feature design. |
| `QUARANTINED_BASELINE` | Existing heuristic remains only as diagnostic comparator. |

Every decision must cite artifact paths, tested strata, sample-size warnings,
causal availability, leakage risk, rationale, and next allowed action.

The current regime classifier is a quarantined baseline until the decision
register explicitly retains, adapts, or replaces each relevant rule. Fixed
thresholds such as `tmax_hour >= 18`, `min_delta_t_per_h < -2`, and
`foehn_score > 60` are not production truth merely because they exist in code.

## Causal Rules

Every thesis must explicitly state what is available at CP20, CP21, CP22, and
CP23. A full-day label may be used only as an evaluation target or segment, not
as pre-CP evidence.

Examples:

- final `tmax_hour` can define a target segment but cannot define a CP feature;
- post-CP wind rotation can explain a failure mode but cannot be used as a
  morning predictor unless converted into a historical train-only prior;
- late Tmax must be month/regime-relative, not a fixed `18:00` rule;
- intraday state changes are not new regimes; they are potential risk features
  between already validated physical regimes.

## Domain Report Pattern

Each domain report should follow the same structure:

1. Scope and questions.
2. Data fields used.
3. Known limitations.
4. Thesis table.
5. Descriptive climatology by month and CP.
6. Relationship to remaining warming, final Tmax, Tmax hour, and late spikes.
7. Relationship to current model errors or validated feature-null errors when
   available.
8. Supported/rejected/blocked thesis decisions.
9. Candidate implications for later feature work.

A domain report without decision-register implications is incomplete.

## Initial Thesis Seed Strategy

The seed set has already been generated in `reports/onda2e/thesis_atlas_v1.md`.
Future work may adapt, replace, or block individual theses, but that file is
the base registry for Onda 2E.

The original seed sources were:

- existing H1-H23 catalog;
- Onda 2R/Onda 4 failure findings;
- old Wellington reports, treated as untrusted thesis sources;
- current data artifacts: `obs.parquet`, `labels.parquet`, `features.parquet`;
- physical decomposition of Wellington meteorology around Cook Strait, terrain,
  frontal passage, NW flow, maritime caps, cloud, pressure, and diurnal timing.

The seed generation should intentionally overproduce claims, then deduplicate
them into a registry. Duplication is acceptable at draft time; silent omission
is more dangerous than pruning.

## Promotion Rules

A thesis may enter a later feature-design queue only when all are true:

- status is `supported`;
- evidence level is at least `E2_causal_available`;
- leakage risk is documented;
- the effect is stratified by CP and month, or the report explains why that is
  unnecessary;
- the thesis is not merely a rediscovery of final outcome information;
- the required data exists in the current stack or is explicitly blocked as an
  external-data requirement.

Supported theses still do not become features automatically. A later feature
wave must choose a small subset and define walk-forward validation.

## Relationship To Current Waves

Onda 2E sits between Onda 2R/Onda 4 and Onda 3.

- Onda 2R remains the current regime repair record.
- Onda 4 remains the robustness gate and currently blocks Onda 3.
- Onda 2E explains the climatology deeply enough to decide how to repair
  regimes, cooling, timing, and candidate features without trial-and-error.
- Onda 3 remains blocked until Onda 2E produces decision registers, promotion
  queues, and Onda 4 blockers have a data-backed repair path.

## Exit Criteria

Onda 2E is complete when:

1. The 251 thesis candidates in `reports/onda2e/thesis_atlas_v1.md` have been
   parsed, audited, and reconciled.
2. Every thesis has domain, causal availability, leakage risk, and status.
3. Each domain has a markdown report with tables/plots or a documented block.
4. Regime and cooling claims are explicitly resolved enough to propose a
   classifier-repair plan, or explicitly blocked with reasons.
5. The project has a promotion queue of supported, causal theses and a rejection
   register of failed ideas.
6. The project has a regime design queue and a quarantined-baseline register.
7. ROADMAP and Onda 4 docs reflect that feature/model work remains blocked until
   this atlas is reviewed.

## Default Design Choices

The atlas may use full-day outcomes as targets or evaluation segments, provided
they are never used as CP evidence. Each report must label this distinction
explicitly.

Onda 2E should cover all 13 domains in the registry, but implementation should
start with the highest-risk domains declared by the official atlas:

- `REGIME`
- `COOLING`
- `WIND`
- `TMAX_TIMING`
- `RAIN_CLEARING`
- `PRESSURE`

Blocked external-data theses stay in the same thesis registry with
`blocked_external_data` status. A separate future-data backlog can be generated
from that registry later, but the atlas should preserve one unified view of
what the climatology needs.

## First Execution Finding

The first parser/audit pass found that the official atlas summary declares 251
theses and 6 external-data blocks. The markdown body contains 231 explicit
thesis IDs; 20 `IX` interaction theses are declared in the summary but missing
their detailed rows, and `WCT-TIMING-017`/`WCT-TIMING-018` are referenced
outside the quick-reference registry. These 22 entries are preserved in the
machine registry with `registry_missing_detail` status until the source atlas is
completed or adapted.
