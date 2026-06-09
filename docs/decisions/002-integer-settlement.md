# ADR-002: Integer Settlement

- **Date:** 2026-06-04
- **Status:** Accepted

## Context

Polymarket daily-maximum-temperature contracts settle on the **integer degree Celsius** reported in the METAR TT/DD group. The raw METAR text is the authoritative source -- not `tmpf` (Fahrenheit decimal), not a derived conversion.

This creates two design constraints:
1. The parser must extract the integer degree from raw METAR text, not round a decimal `tmpf` conversion.
2. The forecaster's output must map internal decimal predictions to the integer bracket that Polymarket will settle on.

P1 (Causal Firewall) says: internal computation is decimal. P4 (Settlement Honesty) says: output is integer, with explicit quantification of boundary risk.

## Decision

**Internal decimal, integer output with commercial rounding.**

- `integer_settlement(dec)` in `solarstorm/data/_settlement.py` uses commercial rounding (half-up): `floor(dec + 0.5)`.
- `bracket_for(dec)` is the Polymarket bracket function -- equivalent to `integer_settlement(dec)`.
- `flip_risk(dec)` quantifies proximity to the 0.5 degree boundary where 0.1 degree flips the bracket:
  - Risk = 0.0: exactly on a .5 boundary (deterministic -- always rounds same way).
  - Risk = 0.5: exactly at an integer (maximum uncertainty -- 0.1 degree changes the bracket).
  - `risco_de_flip(tmax_dec)` in `solarstorm/data/_labels.py` computes the standardized metric.

The temperature parsed from METAR is validated against plausibility bounds: `TMP_C_INT_PLAUSIBILITY = (-10, 40)` in `_config.py`.

## Alternatives Considered

1. **Pure integer pipeline:** Convert everything to integers at ingest. Rejected -- loses sub-degree signal (dewpoint depression, warming rate) that P2 (evidence) values.
2. **Banker's rounding (half-to-even):** Round 14.5 to 14. Rejected -- Polymarket settlement rules follow commercial rounding conventions; half-up is the standard.
3. **Float output:** Output decimal probabilities and let the user round. Rejected -- P4 demands the forecaster own the settlement logic, not delegate it.

## Consequences

### Enabled
- Direct compliance with Polymarket settlement rules.
- `risco_de_flip` preserves bracket-boundary risk for future uncertainty-aware
  modeling. It does not authorize position sizing before the model gate passes.
- Auditable trace from METAR text to binary settlement outcome.

### Prevents
- Discrepancy between "what we predicted" and "what the market pays."
- Silent rounding errors from Fahrenheit-to-Celsius conversion (`tmpf` int rounding).
- Overconfidence at integer boundaries.

## References

- `solarstorm/data/_settlement.py` -- `integer_settlement()`, `bracket_for()`, `FlipRisk`, `flip_risk()`
- `solarstorm/data/_labels.py` -- `risco_de_flip()`
- `solarstorm/_config.py` -- `TMP_C_INT_PLAUSIBILITY`
- `solarstorm/data/_metar.py` -- `parse_tmp_c_int_from_row()` (ADR-007)
