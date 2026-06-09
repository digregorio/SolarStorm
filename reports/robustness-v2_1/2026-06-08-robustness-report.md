# Robustness Hardening Report - 2026-06-08

**Config version:** 1.0
**Generated:** 2026-06-08T00:43:03.566378+00:00
**Verdict:** **GO**

## Input Artifacts

- **features:** sha256=b2167727b342fad8c43f17d8f14fadf03cc13d32c9b022fc53e1e44ef89afe53
- **labels:** sha256=bc19ebafb2f4964b54fa3a70677b5e7ad7c435b6ca817b00525bc9d5b786a468
- **validated_feature_contract:** sha256=7392ce9dc630feacd854983a97a07dfc9f42d3d10fb8dac77ce2fcfeb9d5eb4f

## 1. Per-Year Replication

Years with at least one passing feature: 8
Warning threshold: < 5; block threshold: < 3

| Year | Rows | Passing |
|------|------|---------|
| 2018 | 44 | 19 |
| 2019 | 44 | 14 |
| 2020 | 44 | 12 |
| 2021 | 44 | 20 |
| 2022 | 44 | 24 |
| 2023 | 44 | 23 |
| 2024 | 44 | 21 |
| 2025 | 44 | 23 |

## 2. Regime Sensitivity

Dead regimes: None

## 3. Drift Trend

Mann-Kendall S: 6.00
p-value: 0.5362
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
| R2: Dead regimes | None | PASS |
| R3: Causal firewall | 0 violations | PASS |
| R4: Drift trend | p=0.5362 | PASS |
| R5: Fresh gate re-run | True | PASS |
| R6: Anti-nowcast lead-time | True | PASS |
| R7: Month/regime Tmax timing norms | artifact=False | PASS |
| R8: Late-spike evidence pack | produced=True | PASS |
| R9: Late-Tmax risk baseline | exists=True | PASS |

Final verdict: **GO**