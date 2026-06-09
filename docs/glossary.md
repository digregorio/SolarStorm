# Glossary — SolarStorm Terminology

## Project Methodology

| Term | Definition |
|------|------------|
| **Onda** | Portuguese for "wave." Development phase: Onda 0 (scaffold), Onda 1 (baselines), Onda 2 (prove predictive value), Onda 2E (climatology atlas), Onda 2E-Gate (evidence decisions), Onda 3 (ML models) |
| **P1-P6** | Six design principles: P1 Causal Firewall, P2 Evidence Over Parameters, P3 Hypotheses Must Be Testable, P4 Settlement Honesty, P5 Versioned Artifacts, P6 Evidence Must Become Decisions |
| **G1-G5** | Five frozen quality gates applied to every model: G1 null-not-beaten, G2 fallback dominance, G3 p50 collapse, G4 anti-nowcaster, G5 per-CP |
| **Evidence-to-Decision Gate** | ADR-012 gate requiring every EDA finding, regime rule, cooling rule, timing rule, and feature candidate to become a traceable decision before downstream use |
| **QUARANTINED_BASELINE** | Decision status for an old or current heuristic kept only as a diagnostic comparator, not as production truth |

## Data

| Term | Definition |
|------|------------|
| **METAR** | Aviation routine weather report. Text format containing temperature, dewpoint, wind, pressure, visibility, clouds |
| **IEM** | Iowa Environmental Mesonet. Free ASOS data archive at mesonet.agron.iastate.edu |
| **ASOS** | Automated Surface Observing System. US-standard weather station network |
| **ICAO** | Four-letter airport identifier. NZWN = Wellington, NZAA = Auckland, etc. |
| **NZWN** | Wellington International Airport ICAO code |
| **NZST/NZDT** | New Zealand Standard Time (UTC+12) / New Zealand Daylight Time (UTC+13) |
| **DST** | Daylight Saving Time. NZDT runs from last Sunday September to first Sunday April |

## Labels and Features

| Term | Definition |
|------|------------|
| **Tmax** | Daily maximum temperature (integer °C). The Polymarket settlement target |
| **CP** | Checkpoint. A specific UTC hour when a forecast is issued. CP20 = 20:00 UTC, CP23 = 23:00 UTC |
| **k_cp** | Maximum integer temperature observed *before* a checkpoint. The best "nowcast" available at CP time |
| **remaining_warming** | `Tmax - k_cp`. How much warming remains after the checkpoint. Core prediction target from Onda 3 |
| **risco_de_flip** | "Flip risk." Distance from the nearest 0.5°C rounding boundary. 0 = safe, 0.5 = max risk |
| **day_complete** | Boolean flag: day has ≥min_obs observations AND max gap ≤ max_gap_minutes |
| **tmax_hour** | Local hour when the daily Tmax occurred |
| **tmax_atypical_hour** | Tmax occurred outside 06:00-18:00 local (unusual, often weather-driven) |

## Baselines

| Term | Definition |
|------|------------|
| **L0 persistence** | Tmax = k_cp (temperature right now). The simplest possible forecast |
| **L1 dminus1** | Tmax = yesterday's Tmax. First-order autocorrelation baseline |
| **L2 climatology** | Tmax = DOY-smoothed climatological mean for this calendar day |
| **L3** | Intentionally skipped — reserved for a persistence-aware baseline |
| **L4 empirical conditional** | P(Tmax | month, CP, k_cp) from historical counts. REBAIXADO: never production |
| **REBAIXADO** | Portuguese for "demoted." L4 is explicitly demoted to baseline-only due to data sparsity |
| **best-null-per-CP** | The baseline with lowest MAE for a given CP. The hurdle every model must beat |
| **null baseline** | A simple forecasting rule used as a minimum quality bar (L0-L2) |

## Evaluation

| Term | Definition |
|------|------------|
| **Walk-forward** | Expanding-window cross-validation for time series. Train on [start, split], test on [split, split+365] |
| **Expanding window** | Training data grows at each split (never shrinks). Preserves temporal ordering |
| **Holdout window** | A fixed-length recent window (7, 14, or 30 days) for robustness or leaderboard assessment |
| **Bootstrap CI** | Confidence interval from 1000 resamples of the error distribution. Percentile method |
| **FDR** | False Discovery Rate. Benjamini-Hochberg correction for multiple hypothesis testing at α=0.05 |
| **MAE** | Mean Absolute Error. Primary deterministic metric |
| **RMSE** | Root Mean Squared Error. Penalizes large errors more than MAE |
| **bias** | Mean signed error. Positive = overpredict, negative = underpredict |
| **Bracket Match (BM)** | Fraction of forecasts where `round(p50) == truth` |
| **RPS** | Ranked Probability Score. Proper scoring rule for categorical probability forecasts |
| **CRPS** | Continuous Ranked Probability Score. Generalization of RPS for continuous distributions |
| **corr_diff** | `r(model, truth) - r(baseline, truth)`. Anti-nowcaster discriminant |
| **skill_score** | `1 - MSE_model / MSE_baseline`. Fraction of baseline error eliminated |

## Regimes

| Term | Definition |
|------|------------|
| **causal physical regime** | Weather-state label inferred only from observations available before the CP |
| **calm_radiative** | Candidate repaired regime: weak wind / radiative morning pattern |
| **standard_nw** | Candidate repaired regime: normal northerly or northwesterly flow |
| **strong_nw_foehn** | Candidate repaired regime: strong dry NW flow, foehn-like |
| **southerly_disrupted** | Candidate repaired regime: southerly change, cooling, rain, or frontal disruption |
| **late_warming** | Deprecated as a regime. Use late Tmax / late-spike risk instead |
| **late_tmax_event** | Ex-post timing label: Tmax occurs later than the train-only normal window for its month and physical regime |
| **late_tmax_anomaly** | Difference between observed Tmax hour and train-only expected Tmax hour for month and physical regime |
| **intraday state change** | Observed change in day characteristics such as clearing, cooling, wind rotation, or renewed NW flow. It is a feature/risk layer, not a new regime label |
| **foehn_score** | Composite: `nw_flow_strength * dewpoint_depression`. Higher = more foehn-like |
| **quarantined regime baseline** | Current or legacy regime logic retained for comparison until Onda 2E-Gate explicitly retains, adapts, or replaces it |

## Settlement

| Term | Definition |
|------|------------|
| **Polymarket** | Prediction market platform. Contracts settle on binary outcomes |
| **Commercial rounding** | `floor(dec + 0.5)` — half-up rounding. 14.5 → 15, -2.5 → -2. Contrast with Python's banker's rounding |
| **Integer settlement** | Polymarket contracts settle on integer degrees. Internal computation uses decimal (P1) |
| **prob_dist** | Probability mass function over integer Tmax values. Output of every forecast |
| **IC80** | 80% prediction interval. The narrowest integer range containing ≥80% of probability mass |

## Artifacts

| Term | Definition |
|------|------------|
| **Leaderboard** | Permanent scoreboard (P5). JSON+MD output comparing all baselines by CP |
| **Hypothesis results** | JSON+MD output from `validate` command. Each hypothesis × CP with gates |
| **Validated feature contract** | JSON output listing features that passed all gates. Input to feature selection |
| **obs.parquet** | Raw METAR observations from IEM, parsed into structured format |
| **labels.parquet** | Daily Tmax labels with per-CP k_cp columns |
| **features.parquet** | Feature columns for all hypotheses (H1-H23), dates, and CPs |
