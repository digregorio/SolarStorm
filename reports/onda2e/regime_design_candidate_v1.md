# Regime Design Candidate v1 - 2026-06-07

This is a formal regime-design proposal, not a production classifier.
Candidate v1 promotes `WCT-REGIME-016` only to ADR-012 regime-design review.

## Decision

- Candidate rows: 96
- Proposed k: 6 where the month/season sweep supports it.
- Required next gate: Onda 4 robustness plus final physical interpretation.

## Best K By Approximate BIC

| Stratum | best k | n rows | smallest cluster | BIC | silhouette | eta2 Tmax |
|---|---:|---:|---:|---:|---:|---:|
| month=1 | 6 | 1623 | 162 | 31076.1 | 0.181 | 0.270 |
| month=10 | 6 | 1595 | 159 | 29932.2 | 0.164 | 0.338 |
| month=11 | 6 | 1580 | 146 | 29781.5 | 0.186 | 0.313 |
| month=12 | 6 | 1705 | 187 | 33077.4 | 0.167 | 0.217 |
| month=2 | 6 | 1514 | 147 | 28276.3 | 0.179 | 0.365 |
| month=3 | 6 | 1727 | 176 | 33640.4 | 0.166 | 0.289 |
| month=4 | 6 | 1608 | 172 | 31327.3 | 0.163 | 0.360 |
| month=5 | 6 | 1695 | 204 | 32431.9 | 0.146 | 0.358 |
| month=6 | 6 | 1558 | 204 | 29711.0 | 0.157 | 0.269 |
| month=7 | 6 | 1535 | 146 | 29267.6 | 0.181 | 0.438 |
| month=8 | 6 | 1576 | 127 | 30475.8 | 0.187 | 0.398 |
| month=9 | 6 | 1544 | 139 | 29044.3 | 0.189 | 0.388 |
| season=DJF | 6 | 4842 | 487 | 93048.3 | 0.165 | 0.279 |
| season=JJA | 6 | 4669 | 480 | 90793.9 | 0.168 | 0.372 |
| season=MAM | 6 | 5030 | 614 | 97396.2 | 0.162 | 0.347 |
| season=SON | 6 | 4719 | 457 | 89005.2 | 0.166 | 0.351 |

## Annual Stability

- Matching annual best-k checks: 212/240 (88.3%).
- Mismatch checks requiring k=5 sensitivity review: 28.

## Physical Families

| Family | Clusters | Rows | Mean interpretability |
|---|---:|---:|---:|
| maritime_cloudy_candidate | 1 | 261 | 0.300 |
| mixed_or_transition | 6 | 1937 | 0.200 |
| nw_or_foehn_candidate | 56 | 25580 | 0.403 |
| southerly_disrupted_candidate | 33 | 10742 | 0.518 |

## Caveats

- BIC/AIC/SSE support k=6, but silhouette is not the promotion criterion.
- `mixed_or_transition` clusters require final interpretation.
- No production regime classifier changes until Onda 4 is rerun.