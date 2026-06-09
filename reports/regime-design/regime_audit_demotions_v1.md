# Regime Deadlock Pivot Decision - 2026-06-08

This is not a production classifier.
Status: experiment-only; not a production classifier.

- Decision: PIVOT_ACCEPTED
- Active path: OPTION_C_AUDIT_DEMOTION_PLUS_OPTION_A_BINARY_EXPERIMENT
- Superseded path: V22_V23_CEXP_THRESHOLD_RESTORATION_LOOP

## Gate Roles

| macro | role | blocks gate | R2 pass rows | median n_days |
|---|---|---:|---:|---:|
| macro_nw_continuum | PRODUCTION_BLOCKING | True | 23 | 210.0 |
| macro_southerly_flow | PRODUCTION_BLOCKING | True | 47 | 110.0 |
| macro_calm_radiative | AUDIT_ONLY | False | 0 | 27.0 |

## Note on Audit Demotion

Demotion is not deletion. `macro_calm_radiative` is retained as an audit segment.
It will be reported separately but will not block the production macro gate.
The production-blocking macro set for the pivot review is
`macro_nw_continuum` and `macro_southerly_flow`.
