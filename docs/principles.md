# SolarStorm Design Principles (P1-P6)

These principles govern every design decision. They are ranked by priority:
P1 is the hardest constraint and failures cascade downward. SolarStorm is a
data-first climatology project before it is a modeling project; rules, regimes,
features, and models must earn their place through evidence.

## P1: Causal Firewall

> **No future information leaks into any forecast.**

- Every feature at a checkpoint `cp_utc` must satisfy `feature_max_ts < cp_utc` (strict inequality). The observation timestamp of the latest input must be strictly before the checkpoint.
- Violation raises `RuntimeError` -- no silent fallback, no diagnostic downgrade.
- Internal computation uses **decimal** temperatures (`tmax_dec` from `tmpf`); the integer bracket is derived only at the output layer.
- Source: `solarstorm/_contracts.py` (`require_causal()`), `solarstorm/data/_labels.py` (`risco_de_flip()`).

**Why it is P1:** A forecast is worthless if it peeks at the answer. No other gate matters if causality is broken.

## P2: Evidence Over Parameters

> **No hardcoded meteorological constants except contractual CP_SET.**

- All thresholds, regimes, and climatological parameters must be data-driven, computed from the training set only.
- The sole exception: `CP_SET_UTC` (checkpoint hours) and `ICAO`/`TZ_NAME` are contractual constants defined in `_config.py`.
- Regime thresholds (`foehn_score > 60.0`, `max_delta > 1.0`, etc.) may exist
  only as candidate tests or quarantined baselines until ADR-012 decision
  records explicitly retain, adapt, reject, or replace them.
- Old Reports' fitted constants (e.g., "Tmax = T09 * 1.15 + 4") are deliberately excluded -- their backtests showed 33-38% out-of-sample vs inflated in-sample.

**Why it is P2:** The old Wellington project died from overfitted constants. If it cannot be derived from data, it does not go in.

## P3: Hypotheses Must Be Testable

> **Every EDA finding is registered as a gated hypothesis with bootstrap CI + FDR.**

- Each hypothesis gets a unique H-ID, a feature column, and a physical justification (source field).
- Validation is via the walk-forward harness: expanding-window splits, paired bootstrap CI (n=1000), Benjamini-Hochberg FDR correction at alpha=0.05.
- A hypothesis passes only if CI95 excludes zero, FDR survives, AND all five gates (G1-G5) pass.
- Failed hypotheses are documented with the same rigor as passed ones (P5).
- H17-H23 were mined from the old overfitted protocols but registered as gated tests -- they must earn their place, not inherit it.

**Why it is P3:** If you cannot test it, you cannot trust it. The old project's 50 theses were never falsified -- they were baked in.

## P4: Settlement Honesty

> **Decimal internally, integer output. Commercial rounding (half-up).**

- `integer_settlement(dec)` uses commercial rounding: `floor(dec + 0.5)`. 14.5 rounds to 15; -2.5 rounds to -2.
- `risco_de_flip` quantifies how close a decimal value is to a 0.5 degree boundary where 0.1 degree flips the Polymarket bracket.
  - 0.0 = exactly on a .5 boundary (no risk -- always rounds the same way).
  - 0.5 = exactly at an integer (max risk -- 0.1 degree changes the bracket).
- Source: `solarstorm/data/_settlement.py` (`FlipRisk`, `flip_risk()`).

**Why it is P4:** Polymarket contracts settle on integer degrees. How close we are to the boundary determines whether the forecast has practical edge or is noise.

## P5: Versioned Artifacts

> **All outputs timestamped, reproducible, JSON+MD format.**

- Every CLI command that produces output writes a versioned artifact to `reports/` (e.g., `reports/2026-06-05/hypothesis_results.json`).
- Stdout is an echo, not the authoritative record. The artifact is the truth.
- Leaderboard is a **permanent scoreboard** -- each run appends a dated entry, never overwrites.
- Reproducibility is anchored by `SEED = 42` in `_config.py`.
- Formats: JSON for machine consumption, Markdown for human review.

**Why it is P5:** The old project's results were scattered across notebooks and Slack threads. Versioned artifacts make the evaluation trail auditable and the leaderboard a living document.

## P6: Evidence Must Become Decisions

> **EDA that does not feed a traceable decision cannot guide the project.**

- Every Onda 2E thesis, regime rule, cooling rule, timing rule, and candidate
  feature must end in a registered decision: `SUPPORTED`, `REJECTED`,
  `ADAPTED`, `BLOCKED`, `PROMOTED_TO_REGIME_DESIGN`,
  `PROMOTED_TO_FEATURE_CANDIDATE`, or `QUARANTINED_BASELINE`.
- A decision must cite the artifact that supports it, the strata tested
  (month/CP/regime when applicable), sample-size warnings, causal availability,
  and leakage risk.
- EDA tables are not enough. A CSV in `reports/` is descriptive evidence, not
  permission to change regimes, features, gates, or models.
- Existing hardcoded or heuristic rules are quarantined baselines until this
  gate explicitly retains, adapts, rejects, or replaces them.
- Rejected ideas must not return under new names unless new evidence is added.

**Why it is P6:** The project has repeatedly drifted from evidence into
plausible-sounding rules. The 251-thesis atlas must change project decisions,
not become an archive.

## Cascade

These principles cascade: if P1 (causality) is violated, P3 (hypothesis
testing) is meaningless. If P2 (evidence) is violated, P4 (settlement honesty)
becomes a lie about precision. P5 (versioning) makes all others auditable. P6
prevents evidence from being ignored after it is produced.

## Source

Extracted from the codebase on 2026-06-04 and updated on 2026-06-07 after Onda
2E exposed the need for a formal Evidence-to-Decision Gate.
