# Regime Candidate Validation - 2026-06-07

This is not a production classifier.
Candidate labels are assigned offline for Onda 4 R2 validation only.

- Assignment rows: 21824
- Candidate ontology families: 4
- Dead candidate families: 2

## Validation Scope

| Audit item | Status | Detail |
|---|---|---|
| r2_validation_mode | WARN | Candidate R2 screening uses one annual walk-forward window; run full Onda 4 before production promotion. |
| r2_cp_set | PASS | 20:00,21:00,22:00,23:00 |
| r2_test_starts | PASS | 2025-01-01 |

## Candidate Family Counts

| Candidate family | Rows |
|---|---:|
| candidate_maritime_cloudy | 31 |
| candidate_mixed_or_transition | 320 |
| candidate_nw_or_foehn | 15638 |
| candidate_southerly_disrupted | 5835 |

## R2 Candidate Result

| Candidate family | Status |
|---|---|
| candidate_maritime_cloudy | DEAD |
| candidate_mixed_or_transition | DEAD |
| candidate_nw_or_foehn | PASS |
| candidate_southerly_disrupted | PASS |

## Next Action

Keep the candidate in regime-design review and revise dead families before a full Onda 4 rerun.