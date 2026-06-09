# SolarStorm

Intraday Tmax probabilistic forecaster for NZWN (Wellington Airport).
The long-term target is Polymarket daily-maximum-temperature markets, but the
current project is model-first: no financial layer, EV, sizing, shadow trading,
or execution until a production model proves predictive skill.

SolarStorm is data-first before it is model-first. EDA findings cannot remain
unused reports and cannot become features or regimes by intuition. ADR-012
requires every thesis, regime rule, cooling rule, timing rule, and feature
candidate to pass an Evidence-to-Decision Gate before it can guide downstream
work.

## Quick Start

```bash
pip install -e ".[dev]"
python -m solarstorm ingest       # backfill METAR from IEM (2009-present)
python -m solarstorm features     # build feature columns
python -m solarstorm validate     # validate hypotheses with walk-forward CI
python -m solarstorm leaderboard  # generate baseline + feature-null leaderboard
python -m solarstorm robustness   # run Onda 4 go/no-go robustness checks
python -m solarstorm onda2e       # generate Onda 2E EDA + decision-gate registers
```

The original 2026-06-06 Onda 4 report returned NO-GO because the old ontology
treated `late_warming` as a causal regime. Onda 2R separated causal physical
regimes from late-Tmax risk, and the v2.1 non-production candidate later passed
a full candidate Onda 4 rerun. Corrected Onda C still kept regime design in
review, and the v2.2 calm/radiative restoration now blocks promotion because
`macro_calm_radiative` has 0/92 passing R2 rows. The v2.3 diagnostic explains
that blocker as `CALM_RADIATIVE_VALIDATION_TARGET_GAP`: calm/radiative has
2,572 assignment rows, but its R2 median `n_days` is only 27. The follow-up
`CEXP-CALM-RADIATIVE-001` target diagnostic found 48 calm/radiative month x CP
cells, 20 underpowered cells, median p50 remaining warming of 3.5 C, and median
Tmax hour of 13:00. `CEXP-CALM-RADIATIVE-002` then screened 8 train-window
calm-specific feature hypotheses and found 1 preliminary candidate signal,
`cloud_cover_suppression`; all rows remain `EXPERIMENT_ONLY`.
`CEXP-CALM-RADIATIVE-002B` validated that signal as pre-CP cloud evidence rather
than a proxy/artifact in the current train window: 1,725 rows, slope -2.89,
controlled slope -1.75, and 25/25 supported month x CP cells with negative
slopes. CEXP-003 demote/split was not triggered, but Onda 3 model work remains
blocked.

## Documentation

- [Architecture](docs/architecture.md) -- pipeline, modules, data flow
- [Principles](docs/principles.md) -- P1-P6 design principles
- [Decisions](docs/decisions/) -- architecture decision records
- [Replication Guide](docs/replication.md) -- adapting for another city
- [Bug Register](docs/bug-register.md) -- known issues and fixes
- [Glossary](docs/glossary.md) -- terminology
- [Roadmap](ROADMAP.md) -- wave status and on-hold scope
- [Onda 4 Robustness](docs/onda4_robustness_plan.md) -- anti-nowcast robustness plan
- [Onda 2R Regime Repair](docs/onda2r_regime_ontology_repair_plan.md) -- new regime ontology plan
- [Regime Ontology Design](docs/regime_ontology_design.md) -- causal regimes vs late-Tmax risk
- [Regime Model Card](docs/regime_model_card.md) -- implemented Onda 2R regime heuristic
- [ADR-012 Evidence-to-Decision Gate](docs/decisions/012-evidence-to-decision-gate.md) -- mandatory bridge from EDA to project decisions

## Legacy

The prior Wellington iteration is archived at `archive/wellington-legacy` (git tag).
See `quarentena/` for historical reports and postmortems.
