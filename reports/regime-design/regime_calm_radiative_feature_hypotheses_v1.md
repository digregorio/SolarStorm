# CEXP-CALM-RADIATIVE-002 Feature Hypotheses - 2026-06-08

This is not a production classifier.
This artifact screens train-only calm/radiative feature hypotheses against the remaining_warming audit target.

- Candidate features screened: 8
- Candidate signals: 1
- Blocked leakage features: 0

## Feature Screen

| Feature | Rows | Corr | Slope | Variance | Leakage | Causal role | Disposition |
|---|---:|---:|---:|---|---|---|---|
| cloud_base_transparency | 1725 | None | None | CONSTANT | causal_candidate | CAUSAL_CANDIDATE_SCREEN | CONSTANT_FEATURE |
| cloud_cover_suppression | 1725 | -0.3176749019916105 | -2.891029076447252 | USABLE | causal_candidate | CAUSAL_CANDIDATE_SCREEN | CANDIDATE_SIGNAL |
| dewpoint_collapse_rate_3h | 1059 | 0.15932938507768898 | 0.7729478392277085 | USABLE | causal_candidate | CAUSAL_CANDIDATE_SCREEN | WEAK_SIGNAL |
| dewpoint_depression | 2089 | -0.001283106690579076 | -0.003254258572046875 | USABLE | causal_candidate | CAUSAL_CANDIDATE_SCREEN | WEAK_SIGNAL |
| nocturnal_plateau_flag | 2089 | None | None | CONSTANT | causal_candidate | CAUSAL_CANDIDATE_SCREEN | CONSTANT_FEATURE |
| pressure_trend_3h | 1059 | 0.07127375141210389 | 0.0035479216259785866 | USABLE | causal_candidate | CAUSAL_CANDIDATE_SCREEN | WEAK_SIGNAL |
| sst_maritime_cap | 0 | None | None | UNDERPOWERED | causal_candidate | CAUSAL_CANDIDATE_SCREEN | UNDERPOWERED_FEATURE |
| warming_rate_06_09 | 1059 | 0.18668482174718967 | 0.6468262142636434 | USABLE | causal_candidate | CAUSAL_CANDIDATE_SCREEN | WEAK_SIGNAL |

## Decision

CEXP-002 may nominate causal feature work for a future baseline, but it does not promote Onda 3, alter regime labels, or write production features.