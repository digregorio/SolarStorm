# Robustness Hardening Report - 2026-06-06

**Config version:** 1.0
**Generated:** 2026-06-06T13:02:11.255519+00:00
**Verdict:** **NO-GO**

## Input Artifacts

- **features:** sha256=1b20e5b657ab2f0c58c6e177c973a0f511893e34edf519e111e3052865a7931e
- **labels:** sha256=bc19ebafb2f4964b54fa3a70677b5e7ad7c435b6ca817b00525bc9d5b786a468
- **validated_feature_contract:** sha256=7392ce9dc630feacd854983a97a07dfc9f42d3d10fb8dac77ce2fcfeb9d5eb4f

## 1. Per-Year Replication

Years with at least one passing feature: 8
Warning threshold: < 5; block threshold: < 3

| Year | Rows | Passing |
|------|------|---------|
| 2018 | 44 | 14 |
| 2019 | 44 | 13 |
| 2020 | 44 | 10 |
| 2021 | 44 | 19 |
| 2022 | 44 | 20 |
| 2023 | 44 | 20 |
| 2024 | 44 | 18 |
| 2025 | 44 | 20 |

## 2. Regime Sensitivity

Dead regimes: calm_radiative, standard_nw

## 3. Drift Trend

Mann-Kendall S: 4.00
p-value: 0.7105
Warning: False

## 4. Causal Firewall Re-Audit

Clean features: 11
Violations: 0

## 5. Anti-Nowcast Lead-Time

Nowcast-only evidence: False

## 6. Month/Regime Tmax Timing Norms

Fixed-CP artifact detected: False
Late-Tmax risk baseline exists: True

## 7. Late-Spike Evidence Pack

Late-spike candidates: 14892

## 8. Go/No-Go Verdict

| Criterion | Result | Severity |
|-----------|--------|----------|
| R1: Per-year replication | 8 passing years | PASS |
| R2: Dead regimes | calm_radiative, standard_nw | BLOCK |
| R3: Causal firewall | 0 violations | PASS |
| R4: Drift trend | p=0.7105 | PASS |
| R5: Fresh gate re-run | True | PASS |
| R6: Anti-nowcast lead-time | True | PASS |
| R7: Month/regime Tmax timing norms | artifact=False | PASS |
| R8: Late-spike evidence pack | produced=True | PASS |
| R9: Late-Tmax risk baseline | exists=True | PASS |

Final verdict: **NO-GO**