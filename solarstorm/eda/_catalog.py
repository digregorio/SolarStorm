"""Seed hypothesis catalog H1-H13 (P3). Each hypothesis becomes a gated EDA test.

Sources: Reestruturação_SolarStorm.txt, Wilson & Fovell 2018, model_error_taxonomy.md,
         auditoria forense items #8-#21, foehn literature.
"""
from __future__ import annotations

from solarstorm.eda._hypotheses import Hypothesis

SEED_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(id="H1", feature_column="slope_3h",
               description="Slope 3h (delta T/hour) improves remaining_warming forecast",
               source="Reestruturação Achado 13"),

    Hypothesis(id="H2", feature_column="hours_to_expected_peak",
               description="Expected peak hour (by month x regime) improves MAE at CP",
               source="Reestruturação Achado 13"),

    Hypothesis(id="H3", feature_column="regime_label",
               description="Causal physical regime separates forecast error significantly",
               source="model_error_taxonomy.md"),

    Hypothesis(id="H4", feature_column="dewpoint_depression",
               description="Dewpoint depression at CP carries signal for Tmax",
               source="Wilson & Fovell 2018"),

    Hypothesis(id="H5", feature_column="tmax_dminus1",
               description="T(D-1) adds predictive value beyond dminus1 pure",
               source="Auditoria #19"),

    Hypothesis(id="H6", feature_column="tmin_delta_tmax",
               description="Tmin of the day influences delta Tmax by regime x month",
               source="Auditoria #20"),

    Hypothesis(id="H7", feature_column="intraday_regime_change",
               description="Intraday day-state changes cause systematic error",
               source="Auditoria #14"),

    Hypothesis(id="H8", feature_column="wind_dir_change_s_to_n",
               description="Wind direction change S to N precedes late-Tmax timing risk",
               source="EDA projeto, foehn literature"),

    Hypothesis(id="H9", feature_column="day_sequence_pattern",
               description="Recent day-sequence patterns have predictive structure",
               source="Auditoria #16"),

    Hypothesis(id="H10", feature_column="precip_disruption",
               description="Rain/clearing/post-frontal recovery cause regime errors",
               source="Auditoria #11, #15"),

    Hypothesis(id="H11", feature_column="tmax_hour_by_regime_month",
               description="Tmax hour varies significantly by month x regime (P2)",
               source="Auditoria #12, #22"),

    Hypothesis(id="H12", feature_column="cloud_cover_suppression",
               description="Cloud cover reduces Tmax vs month x regime expectation",
               source="Auditoria #15"),

    Hypothesis(id="H13", feature_column="pressure_trend_3h",
               description="Pressure trend (3h) signals day-state change",
               source="Foehn literature, Reestruturação"),

    # H14-H16: structural refinements to the regime classifier, registered here
    # as gated hypotheses rather than baked into the heuristic, so they earn
    # their place via walk-forward effect size + CI (P3) instead of being tuned
    # on a handful of unit fixtures.
    Hypothesis(id="H14", feature_column="foehn_score",
               description="Composite foehn_score (NW-sector flow strength x dewpoint "
                           "depression) segments error better than a direction-only or "
                           "hard wind-speed cut",
               source="Regime classifier review 2026-06-04; eda_regime_path.py:262"),

    Hypothesis(id="H15", feature_column="late_warming_anomaly",
               description="Late-Tmax measured as delta T anomaly vs the hour's train-only "
                           "climatology ('surprise') beats absolute Tmax-hour timing for "
                           "segmenting late-Tmax error",
               source="Regime classifier review 2026-06-04; late_warming_bias_audit.md"),

    Hypothesis(id="H16", feature_column="regime_score_argmax",
               description="A continuous score-based regime classifier (argmax over "
                           "physical-regime scores) generalizes better across "
                           "seasons / ENSO phases than fixed boolean thresholds",
               source="Regime classifier review 2026-06-04"),

    # H17-H23: physical discriminators mined from the prior (overfitted) NZWN
    # protocols in 'Old Reports/'. Registered as gated hypotheses - NOT baked in.
    # The old team's fitted coefficients/offsets (e.g. Tmax = T09*1.15 + 4, per-
    # cluster offset tables) are deliberately excluded: their own backtests showed
    # 33-38% out-of-sample vs inflated in-sample claims. We keep only the falsifiable
    # PHYSICS and let walk-forward effect size + CI decide. Source mining synthesized
    # 2026-06-04 from NZWN_Postmortem_50Theses.md and the Protocol_14/15 series.
    Hypothesis(id="H17", feature_column="warming_rate_06_09",
               description="Pre-CP morning warming rate (T09-T06)/3 segments regime better "
                           "than wind direction: it integrates radiation + advection + "
                           "mixing into one causal scalar (>2 C/h => active dry/foehn engine)",
               source="Old Reports: Postmortem_50Theses IV-13; Protocol_14_0 C15/D02"),

    Hypothesis(id="H18", feature_column="nocturnal_plateau_flag",
               description="Peak-already-passed detector: flat morning (T07~=T08~=T09, range "
                           "<=0.5 C) with strong N flow + low cloud implies turbulent nocturnal "
                           "mixing put Tmax before the CP; the anchor is a ceiling not a launch",
               source="Old Reports: Protocol_15_1 (DPN); Postmortem_Apr16 section 6"),

    Hypothesis(id="H19", feature_column="sst_maritime_cap",
               description="For S/SE onshore regimes, recent Cook Strait SST + ~4 C is a "
                           "physical upper bound on Tmax (advected water-temp-limited air mass); "
                           "test as a soft cap feature, never a hard clamp",
               source="Old Reports: Protocol_15_0 section 1.3; Postmortem_50Theses II-14/IV-11"),

    Hypothesis(id="H20", feature_column="dewpoint_collapse_rate_3h",
               description="Absolute dewpoint DROP rate (dTd_3h), not the depression level, is "
                           "the cleaner foehn marker - captures dry continental subsidence "
                           "arriving; distinct from H4/H5 which measure a level not a rate",
               source="Old Reports: Postmortem_50Theses IV-12"),

    Hypothesis(id="H21", feature_column="prefrontal_warming_window",
               description="Falling QNH (3h) + no precip yet + N/NW flow opens a pre-frontal "
                           "window for a final 1-2 C before cloud/rain arrives; anecdotal in the "
                           "old docs so demand a strong CI before trusting",
               source="Old Reports: Protocol_14_0 C09/D10; Postmortem_Apr12_13 (WSP)"),

    Hypothesis(id="H22", feature_column="nw_sector_not_foehn",
               description="NW/W flow (280-310°) crossing cold Cook Strait dries WITHOUT warming "
                           "(adiabatic descent over water) - a false-positive foehn sector to "
                           "exclude; sharpens strong_nw_foehn vs the N/NNE warm sector",
               source="Old Reports: Postmortem_Apr16 section 3.5; Postmortem_50Theses II-07/IV-14/IV-15"),

    Hypothesis(id="H23", feature_column="cloud_base_transparency",
               description="Cloud suppression scales with base HEIGHT: BKN>=8000ft transmits most "
                           "April insolation while low cloud (<2500ft) suppresses; a flat cloud "
                           "penalty is wrong. Refines H12 with base-height dependence",
               source="Old Reports: Protocol_14_1 HCT-01; Postmortem_Apr12_13"),
]
