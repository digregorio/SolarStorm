# Regime Clustering Evidence - 2026-06-06

Source report: `research/regime_clustering_report.md`

Status: candidate evidence for Onda 2R, not a production model by itself.

## Reproducibility

- Station: NZWN.
- Period: 2009-2026 observations available in the current local dataset.
- Morning window: 00:00-08:00 local, preserving the causal firewall for morning CPs.
- Method: Gaussian Mixture Model candidate clustering with K=4.
- Script: `research/run_regime_transition_eda.py`
- Script SHA256: `6EE222A9AB241E7A016D32A97DDA1B1B32BA0317175D167D8E109EF2360`
- Source report SHA256: `F7E158F3E4FE195EECE84BA7B5A166BFABD4057174AE33B024D27E19201E`
- `data/obs.parquet` SHA256: `85595694DA48A89B1C6AF648DD7C9A60061C1A47979EE2344B41AE`
- `data/labels.parquet` SHA256: `BC19EBAFB2F4964B54FA3A70677B5E7AD7C435B6CA817B00525BC9`

## Candidate Finding

The EDA supports four causal physical regime families for Wellington:

- `southerly_disrupted`
- `standard_nw`
- `strong_nw_foehn`
- `calm_radiative`

The same EDA treats late Tmax / late warming as cross-cutting timing risk, not
as a causal regime. A fixed `18:00` rule is deprecated because normal Tmax
timing varies by month and physical regime.

## Limitations

- The clustering result is evidence, not the full production classifier.
- The current Onda 2R classifier is a deterministic causal heuristic derived
  from the physical interpretation and covered by regression tests.
- Late-Tmax thresholds used for future model features must be learned inside
  the walk-forward training window.
