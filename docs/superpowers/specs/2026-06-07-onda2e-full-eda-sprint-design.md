# Onda 2E Full EDA Sprint Design

Status: approved for implementation
Date: 2026-06-07

## Goal

Complete an evidence-producing Onda 2E EDA sprint that gives every thesis in
`reports/onda2e/thesis_atlas_v1.md` an individual review row, with special
depth on physical-regime architecture before any Onda 4 or Onda 3 progress.

## Scope

The sprint must produce reproducible artifacts, not only narrative notes. It
must cover all 251 theses, preserve honest blockers for missing data or missing
registry detail, and avoid promoting any feature, model, or production regime by
intuition.

The regime architecture EDA is the first-class focus:

- build a causal pre-CP clustering matrix;
- exclude outcomes, current regime labels, and train-prior outcome summaries;
- run k-selection by month and season for `k=2..6`;
- evaluate silhouette, AIC/BIC approximation, cluster power, external Tmax
  anomaly separation, and interpretability;
- compare resulting clusters against the quarantined current regime family.

## Required Artifacts

- `reports/onda2e/full_thesis_review.csv`
- `reports/onda2e/onda2e_full_eda_report.md`
- `reports/onda2e/regime_cluster_input_manifest.csv`
- `reports/onda2e/regime_cluster_sweep_by_month_season.csv`
- `reports/onda2e/regime_cluster_profiles.csv`
- `reports/onda2e/regime_cluster_outcome_audit.csv`
- `reports/onda2e/regime_cluster_leakage_audit.csv`
- `reports/onda2e/regime_architecture_sprint_report.md`

## Decision Policy

Every thesis must receive an individual review status. A review row may conclude
that the correct decision is still blocked because of external data, missing
registry detail, insufficient power, or lack of domain EDA. Blocking is an
honest result, not a failure.

Only artifact-backed findings can update ADR-012 decision rows. Any regime
architecture finding must enter `regime_design_queue.csv` before it can affect
Onda 4 repair. `feature_candidate_queue.csv` remains empty unless a thesis has
causal availability, power, leakage review, and a direct implementation path.

## Non-Scope

- Onda 3 model training.
- Production regime classifier replacement.
- Polymarket, EV, position sizing, shadow trading, live execution.
- Using `tmax_int`, `tmax_hour`, `remaining_warming`, `tmax_anomaly`, current
  `regime_label`, or `regime_flags` as clustering inputs.

