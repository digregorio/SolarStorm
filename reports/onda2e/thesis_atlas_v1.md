# Wellington Climatology Thesis Atlas — Onda 2E
**Version:** 1.0-draft  
**Date:** 2026-06-06  
**Station:** NZWN (Wellington Airport)  
**Period:** 2009–2026  
**Status:** E0_candidate (all theses)

---

## Conventions

| Field | Rule |
|---|---|
| **id** | `WCT-DOMAIN-NNN` |
| **strata** | Always includes `month` (1–12) and `regime` (one of the four physical labels or `all`). Never stratified by final outcome. |
| **causal_availability** | States what is visible at each of CP20/CP21/CP22/CP23 (local morning cutoffs ~20:00–23:00 previous calendar day). Full-day outcomes are targets only. |
| **late_tmax threshold** | Never fixed at 17:00. Always `q90_train(tmax_hour \| month, regime)` computed train-only inside walk-forward loop. |
| **status** | All theses start at `E0_candidate`. Evidence level upgrades (E1→E2) require descriptive tables/plots (E1) plus causal availability verification (E2). |

### Domain codes
`REGIME` · `COOLING` · `WIND` · `FOEHN` · `RAIN` · `CLOUD` · `PRES` · `HUM` · `TIMING` · `SPIKE` · `CP` · `DQ` · `IX` · `GAP`

---

## Quick-Reference Registry

| ID | Domain | Claim (short) | Key strata | Status |
|---|---|---|---|---|
| WCT-REGIME-001 | REGIME | Cooling rule (−2 C/h) captures radiative pre-dawn events, not only frontal disruption | month, CP hour | E0_candidate |
| WCT-REGIME-002 | REGIME | southerly_disrupted frequency is highest in winter (Jun–Aug), not uniform | month | E0_candidate |
| WCT-REGIME-003 | REGIME | calm_radiative is chronically underpowered because cooling rule steals clear-sky radiative nights | month, cooling trigger hour | E0_candidate |
| WCT-REGIME-004 | REGIME | The NW sector 270–45° contains three meteorologically distinct sub-sectors | month, sub-sector | E0_candidate |
| WCT-REGIME-005 | REGIME | Daily regime transitions follow non-random Markov sequences by month | month, D-1 regime | E0_candidate |
| WCT-REGIME-006 | REGIME | foehn_score threshold 60 is not calibrated by month | month | E0_candidate |
| WCT-REGIME-007 | REGIME | standard_nw is underpowered because the cooling rule steals ≈8 570 rows from it | cooling trigger audit | E0_candidate |
| WCT-REGIME-008 | REGIME | Regime classification stability (no further change with extra obs) arrives earlier in summer than in winter | month, CP lead | E0_candidate |
| WCT-REGIME-009 | REGIME | Regime border cases (foehn_score near 60, nw_share near 0.4) have systematically weaker effect sizes | regime margin, month | E0_candidate |
| WCT-REGIME-010 | REGIME | Wind direction natural cluster boundaries in METAR may differ from the prescribed sector cutoffs | month, direction distribution | E0_candidate |
| WCT-REGIME-011 | REGIME | The pre-dawn cooling trigger in the classifier conflates radiative cooling (physical, normal) with frontal cooling (synoptic disruption) | cooling hour, month | E0_candidate |
| WCT-REGIME-012 | REGIME | strong_nw_foehn is heavily concentrated in spring–summer; its q90 timing thresholds differ from annual averages | month | E0_candidate |
| WCT-REGIME-013 | REGIME | D-1 regime state predicts D-0 regime assignment probabilities beyond a naive DOY prior | month, D-1 regime | E0_candidate |
| WCT-REGIME-014 | REGIME | Foehn events cluster in multi-day sequences; regime persistence is higher for strong_nw_foehn than for calm_radiative | consecutive day count, month | E0_candidate |
| WCT-REGIME-015 | REGIME | southerly_disrupted → calm_radiative transition (post-frontal clear) produces systematically higher next-day Tmax | month, transition type | E0_candidate |
| WCT-REGIME-016 | REGIME | A data-driven K-selection test should validate K=4 vs K=3 and K=5 for Wellington clustering | month, feature set | E0_candidate |
| WCT-REGIME-017 | REGIME | Calm/light wind in the morning window with variable direction should not default to calm_radiative | wind speed threshold, month | E0_candidate |
| WCT-REGIME-018 | REGIME | Regime classification errors (high foehn_score yet classified southerly due to cooling rule) form a systematic error class | foehn_score bin, month | E0_candidate |
| WCT-REGIME-019 | REGIME | Monthly regime prior probabilities by CP must be documented before any per-regime per-month thesis is testable | month, CP | E0_candidate |
| WCT-REGIME-020 | REGIME | southerly_disrupted needs a 4-way sub-typology: (A) radiative capture, (B) deep frontal southerly, (C) shallow southerly, (D) post-frontal partial recovery | trigger type, month | E0_candidate |
| WCT-COOL-001 | COOLING | Cooling rate peak hour (before 06:00 = radiative; after 09:00 = frontal) is a better disruption discriminator than magnitude alone | month, CP window | E0_candidate |
| WCT-COOL-002 | COOLING | By month, the -2 C/h threshold fires more often on non-disrupted winter mornings because of longer and colder radiative nights | month, hour of min-delta | E0_candidate |
| WCT-COOL-003 | COOLING | Frontal cooling shows rapid wind-direction shift + fast temperature drop; radiative cooling is gradual with light/variable wind | wind speed, direction delta, month | E0_candidate |
| WCT-COOL-004 | COOLING | Dewpoint rises during maritime southerly cooling (warmer SST air replacing), distinguishing it from foehn collapse cooling | dewpoint trend, wind sector, month | E0_candidate |
| WCT-COOL-005 | COOLING | Continuous cooling duration (hours) visible by CP predicts Tmax suppression depth better than the minimum cooling rate | hours of cooling, month, regime | E0_candidate |
| WCT-COOL-006 | COOLING | High-speed cooling (>20 kt southerly) predicts sustained Tmax suppression; light-wind cooling is more likely radiative and transient | wind speed during cooling, month | E0_candidate |
| WCT-COOL-007 | COOLING | Post-frontal recovery is a distinct sub-class within southerly_disrupted; these days may achieve Tmax near climatology despite morning cooling | hours since frontal passage, month | E0_candidate |
| WCT-COOL-008 | COOLING | In summer, even 3–4 C of frontal morning cooling still leaves more remaining warming potential than in winter because of greater solar input | month, remaining warming delta | E0_candidate |
| WCT-COOL-009 | COOLING | Cooling events arriving after 09:00 (post-dawn, after warming has started) suppress Tmax more severely than pre-dawn cooling | cooling hour, month, regime | E0_candidate |
| WCT-COOL-010 | COOLING | Temperature at CP relative to the month's climatological temperature at that hour outperforms absolute cooling rate as a regime diagnostic | month, CP, T_anomaly | E0_candidate |
| WCT-COOL-011 | COOLING | The southerly_disrupted label needs to separate cooling due to latent heat (rain evaporation) from dry frontal cooling | precipitation flag, month | E0_candidate |
| WCT-COOL-012 | COOLING | Maritime cooling (S/SE, dewpoint rises) and radiative cooling (calm, dewpoint steady) produce qualitatively different temperature profile shapes distinguishable from METAR data | wind sector, dewpoint trend, month | E0_candidate |
| WCT-COOL-013 | COOLING | Consecutive cooling days (D-2 cold, D-1 cold, D-0) predict more sustained Tmax suppression than isolated single-day disruptions | consecutive count, month, regime | E0_candidate |
| WCT-COOL-014 | COOLING | Minimum temperature by CP is a better cooling severity proxy than minimum cooling rate: it integrates depth and duration of cold | month, regime, CP | E0_candidate |
| WCT-COOL-015 | COOLING | Post-frontal radiative cooling (after southerly, skies clear, wind drops) is a warming signal for the next day, not a suppression signal for the current day | next-day regime, month | E0_candidate |
| WCT-COOL-016 | COOLING | The relationship between cooling rate and final Tmax is non-monotonic: moderate cooling with post-noon clearing can yield higher Tmax than no cooling (post-frontal clearing effect) | clearing time, month | E0_candidate |
| WCT-COOL-017 | COOLING | Hours since last cooling event predicts recovery rate; 36 h of southerly leaves more residual suppression than 12 h | hours since disruption, month | E0_candidate |
| WCT-COOL-018 | COOLING | By wind sector, cooling rate within 135–225° differs between 180–210° (pure south, cold) and 135–160° (SE, moist maritime) | sub-sector, month | E0_candidate |
| WCT-COOL-019 | COOLING | Temperature inversion strength at dawn (inferred from near-surface dewpoint vs temperature spread) predicts how long before surface heating overcomes the cap | month, regime | E0_candidate |
| WCT-COOL-020 | COOLING | The diurnal temperature range (DTR) by month and regime is a distributional anchor: constrained DTR is not always southerly disrupted — maritime stable days also have low DTR | month, regime, DTR | E0_candidate |
| WCT-WIND-001 | WIND | The heating-per-knot relationship in the N/NNE (330–045°) warm sector differs from W/NW (260–310°) cold Cook Strait sector, by month | sub-sector, speed bin, month | E0_candidate |
| WCT-WIND-002 | WIND | Wind direction persistence (% obs in same ±30° sector) correlates with Tmax outcome more than instantaneous direction | persistence metric, month, regime | E0_candidate |
| WCT-WIND-003 | WIND | Wind speed shows a non-linear relationship with Tmax on northerly/foehn days: 15–30 kt = peak heating sweet spot; above 35 kt = mechanical mixing limits peak | speed bin, month | E0_candidate |
| WCT-WIND-004 | WIND | The summer afternoon sea breeze (SSW-S shift after ~14:00) acts as a natural Tmax limiter; its onset timing varies by month and synoptic strength | sea breeze onset hour, month | E0_candidate |
| WCT-WIND-005 | WIND | Clockwise wind rotation during morning (veering: N→E→S = frontal approach) vs anticlockwise (backing: S→W→N = recovery) predicts whether a NW event is developing or decaying | rotation direction, month | E0_candidate |
| WCT-WIND-006 | WIND | Monthly wind rose by sector for NZWN must be documented as the prior distribution for all wind sector theses | month | E0_candidate |
| WCT-WIND-007 | WIND | NE wind (045–090°) imports maritime moisture from Cook Strait entrance, suppressing Tmax differently from N/NW foehn or S maritime flow | NE sector flag, month | E0_candidate |
| WCT-WIND-008 | WIND | Wind steadiness (gust-to-mean ratio or direction IQR) predicts whether the morning state persists through the afternoon | steadiness metric, month, regime | E0_candidate |
| WCT-WIND-009 | WIND | Wind direction observations when speed < 5 kt are unreliable; filtering calm observations changes sector share on a non-trivial fraction of days | calm threshold, month | E0_candidate |
| WCT-WIND-010 | WIND | The effective foehn sector for Wellington is concentrated in 340–030° (N–NNE) based on topography; the current 270–45° arc may be 40–60° too wide | sub-sector, month | E0_candidate |
| WCT-WIND-011 | WIND | Wind from W (260–280°) crossing Cook Strait may produce cooling or neutral effect rather than foehn warming due to cold water crossing | W sector, Tmax anomaly, month | E0_candidate |
| WCT-WIND-012 | WIND | Wind speed acceleration direction during the morning window (strengthening vs weakening by CP) predicts whether the afternoon state will be stronger than the morning state | speed trend, month, regime | E0_candidate |
| WCT-WIND-013 | WIND | SE/E winds (090–160°) suppress Tmax without triggering southerly_disrupted as coded; these days are likely misclassified | SE flag, Tmax anomaly, month | E0_candidate |
| WCT-WIND-014 | WIND | Wind vector components (u, v) as continuous predictors outperform discrete sector classification in ML models | month, CP | E0_candidate |
| WCT-WIND-015 | WIND | After southerly passage, recovery direction (N via anticlockwise through W) produces different warming trajectory than direct NW recovery | recovery path, month | E0_candidate |
| WCT-WIND-016 | WIND | Wind direction at NZWN is locally amplified by Cook Strait channel; the airport speed may overrepresent the regional NW at certain channel-aligned directions | direction, speed, month | E0_candidate |
| WCT-WIND-017 | WIND | By month, the NW/N wind speed that produces maximum positive Tmax anomaly (sweet spot) shifts; summer may have a higher sweet-spot speed than winter | month, speed-Tmax curve | E0_candidate |
| WCT-WIND-018 | WIND | Northerly gust factor (max/mean speed) correlates with foehn intensity and timing of peak Tmax: gustier foehn peaks earlier and drops more sharply | gust factor, month, regime | E0_candidate |
| WCT-WIND-019 | WIND | The number of southerly-sector hourly obs by CP (0–8) predicts remaining cooling potential better than southerly share alone | southerly obs count, CP, month | E0_candidate |
| WCT-WIND-020 | WIND | Wind from 030–090° (NE to E) suppresses Tmax by importing moist Pacific marine air; this sector is untested as a cool/neutral sector | NE-E sector, month | E0_candidate |
| WCT-FOEHN-001 | FOEHN | foehn_score (NW-speed × dewpoint-depression) is driven by either high speed or high depression; these two pathways have different Tmax magnitudes and timing | foehn pathway type, month | E0_candidate |
| WCT-FOEHN-002 | FOEHN | The dewpoint collapse RATE (H20 validated) captures foehn onset timing better than the depression level; rapid collapse (>2 C/h) at 06:00–09:00 is the strongest warming signal | collapse rate, onset hour, month | E0_candidate |
| WCT-FOEHN-003 | FOEHN | Foehn collapse timing in the afternoon (NW weakens → temperature drops) determines final Tmax; days with late foehn collapse are the primary late-spike days in spring-summer | collapse hour, month, regime | E0_candidate |
| WCT-FOEHN-004 | FOEHN | By month, the foehn score threshold that separates days with Tmax anomaly > +3 C must be calibrated from data, not fixed at 60 | month, foehn_score bins | E0_candidate |
| WCT-FOEHN-005 | FOEHN | Multi-day foehn sequences show progressive drying and warming; day 2 and day 3 of a foehn event have different Tmax distributions than day 1 | consecutive foehn days, month | E0_candidate |
| WCT-FOEHN-006 | FOEHN | Pre-foehn cloud burn-off (cloud at CP20-21, clearing by CP23 with dewpoint falling) is a validated foehn development signal before full foehn score is reached | cloud trend, dewpoint trend, CP | E0_candidate |
| WCT-FOEHN-007 | FOEHN | Foehn events with precipitation (pre-frontal rain while NW still present) are currently captured as southerly_disrupted; their Tmax distribution is bimodal (warming vs suppressed) | precip flag + NW flag, month | E0_candidate |
| WCT-FOEHN-008 | FOEHN | Wind backing from N to NW to W during morning signals foehn weakening; direction of backing predicts whether the foehn will sustain through the afternoon | backing/veering, morning hours, month | E0_candidate |
| WCT-FOEHN-009 | FOEHN | The NW/W sector (280–310°) crossing cold Cook Strait produces false foehn: dewpoint drops from adiabatic descent but temperature does not rise above maritime baseline | sector, Tmax anomaly, month | E0_candidate |
| WCT-FOEHN-010 | FOEHN | Summer foehn adds to already-high solar heating (superadditive); winter foehn is the dominant warmth source. The same foehn_score produces different Tmax anomalies by month | month, foehn_score, Tmax anomaly | E0_candidate |
| WCT-FOEHN-011 | FOEHN | Strong foehn events suppress cloud formation via subsidence; the cloud_cover_suppression signal on foehn days has a physically different mechanism than cloud suppression on calm radiative days | regime, cloud signal, month | E0_candidate |
| WCT-FOEHN-012 | FOEHN | The dewpoint depression at CP predicts remaining warming potential differently on foehn vs non-foehn days; the interaction (depression × foehn regime) is stronger than either alone | regime, dewpoint depression, month | E0_candidate |
| WCT-FOEHN-013 | FOEHN | Foehn events are more reliably identifiable at CP23 than CP20 because dewpoint collapse onset typically occurs between 21:00 and 23:00 | CP, dewpoint collapse, month | E0_candidate |
| WCT-FOEHN-014 | FOEHN | The altitude of descending foehn air (proxy: QNH level above seasonal mean) determines adiabatic warming contribution; higher-than-normal QNH amplifies foehn heating | QNH anomaly, month | E0_candidate |
| WCT-FOEHN-015 | FOEHN | After foehn ends, dewpoint recovery rate (rising back toward maritime levels) predicts how quickly foehn warming dissipates by evening | recovery rate, foehn end hour, month | E0_candidate |
| WCT-RAIN-001 | RAIN | Rain timing matters: rain only before 06:00 suppresses Tmax less than rain falling 08:00–12:00 which directly blocks solar heating | rain timing window, month | E0_candidate |
| WCT-RAIN-002 | RAIN | Post-rain clearing rate (cloud cover decreasing after rain ends) predicts whether a late spike is achievable; faster clearing = later and higher Tmax | clearing rate, clearing start hour, month | E0_candidate |
| WCT-RAIN-003 | RAIN | D-1 rainfall affects D-0 Tmax via soil moisture and evapotranspiration; wet soil increases latent heat flux and suppresses Tmax | D-1 precip, month, regime | E0_candidate |
| WCT-RAIN-004 | RAIN | Light precipitation (p01i < 0.5 mm/h) with NW wind is likely orographic drizzle, not frontal rain; these days should not trigger southerly_disrupted | precip intensity, wind sector, month | E0_candidate |
| WCT-RAIN-005 | RAIN | The combination rain + NW (pre-frontal rain, NW still present) vs rain + southerly (post-frontal rain) have different Tmax predictions; current classifier conflates them | wind sector during rain, month | E0_candidate |
| WCT-RAIN-006 | RAIN | Summer rain events recover faster post-clearing than winter (stronger solar angle after clearing); the rain-Tmax suppression slope differs by month | month, clearing lag | E0_candidate |
| WCT-RAIN-007 | RAIN | Heavy morning rain + rapid clearing (southerly front passing quickly) generates the steepest post-clearing temperature rise; post-clearing rate is a late-spike predictor | clearing duration, rain intensity, month | E0_candidate |
| WCT-RAIN-008 | RAIN | Cumulative 3-day precipitation (D-2 + D-1 + D-0 morning) as a soil moisture proxy predicts Tmax suppression; effect is largest in summer when evapotranspiration is highest | 3-day cumulative, month | E0_candidate |
| WCT-RAIN-009 | RAIN | The post-frontal "clearing window" — rapid temperature rise after southerly passage — has a month-dependent duration and starting time that can be learned from historical data | month, frontal passage hour | E0_candidate |
| WCT-RAIN-010 | RAIN | Rain days that become warm and sunny by 14:00 are systematically underforecast; morning rain dominates model prediction without accounting for post-clearing dynamics | clearing time bin, month | E0_candidate |
| WCT-RAIN-011 | RAIN | Northern orographic rain (NW flow with drizzle on Tararua NE slopes) is a specific Wellington pattern where airport Tmax can be high despite recorded light precipitation | precip type proxy, wind sector, month | E0_candidate |
| WCT-RAIN-012 | RAIN | Sequential rain events (D-2 and D-1 both wet, then D-0 dry) produce stronger soil moisture suppression than isolated single-day rain | rain sequence, month | E0_candidate |
| WCT-RAIN-013 | RAIN | The probability of post-frontal clearing is historically quantifiable by month and frontal speed proxy (pressure rise rate); this prior is the fallback when NWP data is unavailable | pressure rise rate, month | E0_candidate |
| WCT-RAIN-014 | RAIN | Thermal recovery after clearing (temperature rising >2 C/h after cloud lifts) is a late-Tmax precursor detectable intraday; its historical frequency and magnitude vary by month | recovery rate threshold, month | E0_candidate |
| WCT-RAIN-015 | RAIN | By season, the fraction of rain days that achieve above-climatology Tmax (post-clearing overshoot) varies; spring may have the highest rate of post-clearing recovery | month, post-clearing Tmax anomaly | E0_candidate |
| WCT-CLOUD-001 | CLOUD | METAR sky condition (cloud_cover_suppression, H12 validated) requires stratification by base height; the suppression effect of OVC002 vs OVC100 differs by an order of magnitude | cloud base height, month, regime | E0_candidate |
| WCT-CLOUD-002 | CLOUD | By month, the typical cloud base height at Wellington differs; winter stratus tends lower (300–600 m), summer cloud higher (1000–2000 m) or convective | month, cloud base distribution | E0_candidate |
| WCT-CLOUD-003 | CLOUD | Morning cloud that burns off by 11:00 has a different Tmax impact than cloud that builds in the afternoon; cloud trajectory matters more than cloud state at CP | cloud trend direction, clearing time, month | E0_candidate |
| WCT-CLOUD-004 | CLOUD | H23 (cloud_base_transparency, validated) needs month-stratified re-test; the base-height effect on transparency may be larger in spring (high solar angle) than in winter | month, cloud base | E0_candidate |
| WCT-CLOUD-005 | CLOUD | Fog and very low stratus (<300 m) in Wellington mornings suppresses early warming severely but often burns off by 10:00 on NW days; its post-burn-off warming rate is a late-Tmax signal | fog flag, NW wind, month | E0_candidate |
| WCT-CLOUD-006 | CLOUD | Stratocumulus from the south (SCT/BKN at 1000–3000 ft) has base height encoding air mass stability; lower base = moister/more stable = more sustained suppression | base height, wind sector, month | E0_candidate |
| WCT-CLOUD-007 | CLOUD | High cloud only (FEW/SCT above 10 000 ft) does not significantly suppress Tmax in summer; the same cloud at low solar angle in winter may reduce Tmax by 0.5–1 C | month, cloud base height | E0_candidate |
| WCT-CLOUD-008 | CLOUD | On clear-sky (SKC/FEW > 20 000 ft) days, Tmax variance is explained by wind sector and regime, not by cloud; cloud suppression feature should be disabled for clear-sky days | clear flag, regime, month | E0_candidate |
| WCT-CLOUD-009 | CLOUD | Mixed cloud days (cloud at CP, clear by afternoon) generate late Tmax by thermodynamic delay; the delay magnitude scales with how long before noon the clearing occurs | clearing time relative to solar noon, month | E0_candidate |
| WCT-CLOUD-010 | CLOUD | Cloud cover at CP does not predict cloud cover at Tmax hour; historical cloud persistence rates by month/regime pair are needed as a prior for models | month, regime, cloud persistence rate | E0_candidate |
| WCT-CLOUD-011 | CLOUD | Wellington orographic cloud (Tararua range shielding) creates cases where airport METAR shows partial cloud while the synoptic pattern is NW foehn; these days are foehn mislabeled as partial cloud | NW flow + partial cloud, month | E0_candidate |
| WCT-CLOUD-012 | CLOUD | Multi-layer cloud reports (2+ distinct layers) produce more persistent suppression than single-layer thin cloud | layer count, month | E0_candidate |
| WCT-CLOUD-013 | CLOUD | Cloud base height trend during morning (rising = improving, falling = deteriorating) predicts afternoon cloud status better than the absolute base height at CP | cloud base trend, month, regime | E0_candidate |
| WCT-CLOUD-014 | CLOUD | By season, summer afternoon convective cloud (building from 13:00–16:00) can interrupt clear-looking days at CP; this convective risk is month-dependent and unpredictable from morning obs alone | month, convective flag | E0_candidate |
| WCT-CLOUD-015 | CLOUD | Cumulonimbus observations are rare at Wellington but indicate convective instability; CB days have high but constrained Tmax (convective release before Tmax can grow further) | CB flag, month | E0_candidate |
| WCT-PRES-001 | PRES | H13 (pressure_trend_3h) was rejected across all CPs; the diurnal pressure tide (±1–2 hPa, peaks 10:00 and 22:00) likely contaminates 3h trends; tide-corrected trends should be tested | tide-corrected trend, month | E0_candidate |
| WCT-PRES-002 | PRES | Absolute QNH level (not trend) encodes air mass type; high QNH (>1025 hPa) predicts stable anticyclonic; low QNH (<1005 hPa) predicts unsettled; the absolute level carries signal lost in the difference | QNH level, month, regime | E0_candidate |
| WCT-PRES-003 | PRES | Pressure rise rate after frontal passage discriminates deep troughs (slow rise = more cloud/suppression) from shallow fronts (fast rise = quick clearing) | pressure rise rate, month | E0_candidate |
| WCT-PRES-004 | PRES | The QNH anomaly (QNH minus month-regime mean) is more informative than absolute QNH because the seasonal baseline dominates the absolute level | month, regime, QNH anomaly | E0_candidate |
| WCT-PRES-005 | PRES | A combined feature QNH > 1020 AND pressure stable (|trend| < 0.5 hPa/h) predicts calm radiative or settled NW conditions; the conditional may rescue what the linear pressure trend lost | compound condition, month | E0_candidate |
| WCT-PRES-006 | PRES | By regime, the pressure profile differs: foehn events show pre-frontal pressure maximum then rapid drop; southerly shows rapid rise post-frontal; calm radiative shows slow diurnal-only variation | regime, pressure profile shape | E0_candidate |
| WCT-PRES-007 | PRES | The pre-frontal pressure drop (H21 rejected as coded) may perform better over a 6-hour window than a 3-hour window because the pre-frontal stage lasts 4–8 hours | trend window length, month | E0_candidate |
| WCT-PRES-008 | PRES | Pressure gradient across Cook Strait (proxy: difference in QNH tendency between NZWN and synoptic neighbors) drives the northerly jet strength; this blocked thesis requires additional station data | BLOCKED — requires 2nd station | E0_candidate |
| WCT-PRES-009 | PRES | Very high pressure (QNH above the seasonal 90th percentile) predicts calm radiative conditions but NOT necessarily high Tmax in winter; solar input is the binding constraint after stability is secured | month, QNH percentile | E0_candidate |
| WCT-PRES-010 | PRES | Post-frontal pressure stabilization rate (how fast QNH rises and levels) predicts the timing of clearing and the likelihood of late Tmax recovery | stabilization rate, month | E0_candidate |
| WCT-PRES-011 | PRES | Pressure level × wind sector interaction: QNH rising + NW = post-frontal clearing onset; QNH falling + NW = pre-frontal foehn; same wind, opposite pressure meaning | QNH trend sign, wind sector, month | E0_candidate |
| WCT-PRES-012 | PRES | Longer-window pressure change (12-hour delta from the previous evening to CP) is a better synoptic-pattern discriminator than 3-hour trend because it captures the full frontal signature | 12h delta, month, regime | E0_candidate |
| WCT-HUM-001 | HUM | Dewpoint anomaly (dewpoint minus month-regime mean dewpoint) is more informative than absolute dewpoint depression because the seasonal moisture baseline dominates the absolute level | month, regime, Td anomaly | E0_candidate |
| WCT-HUM-002 | HUM | Maritime air mass cap: when air is of maritime origin (high dewpoint, moderate temperature), Tmax is physically capped near estimated SST + seasonal offset; lower in winter (colder SST) | month, wind sector, dewpoint level | E0_candidate |
| WCT-HUM-003 | HUM | High RH + low temperature (saturated cold air = maritime flow) vs high RH + moderate temperature (fog before burn-off) carry different Tmax implications despite identical RH | RH, T, wind sector, month | E0_candidate |
| WCT-HUM-004 | HUM | Drying during the morning CP window (dewpoint decreasing over the observation window) is a foehn development signal distinct from the dewpoint collapse rate feature (H20); the direction (drying vs moistening) is the key boolean | dewpoint trend sign, month, CP | E0_candidate |
| WCT-HUM-005 | HUM | NW wind + high dewpoint is a contradiction flag (genuine foehn dries air); this combination may indicate shallow NW over a moist layer or moisture-laden NW, not true foehn | NW + high Td flag, month | E0_candidate |
| WCT-HUM-006 | HUM | Overnight near-saturation (temperature approaches dewpoint before dawn = fog/dew) delays morning warming; fog must lift before surface heating begins, causing late warm start | saturation flag, month, regime | E0_candidate |
| WCT-HUM-007 | HUM | Dewpoint depression rate of decline on foehn days correlates with foehn intensity better than the absolute depression because initial dewpoint varies by season and synoptic setup | rate of Td decline, month | E0_candidate |
| WCT-HUM-008 | HUM | Moist southerly vs dry southerly (both S wind, different dewpoints) predict different Tmax levels; a moist southerly is capped near SST, a dry southerly from further south is colder but less SST-limited | southerly Td level, month | E0_candidate |
| WCT-HUM-009 | HUM | Humidity trend direction during morning CP (rising Td = maritime air arriving; falling Td = foehn developing) is a binary signal with strong physical backing that has not been tested independently | Td trend direction, month, CP | E0_candidate |
| WCT-HUM-010 | HUM | The monthly mean dewpoint seasonal cycle must be documented and removed before any dewpoint anomaly thesis can be evaluated; an undocumented seasonal confound is present | month, Td seasonality | E0_candidate |
| WCT-HUM-011 | HUM | Humidity recovery rate after foehn (dewpoint rising back toward maritime levels after NW weakens) predicts how completely foehn warming dissipates by evening | dewpoint rise rate, post-foehn hours, month | E0_candidate |
| WCT-HUM-012 | HUM | High overnight dew formation (temperature reaches dewpoint before dawn) clusters in calm radiative autumn/spring; identifying these combinations is prerequisite for post-dew warming analysis | dew flag, month, regime | E0_candidate |
| WCT-TIMING-001 | TIMING | The q90 late Tmax timing threshold by month × regime (per ADR-011) has not been documented or visualized; this table is a mandatory prerequisite before any TIMING or SPIKE thesis can proceed | month, regime, q90 table | E0_candidate |
| WCT-TIMING-002 | TIMING | By month, the median Tmax hour varies systematically; summer (Dec–Feb) likely 14:00–16:00; winter (Jun–Aug) likely earlier due to limited solar window; must be verified from data | month, median tmax_hour distribution | E0_candidate |
| WCT-TIMING-003 | TIMING | By regime, the median Tmax hour varies; calm_radiative peaks earliest (dawn-to-noon radiation); foehn days may peak latest (NW strengthens through day); southerly days have no clear peak | regime, month, tmax_hour distribution | E0_candidate |
| WCT-TIMING-004 | TIMING | Month × regime cells with fewer than 30 historical occurrences should be flagged as underpowered for timing statistics; q90 thresholds from these cells are unreliable | month, regime, sample size | E0_candidate |
| WCT-TIMING-005 | TIMING | The hours_to_expected_peak feature (H2, rejected) failed because timing norms were not stratified by month × regime; rebuilding this feature with proper conditioning may rescue the concept | month, regime, peak timing prior | E0_candidate |
| WCT-TIMING-006 | TIMING | Post-frontal clearing days show the highest Tmax hour variance; these days are unpredictable in timing because the clearing time is unknown at morning CP | clearing time, month | E0_candidate |
| WCT-TIMING-007 | TIMING | Conditional probability of Tmax occurring before 13:00, between 13:00 and 17:00, and after 17:00 differs by month and regime; these priors are needed for late spike risk assessment | tmax_hour bucket, month, regime | E0_candidate |
| WCT-TIMING-008 | TIMING | In summer, a late Tmax (after q90 threshold) may still be very high (long day); in winter, late Tmax is constrained by early sunset; the relationship between timing lateness and final magnitude is season-dependent | month, tmax_hour vs tmax_int | E0_candidate |
| WCT-TIMING-009 | TIMING | The warming rate from Tmin to any given hour predicts Tmax hour better than any fixed timing prior; the rate at CP encodes whether the warming cycle is ahead or behind the seasonal norm | warming rate by CP, month, regime | E0_candidate |
| WCT-TIMING-010 | TIMING | Days where Tmax occurs at or before the CP window start (temperature has already peaked at CP time) are a structural failure mode; they should be identified by CP and labeled for evaluation | CP, month | E0_candidate |
| WCT-TIMING-011 | TIMING | The summer sea breeze (SSE onset ~14:00–15:00) creates a Tmax cap; when sea breeze arrives before the foehn can sustain its peak, Tmax is capped earlier than on foehn days without sea breeze | sea breeze flag, month | E0_candidate |
| WCT-TIMING-012 | TIMING | Double-peak days (morning warm → brief cool → afternoon peak) require identifying the final peak from morning evidence only; historical frequency of double peaks by month and regime is needed | double peak frequency, month, regime | E0_candidate |
| WCT-TIMING-013 | TIMING | expected_remaining_warming_time = q50_train(tmax_hour | month, regime) − CP_hour is a direct runway measure that is more interpretable than H2's original implementation | month, regime, CP | E0_candidate |
| WCT-TIMING-014 | TIMING | By season, the within-day Tmax timing distribution modality differs: approximately unimodal in summer (14:00–16:00 peak), more dispersed in winter (clear vs cloudy day polarization) | month, tmax_hour distribution shape | E0_candidate |
| WCT-TIMING-015 | TIMING | Days where Tmax is achieved after 21:00 exist and have a specific mechanism (strong NW holding nocturnal temperature, no cooling transition); their frequency and preconditions by month must be cataloged | extreme late tmax count, month | E0_candidate |
| WCT-TIMING-016 | TIMING | The probability of late Tmax (> q90 threshold per month/regime) is predictable from morning wind, cloud, and humidity state; this probability is the true "late spike risk" target | morning predictors, month, regime | E0_candidate |
| WCT-SPIKE-001 | SPIKE | Late spike definition must be `tmax_hour > q90_train(tmax_hour \| month, regime)`; the current informal 17:00 rule misclassifies events in all months by failing to account for day-length and regime-conditional timing norms | month, regime, q90 threshold | E0_candidate |
| WCT-SPIKE-002 | SPIKE | By month, the q90 late Tmax hour threshold differs substantially; a 17:00 Tmax may be unremarkable in June (low solar angle, limited day) but a genuine late event in February | month, q90 by month | E0_candidate |
| WCT-SPIKE-003 | SPIKE | By regime, the q90 late Tmax threshold differs; a 17:00 Tmax is within the normal range for southerly recovery days and late for calm radiative days | regime, month, q90 by regime | E0_candidate |
| WCT-SPIKE-004 | SPIKE | Late spikes are physically caused by at least four distinct mechanisms: (A) post-frontal clearing, (B) slow-developing foehn, (C) afternoon thermal plume, (D) sea breeze failure on strong NW days; these mechanisms have different morning observable signatures | mechanism type, month, regime | E0_candidate |
| WCT-SPIKE-005 | SPIKE | Morning observable signals that precede late spike events: cloud decreasing (cloud at CP20 but clearing by CP23), pressure shift from falling to rising, wind backing from S toward N, temperature rising faster than climatology | compound morning signal, month, regime | E0_candidate |
| WCT-SPIKE-006 | SPIKE | The frequency of late Tmax events by month × regime must be tabulated; cells with < 10% late event rate indicate that a late spike risk model for those cells is predicting a rare event | month, regime, late event rate | E0_candidate |
| WCT-SPIKE-007 | SPIKE | The prediction interval at settlement time is wider on late-spike-candidate days; identifying these days at CP is useful for uncertainty quantification and risk-adjusted forecasting | heteroskedasticity, month, regime | E0_candidate |
| WCT-SPIKE-008 | SPIKE | The "clearing" signal (cloud cover decreasing between consecutive METARs) is the most direct late-spike precursor for southerly_disrupted days; its timing and rate predict whether clearing will generate a significant Tmax | clearing rate, clearing start hour, month | E0_candidate |
| WCT-SPIKE-009 | SPIKE | Post-frontal temperature recovery rate (warming rate after clearing) varies by season; summer clearing yields faster and higher recovery than winter clearing | clearing time, month | E0_candidate |
| WCT-SPIKE-010 | SPIKE | Foehn-driven late spikes (NW foehn developing slowly through day, peaking in late afternoon) differ mechanistically from post-clearing late spikes; foehn late spikes may be more extreme but less frequent | mechanism, month | E0_candidate |
| WCT-SPIKE-011 | SPIKE | Current model mean error on late Tmax days (tmax_hour > q90) should be quantified separately from pooled MAE; if systematic underestimation is found, this is direct evidence for the late spike risk concept | late event subgroup error, month, regime | E0_candidate |
| WCT-SPIKE-012 | SPIKE | By month, the climatological probability of Tmax after sunset is effectively zero; the effective window for late spikes is month-dependent on civil twilight time | month, sunset hour, late event feasibility | E0_candidate |
| WCT-SPIKE-013 | SPIKE | A continuous late spike index (P(late_tmax_event) given morning observables, conditioned on month × regime) is more useful than a binary classification at CP | probability model, month, regime | E0_candidate |
| WCT-SPIKE-014 | SPIKE | Days transitioning from southerly morning to NW afternoon (southerly_disrupted → NW recovery) should be cataloged as a late-spike sub-type with own historical Tmax distribution | transition type, month | E0_candidate |
| WCT-SPIKE-015 | SPIKE | The interaction between month (day length), regime (physical state), and CP lead time (evidence available) forms a 3D space of late spike probability that must be mapped | month × regime × CP | E0_candidate |
| WCT-SPIKE-016 | SPIKE | Days that appear "settled" at CP23 (clear, calm, warming trend) but still experience a late spike likely have an undetected intraday pattern shift; their precursor fingerprint should be characterized | settled-at-CP false confident days, month | E0_candidate |
| WCT-SPIKE-017 | SPIKE | The minimum hours between CP and Tmax for a "late" event should be regime-relative; at CP23, the minimum runway for a genuinely late event is shorter than at CP20 | CP, regime, late event definition | E0_candidate |
| WCT-SPIKE-018 | SPIKE | Tmax variance is higher on late-spike-candidate days; this heteroskedasticity should be modeled explicitly rather than assuming constant prediction uncertainty | Tmax variance, late event flag, month | E0_candidate |
| WCT-CP-001 | CP | The marginal information gain from CP20→CP21 is the largest single step; understanding which physical signal is first captured in the 20:00–21:00 window is the key CP lead time question | CP step, feature maturation, month | E0_candidate |
| WCT-CP-002 | CP | Features validated only at CP21–23 are limited for early market use; the physical reason for CP20 failure (insufficient obs, no dawn signal yet) must be documented per feature | CP, feature_id, month | E0_candidate |
| WCT-CP-003 | CP | By month, the CP at which regime classification stabilizes (no further change with additional obs) varies; summer regime may stabilize at CP21 while winter requires CP23 due to later sunrise | month, CP stability | E0_candidate |
| WCT-CP-004 | CP | The G4 (nowcast suspect) flag at multiple CPs suggests some validated features may be partly coincident with the day's realization; the temporal window contributing to each feature must be audited for causal purity | G4 flag, feature_id, month | E0_candidate |
| WCT-CP-005 | CP | The information gain from each additional hour of morning observations (CP20→CP21→CP22→CP23) should be quantified by feature and month, creating a "feature maturation curve" | CP step, feature effect size, month | E0_candidate |
| WCT-CP-006 | CP | The 3-observation minimum for regime classification means CP20 in late-sunrise months may have fewer valid obs and thus worse regime classification; CP20 regime is seasonally unreliable | month, sunrise time, obs count | E0_candidate |
| WCT-CP-007 | CP | Some features computed at CP23 may still yield useful signal at 22:30 or 22:45; the discrete CP boundary is administrative, not physically motivated; boundary sensitivity should be tested | near-boundary test, feature_id | E0_candidate |
| WCT-CP-008 | CP | The relationship between CP lead time and forecast MAE is not linear; there may be diminishing returns after CP21 with a step improvement at CP23 (dawn observations); documenting this curve by month informs CP prioritization | month, MAE vs CP | E0_candidate |
| WCT-DQ-001 | DQ | METAR temperature rounding (integer Celsius) creates ±0.5 C uncertainty; for small features (effect size 0.01–0.05), this rounding noise may dominate the signal; affected features should be flagged | feature sensitivity to rounding, month | E0_candidate |
| WCT-DQ-002 | DQ | Wind direction is reported in 10-degree increments; sector boundaries near reported increments (270°, 135°, 225°, 45°) are affected by this discretization; boundary sensitivity should be tested | boundary direction values, month | E0_candidate |
| WCT-DQ-003 | DQ | p01i (1-hour precip) has a detection threshold of ~0.1 mm; very light precipitation is missed; the light-rain domain has a systematic data gap that affects RAIN-004 and any precipitation intensity thesis | precip threshold, month | E0_candidate |
| WCT-DQ-004 | DQ | Missing observations in the morning window (gap at 06:00–07:00) disproportionately affect warming rate features because they fall in the critical dawn window; gap frequency by hour and month must be audited | hour of gap, month | E0_candidate |
| WCT-DQ-005 | DQ | DST transitions create apparent 23-hour and 25-hour days in local time; the warming window length on transition days differs and should be handled explicitly | DST transition date, month | E0_candidate |
| WCT-DQ-006 | DQ | Calm wind direction (00000KT) creates missing direction values; the reason for calmness (true calm vs calm before NW onset) affects regime classification; this should be tracked | calm flag, subsequent wind direction, month | E0_candidate |
| WCT-DQ-007 | DQ | The day_complete flag may exclude valid days where a single late-day gap exists; their systematic properties should be audited for selection bias before the training set is finalized | day_complete audit, month | E0_candidate |
| WCT-DQ-008 | DQ | SPECI (special observation) reports during frontal passages create non-uniform observation spacing; all hourly-delta features may be affected on high-SPECI days; SPECI density by hour and month must be documented | SPECI count, hour, month | E0_candidate |

---

## DOMAIN: GAP — 50 Additional Gap Theses

> These theses address potential coverage gaps, methodological blind spots, and physical phenomena not captured in the main 200 theses. They are all `E0_candidate` and require blocking/unblocking assessment.

| ID | Claim (short) | Key gap type | Status |
|---|---|---|---|
| WCT-GAP-001 | No documented cooling mechanism taxonomy; the classifier cannot be repaired without first distinguishing the 4+ physical types of cooling the rule captures | Structural missing artifact | E0_candidate |
| WCT-GAP-002 | No monthly wind rose for NZWN; all wind sector theses are implicitly averaged across months | Missing prior | E0_candidate |
| WCT-GAP-003 | No Tmax hour distribution table by month × regime; prerequisite for all TIMING and SPIKE theses | Missing artifact | E0_candidate |
| WCT-GAP-004 | No systematic catalog of "clear sky, below-average Tmax" events; CL-019 is hypothesized but not enumerated | Missing event catalog | E0_candidate |
| WCT-GAP-005 | No regime transition probability matrix (Markov); fundamental for D-1 regime → D-0 prediction | Missing structural analysis | E0_candidate |
| WCT-GAP-006 | No post-frontal recovery time study; hours from frontal passage to Tmax by month is the core late-spike variable for southerly days | Missing study | E0_candidate |
| WCT-GAP-007 | No METAR reporting gap audit by hour of day; missing obs are not random and affect morning feature quality systematically | Data quality gap | E0_candidate |
| WCT-GAP-008 | No month-calibrated foehn score threshold; the fixed 60 is untested against data-derived optima | Uncalibrated threshold | E0_candidate |
| WCT-GAP-009 | No clear-sky radiation proxy (DOY + latitude + cloud attenuation); cloud cover is a poor substitute for actual solar input | Missing proxy | E0_candidate |
| WCT-GAP-010 | No multi-day heat event (3+ day above-normal) characterization; clustering pattern and Tmax distribution for heatwave-like sequences is absent | Missing event type | E0_candidate |
| WCT-GAP-011 | No Tmin-Tmax correlation analysis by month and regime; the H6 validated feature masks sub-group structure (high Tmin+high Tmax on maritime days vs low Tmin+high Tmax on foehn days) | Missing stratification | E0_candidate |
| WCT-GAP-012 | No catalog of intraday temperature reversals (≥2 C mid-day drop then recovery); primary source of double-peak days and a late-spike mechanism | Missing event type | E0_candidate |
| WCT-GAP-013 | H8 (wind_dir_change_S_to_N) was rejected as coded; whether wind rotation ORDER (S→SW→W→NW vs NW→W→S) matters has never been tested with proper circular directional algebra | Rejected-but-untested reformulation | E0_candidate |
| WCT-GAP-014 | No quantification of Cook Strait channeling speed amplification; airport speed may not represent the regional NW; all speed thresholds may be airport-specific | Site calibration gap | E0_candidate |
| WCT-GAP-015 | Cloud base HEIGHT trend during morning (rising vs falling) was proposed in WCT-CLOUD-013 but not in any current feature; it is absent from the H1–H23 catalog | Missing feature concept | E0_candidate |
| WCT-GAP-016 | No regime-conditional remaining warming distribution (P10/P50/P90 by regime × month × CP); the fundamental distribution of the forecast target is not documented | Missing distributional artifact | E0_candidate |
| WCT-GAP-017 | No Tmax anomaly (Tmax minus DOY climatology) distribution analysis by month; normality, variance, and tail behavior of anomalies are undocumented | Missing distributional analysis | E0_candidate |
| WCT-GAP-018 | No fog occurrence pattern analysis; fog presence changes the warming trajectory fundamentally and has not been analyzed separately from low cloud | Missing phenomenon | E0_candidate |
| WCT-GAP-019 | H3 (regime_label) was tested only pooled across regimes; per-regime performance of the label itself has not been evaluated (circular but meaningful for segment power analysis) | Missing segment analysis | E0_candidate |
| WCT-GAP-020 | No sensitivity analysis of the −2 C/h cooling threshold; what does the southerly_disrupted population look like at −1.5 and −2.5 C/h? How does it interact with the time of day of cooling? | Threshold sensitivity | E0_candidate |
| WCT-GAP-021 | H21 (pre-frontal warming window) was rejected without root-cause analysis; whether the window was wrongly coded or the physical phenomenon is absent in Wellington data has not been determined | Rejected feature root cause | E0_candidate |
| WCT-GAP-022 | No analysis of precipitation type (frontal vs convective); these types have different duration, intensity, and post-event clearing characteristics | Missing phenomenon split | E0_candidate |
| WCT-GAP-023 | No wind direction uncertainty quantification; days where direction alternates between two sectors in adjacent obs should be flagged for regime reliability analysis | Measurement uncertainty | E0_candidate |
| WCT-GAP-024 | ENSO/IOD effects on Wellington Tmax are not registered; interannual variability from ENSO may explain long-term residuals | BLOCKED — requires ENSO index | E0_candidate |
| WCT-GAP-025 | No quantification of the physical Tmax ceiling effect (SST cap, mixing cap, urban heat island absence); upper bounds on Tmax by month and regime are not defined | Missing upper bound study | E0_candidate |
| WCT-GAP-026 | No observation count effect study; features from windows with 2–4 obs vs 8–10 obs have different noise levels; this heteroskedasticity affects weighting and reliability | Data quality gap | E0_candidate |
| WCT-GAP-027 | No study of "near-miss southerlies" (brief southerly surge → recovery); these days (currently southerly_disrupted) may have high Tmax via rapid recovery and are the most under-predicted group | Missing sub-type | E0_candidate |
| WCT-GAP-028 | No analysis of which Onda 4 gates fail by month; the R2 block on calm_radiative and standard_nw may be driven by specific months with sparse data rather than universal regime weakness | Month-disaggregated gate analysis | E0_candidate |
| WCT-GAP-029 | D-1 REGIME (not D-1 Tmax) × D-0 regime interaction is untested; H5 (D-1 Tmax) was rejected but the regime-sequence effect may carry signal missed by the scalar temperature | Missing interaction | E0_candidate |
| WCT-GAP-030 | No sea breeze onset timing study; if sea breeze arrives earlier than normal, Tmax is capped earlier; onset timing distribution by month and synoptic regime is absent | Missing phenomenon | E0_candidate |
| WCT-GAP-031 | No study of convective days (summer afternoon thunderstorm); convective initiation effectively limits Tmax by vertical mixing and cloud shading | Missing event type | E0_candidate |
| WCT-GAP-032 | No warming trajectory shape analysis (sinusoidal expected shape vs actual deviations); deviations encode foehn onset, cloud interruption, and clearing; no current feature captures the shape | Missing shape feature concept | E0_candidate |
| WCT-GAP-033 | No anticyclone age effect study; day 2 and day 3 of a multi-day anticyclone may have systematically different Tmax than day 1 due to progressive drying and pressure change | Missing sequence analysis | E0_candidate |
| WCT-GAP-034 | Wellington Tmax percentile climatology (P5/P25/P75/P95 by DOY) is not used in any EDA stratification; anomaly contextualization requires this as a denominator | Missing percentile artifact | E0_candidate |
| WCT-GAP-035 | CP22 is rarely validated or studied independently; whether it adds independent information over CP21 is unanswered | CP coverage gap | E0_candidate |
| WCT-GAP-036 | No analysis of hourly temperature profile during precipitation; the evaporative cooling signature during rain vs before/after carries information about rain type and intensity | Missing intra-event analysis | E0_candidate |
| WCT-GAP-037 | No systematic catalog of extreme Tmax days (top 5%); meteorological preconditions for exceptional days have not been enumerated | Missing extreme event catalog | E0_candidate |
| WCT-GAP-038 | No southerly disruption persistence distribution by month; duration of southerly events (hours) differs by month and affects how often morning southerly becomes full-day vs partial-day event | Missing duration distribution | E0_candidate |
| WCT-GAP-039 | H18 (nocturnal_plateau_flag) was rejected as coded but the phenomenon (Tmax already past at CP) may exist and is structurally dangerous for forecasting; root cause of rejection not analyzed | Rejected feature root cause | E0_candidate |
| WCT-GAP-040 | No feature importance temporal stability check; a feature validated in aggregate may have unstable importance across different walk-forward windows | Validation gap | E0_candidate |
| WCT-GAP-041 | No non-stationarity test on the Tmax series (2009–2026); climate trends, equipment changes, or land use changes near the airport could create temporal drift | Data stationarity | E0_candidate |
| WCT-GAP-042 | No northerly surge event detection (speed increases from ~10 to ~30 kt over 2–3 h); this rapid onset event generates rapid Tmax increase and is not represented in any feature | Missing event type | E0_candidate |
| WCT-GAP-043 | No cloud cover persistence during post-frontal recovery; whether cloud clears quickly or persists for hours after frontal passage determines if Tmax recovery is achievable | Missing post-event analysis | E0_candidate |
| WCT-GAP-044 | Validated features H1/H6/H10/H12/H17/H20/H23 have not been tested for inter-correlation; some may be proxies for the same underlying phenomenon, inflating apparent information | Feature redundancy | E0_candidate |
| WCT-GAP-045 | No diurnal temperature range (DTR) analysis by month and regime; DTR at the right time of day may predict Tmax better than either Tmin or Tmax alone | Missing variable analysis | E0_candidate |
| WCT-GAP-046 | No Wellington "southerly buster" sub-type analysis; a rapid intense southerly with a characteristic sharp temperature drop may warrant a separate southerly_disrupted sub-class | Missing sub-type | E0_candidate |
| WCT-GAP-047 | No analysis of temperature inversion strength at dawn; the inversion lid constrains morning warming amplitude; proxy evidence may be available from surface dewpoint vs temperature spread | Missing proxy | E0_candidate |
| WCT-GAP-048 | No documentation of which month × regime cells are sample-size limited (< 30 days); these cells should be flagged in every EDA to prevent spurious patterns from sparse strata | Missing power analysis | E0_candidate |
| WCT-GAP-049 | No study of the orographic cloud shadow effect specific to NZWN (Tararua rain shadow sheltering the airport from cloud while generating cloud further north); this is a site-specific effect with direct impact on cloud feature reliability | Site-specific gap | E0_candidate |
| WCT-GAP-050 | No joint uncertainty propagation analysis; individual features have documented leakage risks, but the combined leakage risk of using multiple features together in a model has not been assessed | Compound leakage risk | E0_candidate |

---

## Detailed Thesis Definitions

> Each thesis below expands the registry entry with physical rationale, observable evidence, causal availability, strata requirements, test plan, and leakage risk. Presented by domain.

---

### REGIME Domain (20 theses)

---

#### WCT-REGIME-001
**Claim:** The cooling rule (`min_delta_t_per_h < −2 C/h`) in the `southerly_disrupted` classifier captures pre-dawn radiative cooling events (physically normal, not synoptic disruption) as well as frontal cooling, leading to chronic misclassification of calm/NW mornings.

**Physical rationale:** Wellington Airport is in an open coastal position with good long-wave radiation loss on clear-sky calm nights. Pre-dawn cooling rates of 2–3 C/h are expected on calm anticyclonic mornings, especially in autumn/spring when nights are long and skies are clear. The rule was intended to flag frontal cooling but fires indiscriminately on any sharp cooling regardless of wind and sky state.

**Observable evidence:** `tmp_c_int` time series in pre-CP window, `wind_dir_deg`, `sknt`, cloud codes. Min delta hour must be derived from obs timestamps.

**Causal availability:**
- CP20: first ~2h of midnight window available.
- CP21–23: full window; min-delta hour is computable.

**Target relation:** regime_label assignment accuracy, southerly_disrupted share by month, Tmax error on misclassified days.

**Strata:** month (1–12), CP, hour of min-delta (<06:00 vs 06:00–12:00), wind sector during cooling.

**Test plan:**
1. Extract hour of minimum delta_t for all southerly_disrupted rows.
2. Cross-tabulate with wind sector during cooling hour.
3. Compare Tmax anomaly distributions: cooling before 06:00 with light/calm wind vs cooling 06:00–12:00 with southerly wind.
4. Simulate removing pre-dawn calm-wind cooling events from trigger; compare regime distribution.

**Leakage risk:** None — all features are pre-CP. Avoid using final regime as anything but an evaluation segment.

**Status:** E0_candidate

---

#### WCT-REGIME-002
**Claim:** The frequency of `southerly_disrupted` is highest in winter (Jun–Aug) and lowest in summer (Dec–Feb); this seasonal variation is not captured in the current classifier, which treats all months equally.

**Physical rationale:** New Zealand's mid-latitude position means more active westerly/southerly frontal systems pass in winter. The cool-season jet stream steers more systems across the region. Summer is typically under higher pressure (more anticyclonic).

**Observable evidence:** `regime_label` (post-hoc), date_local for month extraction.

**Causal availability:** Month is fully available at all CPs (it is a calendar quantity).

**Target relation:** Prior probability of each regime by month — required for Bayesian updating with CP evidence.

**Strata:** month (1–12).

**Test plan:**
1. Compute regime frequency by month from features.parquet.
2. Plot monthly regime distribution (stacked bar).
3. Chi-square test of regime × month independence.
4. Document which months have fewer than 30 days per regime (sample-size limit).

**Leakage risk:** None — uses causal regime labels and calendar month only.

**Status:** E0_candidate

---

#### WCT-REGIME-003
**Claim:** `calm_radiative` has only 625 rows (≈2.9% of feature rows) because the cooling rule absorbs clear-sky radiative nights into `southerly_disrupted`; the true frequency of calm radiative mornings is substantially higher.

**Physical rationale:** Radiative cooling nights (clear, calm) are common under anticyclonic conditions. These nights cool faster than maritime cloudy nights. If the −2 C/h threshold fires on these nights, the morning is misclassified as southerly_disrupted even though no southerly flow exists.

**Observable evidence:** southerly_share, cooling trigger hour, wind sector, cloud codes, regime_label.

**Causal availability:** All fields available at CP21–23.

**Target relation:** calm_radiative frequency, R2 gate failure (underpowered segment).

**Strata:** month, cooling trigger hour bin.

**Test plan:**
1. From southerly_disrupted rows where cooling is the primary trigger and southerly_share < 0.2 and NW flow present, tabulate.
2. Estimate how many would reclassify to calm_radiative under a relaxed cooling rule.
3. Cross-reference with cloud codes: if cloud was SCT or less and wind was light, likely misclassified.

**Leakage risk:** Experiment must not change production labels in features.parquet without a proper validation cycle.

**Status:** E0_candidate

---

#### WCT-REGIME-004
**Claim:** The NW sector (270–045°) contains three physically distinct sub-sectors: W (260–290°, cold Cook Strait crossing), NW (290–330°, mixed), N/NNE (330–045°, warm foehn descent). These sub-sectors have different Tmax impacts.

**Physical rationale:** Air from 260–290° crosses the cold Cook Strait waters before arriving at Wellington. Air from 330–045° descends from the Tararua/Rimutaka ranges with adiabatic warming. The 270–045° arc conflates cold-water-crossing with mountain-descent flow.

**Observable evidence:** `wind_dir_deg`, `sknt`, `dwp_c_int`, `tmp_c_int`, Tmax label.

**Causal availability:** Wind direction available at all CPs.

**Target relation:** Tmax anomaly by sub-sector, foehn score by sub-sector.

**Strata:** sub-sector (W, NW, N/NNE), month, wind speed bin.

**Test plan:**
1. Compute median Tmax anomaly (vs climatology) for each sub-sector, stratified by month.
2. Compare dewpoint depression by sub-sector.
3. Test whether N/NNE has significantly higher Tmax anomaly than W, controlling for speed.

**Leakage risk:** Use only pre-CP wind observations for sector assignment; Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-005
**Claim:** Daily regime transitions follow non-random sequences by month; the conditional probability P(D-0 regime | D-1 regime, month) differs materially from the marginal P(D-0 regime | month).

**Physical rationale:** Weather systems evolve with time scales of 2–5 days. After a southerly front, the next day tends to be post-frontal clearing or early NW recovery. After a foehn event, the next day may continue foehn or begin a new frontal sequence. These are physical persistence and transition patterns.

**Observable evidence:** `regime_label` on consecutive days, `date_local`.

**Causal availability:** D-1 regime is fully observable by D-0 CP20.

**Target relation:** D-0 regime assignment probability (prior improvement), D-0 Tmax prediction improvement.

**Strata:** month, D-1 regime, D-0 regime (transition type).

**Test plan:**
1. Build a 4×4 transition matrix by month.
2. Test each cell against the marginal distribution (chi-square or likelihood ratio).
3. Identify the month/transition combinations with the largest departure from independence.
4. Compute the information gain (KL divergence) of knowing D-1 regime for each month.

**Leakage risk:** D-1 regime uses D-1 causal pre-CP labels only; D-0 regime is causal by construction. The D-0 Tmax is the evaluation target only.

**Status:** E0_candidate

---

#### WCT-REGIME-006
**Claim:** The `foehn_score` threshold of 60 for `strong_nw_foehn` is not calibrated by month; the same NW flow produces different dewpoint depression in summer (naturally more humid) vs winter (drier baseline air).

**Physical rationale:** The initial dewpoint before foehn descent varies with the air mass origin. In summer, maritime air has higher dewpoint, so foehn descent produces a larger relative change but may not always exceed the fixed threshold. In winter, drier air masses may produce high foehn_score even for moderate NW events.

**Observable evidence:** `foehn_score` (computed), `dwp_c_int`, `sknt`, month, Tmax label.

**Causal availability:** foehn_score components available at CP21–23.

**Target relation:** strong_nw_foehn frequency by month, Tmax anomaly by foehn_score bin.

**Strata:** month, foehn_score bin (0–20, 20–40, 40–60, 60–80, 80+).

**Test plan:**
1. Plot foehn_score distribution by month.
2. For each month, find the foehn_score value that maximizes Tmax anomaly separation.
3. Test whether the optimal threshold by month differs from 60 using bootstrapped confidence intervals.

**Leakage risk:** Use train-only data to find month-specific thresholds; test-set Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-007
**Claim:** `standard_nw` has only 2,466 rows (≈11.3%) because the cooling rule steals approximately 8,570 rows that should properly belong to `standard_nw`; this underpowers the segment and causes R2 failure.

**Physical rationale:** This is an empirically supported claim from the 2026-06-06 cooling-rule experiment (documented in `reports/regime/2026-06-06-cooling-rule-experiment.md`). The experiment showed 8,570 rows would move from southerly_disrupted to standard_nw if cooling were not the sole trigger.

**Observable evidence:** Trigger audit artifact, cooling rule experiment simulation.

**Causal availability:** All regime features are pre-CP causal.

**Target relation:** R2 gate (dead regime check), standard_nw Tmax prediction skill.

**Strata:** month, cooling trigger type.

**Test plan:**
1. From trigger audit: identify southerly_disrupted rows with cooling primary trigger and no southerly wind sector evidence.
2. For these rows, compute Tmax anomaly; test if it resembles standard_nw or southerly_disrupted.
3. Propose a revised trigger that requires at least one of: (a) southerly wind share ≥ 0.3, (b) precipitation, (c) post-dawn cooling.

**Leakage risk:** Simulation only; changes to production labels require a new validation cycle and Onda 4 rerun.

**Status:** E0_candidate

---

#### WCT-REGIME-008
**Claim:** In summer months (Nov–Feb), regime classification stabilizes earlier (CP21 often sufficient) because the morning warming cycle begins before the CP window ends; in winter (May–Aug), CP23 may be needed for reliable regime assignment.

**Physical rationale:** In summer, sunrise occurs around 05:30–06:30; by CP21 (21:00 prior day local), the pre-dawn window already includes useful thermal signals. In winter, sunrise is after 07:30 and the CP window ends before dawn has had any warming effect.

**Observable evidence:** Regime label stability (does the label change when the window is extended from CP20 to CP21 to CP22 to CP23?), sunrise time, month.

**Causal availability:** CP and sunrise time are fully causal.

**Target relation:** Regime classification stability, feature effect size by CP.

**Strata:** month (winter vs summer), CP step.

**Test plan:**
1. For each day, classify regime at CP20, 21, 22, 23 using progressively longer observation windows.
2. Compute label stability (fraction of days where label changes with each additional CP step) by month.
3. Document the "regime stabilization CP" by month.

**Leakage risk:** Use only pre-CP observations at each CP step; no final-day outcomes.

**Status:** E0_candidate

---

#### WCT-REGIME-009
**Claim:** Regime border cases (foehn_score near 60 ± 10, nw_share near 0.4 ± 0.05) have systematically weaker Tmax prediction skill than cases far from borders because the classifier makes arbitrary binary decisions in physically ambiguous regions.

**Physical rationale:** A continuous physical phenomenon (gradual NW flow strengthening with progressive drying) is discretized by hard thresholds. Cases near the threshold are the most uncertain physically. Hard-boundary classifiers impose sharp error discontinuities near thresholds.

**Observable evidence:** foehn_score, nw_share, Tmax anomaly, regime_label.

**Causal availability:** Scores and shares available at CP21–23.

**Target relation:** Tmax prediction error, regime classification confidence.

**Strata:** distance from regime boundary (near vs far), month.

**Test plan:**
1. Define "near boundary" as foehn_score within 10 of 60, or nw_share within 0.05 of 0.4.
2. Compare MAE on near-boundary vs far-from-boundary days.
3. Test whether a soft scoring (probability of regime) reduces boundary-region errors.

**Leakage risk:** Boundary definition uses pre-CP features only; Tmax is evaluation.

**Status:** E0_candidate

---

#### WCT-REGIME-010
**Claim:** Wind direction natural cluster boundaries in the NZWN METAR data may differ from the prescribed sector cutoffs (270°, 135°, 225°, 45°); data-driven direction cluster centers should be computed and compared to the prescribed boundaries.

**Physical rationale:** Wellington's terrain channels wind into preferred direction corridors. The actual wind rose may show concentrated frequencies at 10–30°, 150–180°, 290–320°, rather than uniformly distributed. The natural cluster boundaries may not coincide with the prescribed cutoffs.

**Observable evidence:** `wind_dir_deg` distribution, all obs, by month.

**Causal availability:** Wind direction is fully pre-CP.

**Target relation:** Regime classification boundary, sector-Tmax relationship steepness.

**Strata:** month.

**Test plan:**
1. Plot the full NZWN wind direction rose by month.
2. Identify natural gaps in the direction distribution (valleys in the histogram).
3. Compare natural boundaries to prescribed boundaries (270, 135, 225, 45).
4. Test whether using natural boundaries improves Tmax anomaly separation.

**Leakage risk:** Wind direction is pre-CP; Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-011
**Claim:** The pre-dawn window (00:00–06:00) cooling trigger in the classifier conflates two physically distinct phenomena: (A) normal radiative overnight cooling (expected on any calm clear night) and (B) post-dawn frontal cooling (synoptic disruption); only (B) should trigger `southerly_disrupted`.

**Physical rationale:** Radiative cooling follows a smooth, predictable curve from sunset to pre-dawn minimum. Its rate is governed by clear-sky long-wave emission and is independent of frontal activity. Frontal cooling is sudden, tied to wind change, and usually arrives in a discrete shock. The classifier applies the same trigger to both.

**Observable evidence:** `tmp_c_int` time series, `wind_dir_deg`, hour of min-delta, cloud codes.

**Causal availability:** Full pre-dawn window is available at CP20–23.

**Target relation:** Regime classification accuracy, southerly_disrupted composition.

**Strata:** month, hour of min-delta (pre-dawn = 00:00–05:59, dawn = 06:00–08:59, post-dawn = 09:00+), wind sector during cooling.

**Test plan:**
1. For all southerly_disrupted rows with cooling trigger: extract hour of minimum delta.
2. Split by pre-dawn calm-wind vs post-dawn southerly-wind.
3. Compare Tmax distributions of the two groups.
4. If distributions differ significantly, propose a time-conditioned cooling rule.

**Leakage risk:** All fields are pre-CP. Hour of cooling event is observable before CP.

**Status:** E0_candidate

---

#### WCT-REGIME-012
**Claim:** `strong_nw_foehn` is heavily concentrated in spring–summer (Oct–Mar); using annual statistics for this regime without month stratification makes timing thresholds, Tmax distributions, and feature effect sizes misleading.

**Physical rationale:** The synoptic patterns that drive strong NW/foehn events are more frequent in spring as the westerly jet strengthens and frontal systems become more active. Summer has more settled high-pressure events. Winter southerlies dominate. Foehn events are spring-autumn biased in the historical record.

**Observable evidence:** `regime_label`, `date_local` (month), Tmax label.

**Causal availability:** Month is fully causal.

**Target relation:** Monthly prior for strong_nw_foehn, timing thresholds, Tmax distributions.

**Strata:** month.

**Test plan:**
1. Compute strong_nw_foehn frequency by month.
2. Compute Tmax anomaly and tmax_hour distributions separately by month.
3. Flag months with fewer than 15 strong_nw_foehn days as underpowered for timing statistics.

**Leakage risk:** None — uses only causal regime label and calendar.

**Status:** E0_candidate

---

#### WCT-REGIME-013
**Claim:** D-1 regime state predicts D-0 regime assignment probabilities beyond a naive DOY prior; P(D-0 = calm_radiative | D-1 = southerly_disrupted, month = Oct) > P(D-0 = calm_radiative | month = Oct) because post-frontal clearing is a predictable sequence.

**Physical rationale:** Post-frontal recovery is a well-documented meteorological sequence: frontal passage → cold southerly → rapid pressure rise → clearing → NW or calm radiative. This creates a systematic conditional probability for day-following-southerly having calm or NW regime.

**Observable evidence:** D-1 `regime_label`, D-0 `regime_label` (causal), `date_local`.

**Causal availability:** D-1 regime is fully observable by D-0 CP20.

**Target relation:** D-0 regime prior, D-0 Tmax distribution.

**Strata:** month, D-1 regime (4 values), D-0 regime (4 values) — 4×4×12 cells.

**Test plan:**
1. Build monthly 4×4 transition matrices.
2. Compute information gain KL(P(D-0|D-1) || P(D-0)) for each month.
3. Identify high-information transitions.
4. Test whether D-1 regime improves Tmax prediction as a conditioning variable.

**Leakage risk:** D-1 regime uses only D-1 pre-CP observations. D-0 regime is causal. D-0 Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-014
**Claim:** Foehn events cluster in multi-day sequences; the probability of `strong_nw_foehn` on D+1 given `strong_nw_foehn` on D-0 is materially higher than the base rate, especially in spring and autumn.

**Physical rationale:** The synoptic patterns that drive foehn — blocking highs over the Tasman, northerly flow ahead of a stalled front — often persist for 2–4 days before a front finally passes. Multiple consecutive foehn days are therefore physically expected.

**Observable evidence:** `regime_label` on consecutive days.

**Causal availability:** D-1 regime is causal at D-0 CP20.

**Target relation:** D-0 regime prior, multi-day foehn Tmax trajectory.

**Strata:** month, consecutive foehn day count (1, 2, 3+).

**Test plan:**
1. Identify consecutive foehn sequences in the label history.
2. Compute Tmax anomaly by sequence position (day 1 vs day 2 vs day 3+).
3. Test if day 2 and day 3+ have different Tmax than day 1.
4. Document whether multi-day foehn shows increasing or stable Tmax (does drying accumulate?).

**Leakage risk:** Uses only D-1 causal regime. Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-015
**Claim:** The `southerly_disrupted` → `calm_radiative` transition (post-frontal clear) is an identifiable sequence that produces systematically higher next-day Tmax because the post-frontal air mass is clean (low dewpoint, no cloud).

**Physical rationale:** After a cold front passes Wellington, the southerly gradually backs to SW and then W/NW as the high pressure builds in. Skies clear (subsidence). The next morning begins clear and cold (strong radiative cooling from the clean air), setting up a high DTR day with potentially high Tmax under solar heating.

**Observable evidence:** D-1 → D-0 regime transition, D-0 Tmax anomaly, D-0 cloud cover, D-0 dewpoint.

**Causal availability:** D-1 regime is causal at D-0 CP20. D-0 cloud/dewpoint is pre-CP.

**Target relation:** D-0 Tmax anomaly — evaluation target only.

**Strata:** month, D-1 → D-0 transition type.

**Test plan:**
1. Filter for D-1 = southerly_disrupted AND D-0 = calm_radiative.
2. Compare D-0 Tmax anomaly to (a) D-0 calm_radiative all, (b) other D-1 → calm_radiative transitions.
3. Stratify by month.
4. Compute the effect size of the specific southerly → calm pathway.

**Leakage risk:** D-0 Tmax is evaluation only. D-1 regime is fully causal.

**Status:** E0_candidate

---

#### WCT-REGIME-016
**Claim:** A K=4 Gaussian Mixture Model may not be the optimal cluster count for Wellington; K=3 (merging strong_nw_foehn into standard_nw) or K=5 (splitting southerly into frontal vs shallow maritime) should be evaluated with BIC/AIC.

**Physical rationale:** The current K=4 was a candidate finding from the Onda 2R clustering study. BIC selection was not confirmed as decisive. A K=5 solution might separate "shallow southerly" (brief change, quick recovery) from "deep frontal southerly" (persistent suppression).

**Observable evidence:** Morning METAR features used for clustering: wind vector, Td-T, pressure, cloud codes.

**Causal availability:** All clustering features are pre-CP.

**Target relation:** Tmax prediction error by cluster, R2 gate performance.

**Strata:** month (clustering may be more stable if run within-season).

**Test plan:**
1. Run GMM for K=3, 4, 5 with BIC/AIC selection.
2. For each K, compute within-cluster Tmax anomaly spread.
3. For each K, test regime × Tmax MAE vs the current K=4 solution.
4. Document cluster interpretability.

**Leakage risk:** Clustering must be run on pre-CP features; Tmax and timing labels must not enter the feature matrix.

**Status:** E0_candidate

---

#### WCT-REGIME-017
**Claim:** When wind speed is below 5 kt and direction is variable/calm, the classifier defaults to `calm_radiative`. However, pre-dawn calm before a NW onset event is qualitatively different from true calm radiative conditions and should not be labeled the same.

**Physical rationale:** On days where a NW foehn event is developing, wind may temporarily drop to calm during the overnight transition. The subsequent morning shows rapidly strengthening NW flow. Labeling the calm phase as calm_radiative misrepresents the developing warming trajectory.

**Observable evidence:** Wind speed, direction trend during window, subsequent warming rate, regime label.

**Causal availability:** Wind speed and trend are pre-CP.

**Target relation:** Regime label accuracy, subsequent Tmax anomaly for calm-pre-NW days.

**Strata:** month, calm duration, subsequent wind sector change.

**Test plan:**
1. Identify days labeled calm_radiative where wind strengthens to NW > 10 kt in the second half of the CP window.
2. Compare their Tmax anomaly to pure calm_radiative (no subsequent NW strengthening).
3. Test whether the "calm-before-NW" sub-type has higher Tmax than true calm_radiative.

**Leakage risk:** Window split must remain pre-CP; Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-018
**Claim:** Regime classification inconsistencies (days where foehn_score > 60 but southerly_disrupted is assigned because the cooling rule fired) form a systematic error class with distinct Tmax behavior.

**Physical rationale:** The cooling rule takes priority in the current classifier heuristic. Days with high foehn_score AND a sharp pre-dawn cooling episode are labeled southerly_disrupted even though the dominant physical state by CP may be NW/foehn.

**Observable evidence:** foehn_score, cooling trigger flag, final regime_label, Tmax anomaly.

**Causal availability:** All pre-CP.

**Target relation:** Tmax anomaly for inconsistent cases, model error pattern.

**Strata:** month, foehn_score bin, cooling trigger hour.

**Test plan:**
1. Identify rows: cooling_trigger = True AND foehn_score > 50.
2. Compare their Tmax anomaly to (a) southerly_disrupted (clean cases) and (b) strong_nw_foehn.
3. Test whether these inconsistent cases have Tmax closer to foehn or southerly distribution.
4. Document the monthly frequency of inconsistencies.

**Leakage risk:** Uses only pre-CP features and causal regime label. Tmax is evaluation only.

**Status:** E0_candidate

---

#### WCT-REGIME-019
**Claim:** Monthly regime prior probabilities P(regime | month, CP) have never been documented in the atlas; this table is a mandatory prerequisite before any per-regime per-month thesis can be properly tested or interpreted.

**Physical rationale:** Without knowing the base rates, all conditional analyses are uninterpretable. A 5% increase in Tmax within strong_nw_foehn in October is meaningless if strong_nw_foehn occurs only 3 times in October.

**Observable evidence:** `regime_label`, `date_local`, `cp_time`.

**Causal availability:** Fully causal.

**Target relation:** All downstream theses in REGIME, TIMING, SPIKE, COOLING, WIND domains.

**Strata:** month × regime × CP (4×12 cells minimum).

**Test plan:**
1. Compute counts and proportions per (month, regime, CP).
2. Flag cells with n < 30 as underpowered.
3. Produce a visualization (12-month × 4-regime heat map).
4. Publish as a mandatory prerequisite artifact.

**Leakage risk:** None — uses only causal regime labels and calendar.

**Status:** E0_candidate

---

#### WCT-REGIME-020
**Claim:** `southerly_disrupted` needs a 4-way sub-typology: (A) radiative capture (pre-dawn cooling, light wind), (B) deep frontal southerly (strong S wind, heavy rain, rapid temperature drop after dawn), (C) shallow southerly (brief S intrusion, temperature drop limited), (D) post-frontal partial recovery (southerly weakening, temperature recovering). These 4 sub-types have qualitatively different Tmax distributions.

**Physical rationale:** The current single southerly_disrupted label conflates physically distinct phenomena. Sub-type (A) days may achieve near-normal Tmax by afternoon. Sub-type (B) days are suppressed all day. Sub-type (C) days show partial recovery. Sub-type (D) days may end up as late-spike candidates. Conflating them inflates within-class variance and makes prediction harder.

**Observable evidence:** Cooling trigger hour, southerly wind speed/share, precipitation, temperature recovery rate during CP window, pressure trend.

**Causal availability:** All sub-type discriminators are observable pre-CP.

**Target relation:** Tmax anomaly distribution by sub-type, model error by sub-type.

**Strata:** month, sub-type (A/B/C/D).

**Test plan:**
1. Define discriminating rules for each sub-type based on the physical rationale.
2. Apply to the southerly_disrupted rows and assign sub-type labels.
3. Compute Tmax anomaly distribution per sub-type per month.
4. Test whether sub-type Tmax distributions are significantly different from each other.
5. Assess whether sub-type is predictable from CP-observable features.

**Leakage risk:** Sub-type discriminators must use only pre-CP features. Tmax is evaluation only.

**Status:** E0_candidate

---

### COOLING Domain (20 theses)

> Full detailed expansions for WCT-COOL-001 through WCT-COOL-020 follow the same structure as the REGIME theses above. For brevity in this atlas draft, the remaining domain theses are presented in compact form. Full expansion of each thesis follows the same template and should be produced in the domain-specific reports.

---

**WCT-COOL-001** — Cooling peak hour (before 06:00 = radiative, after 09:00 = frontal) is a better disruption discriminator than magnitude alone. *Strata: month, CP window, cooling hour bin.* The test plan derives the hour of minimum delta_t for every southerly_disrupted row and cross-tabulates with wind sector; the hypothesis passes if the Tmax anomaly distributions of pre-dawn calm-wind cooling and post-dawn southerly cooling are statistically different by month.

**WCT-COOL-002** — Winter (Jun–Aug) has longer, colder radiative nights; the −2 C/h threshold fires more often on non-disrupted winter mornings, inflating southerly_disrupted false positives in winter. *Strata: month, cooling trigger hour.* Test: false positive rate of the cooling rule (cooling trigger = True but southerly_share < 0.2) by month.

**WCT-COOL-003** — Frontal cooling: rapid direction shift + fast temperature drop, distinct from gradual radiative cooling with light/variable wind. The wind speed during the cooling hour is the key discriminator. *Strata: month, wind speed during cooling.* Test: compare Tmax anomaly for (high-speed cooling vs low-speed cooling) × month.

**WCT-COOL-004** — Dewpoint rises during maritime S/SE cooling (maritime air replaces continental); dewpoint falls or holds during foehn-adjacent cooling. This sign discriminates cooling type without needing wind direction confidence. *Strata: month, wind sector.* Test: dewpoint trend during cooling × cooling type × month × Tmax anomaly.

**WCT-COOL-005** — Continuous cooling duration (hours) by CP predicts Tmax suppression depth better than the minimum cooling rate; the accumulated cold is what matters. *Strata: month, CP, cooling duration bin.* Test: regress remaining_warming on cooling duration × month × regime.

**WCT-COOL-006** — Southerly wind speed during the cooling episode discriminates sustained suppression from transient disruption: >20 kt southerly during cooling predicts all-day suppression. *Strata: month, southerly speed bin.* Test: conditional Tmax distribution by speed bin × month.

**WCT-COOL-007** — Post-frontal recovery is a distinct sub-class within southerly_disrupted; afternoon Tmax of recovery days resembles the climatological mean despite morning disruption. *Strata: month, recovery indicator (pressure trend turning positive + wind backing).* Test: compare Tmax anomaly of recovery-flag days vs non-recovery southerly_disrupted by month.

**WCT-COOL-008** — In summer (Dec–Feb), 3–4 C of frontal morning cooling still leaves high remaining warming potential; in winter (Jun–Aug), the same cooling leaves almost no remaining warming. *Strata: month, cooling depth.* Test: correlation of cooling depth with remaining_warming by month; test whether month × cooling interaction is significant.

**WCT-COOL-009** — Cooling events arriving after 09:00 suppress Tmax more severely than pre-dawn cooling because they interrupt the established daytime warming cycle. *Strata: month, cooling onset hour.* Test: Tmax anomaly vs cooling onset hour × month; test for monotone relationship.

**WCT-COOL-010** — Temperature at CP relative to the month's climatological temperature at that hour (T_anomaly_at_CP) outperforms the minimum cooling rate as a regime diagnostic. *Strata: month, CP, T_anomaly_at_CP.* Test: compare H3 effect size for T_anomaly_at_CP vs min cooling rate × month.

**WCT-COOL-011** — Cooling due to rain evaporation (latent heat cooling: rain present + temperature drop) has a different Tmax suppression signature from dry frontal cooling (no rain, sharp temperature drop + direction shift). *Strata: month, rain flag + dry frontal flag.* Test: Tmax anomaly by cooling type × month.

**WCT-COOL-012** — Maritime cooling (S/SE wind, dewpoint rising) and radiative cooling (calm/light wind, dewpoint steady) produce qualitatively different temperature profile shapes distinguishable from METAR hourly data alone. *Strata: month, cooling type.* Test: profile clustering of the cooling episodes; compare Tmax outcomes.

**WCT-COOL-013** — Consecutive cooling days (D-2, D-1, D-0 all southerly_disrupted) predict more sustained Tmax suppression than isolated single-day disruptions. *Strata: month, consecutive cool day count (1, 2, 3+).* Test: Tmax anomaly by consecutive count × month.

**WCT-COOL-014** — Minimum temperature by CP is a better cooling severity proxy than min cooling rate because it integrates both depth and duration; a cold CP20 temperature is an integrating signal. *Strata: month, CP, T_min_by_CP.* Test: compare effect size of T_min_by_CP vs min_delta_t_per_h for predicting Tmax anomaly by month.

**WCT-COOL-015** — Post-frontal radiative cooling (after southerly, skies clear, wind drops = overnight radiative) is a positive signal for next-day Tmax because it signals clean dry air and clear skies. *Strata: month, post-frontal night cooling flag.* Test: D+1 Tmax anomaly given post-frontal-night cooling, by month.

**WCT-COOL-016** — The rain-Tmax relationship is non-monotonic: moderate cooling + post-noon clearing can yield higher Tmax than no cooling at all (post-frontal clearing overshoot). *Strata: month, clearing time, cooling depth.* Test: plot Tmax anomaly vs (cooling depth, clearing time) for rain days by month; test for non-monotone pattern.

**WCT-COOL-017** — Hours since last cooling event predicts recovery rate: after 36 hours of southerly disruption, residual moisture and cloud suppress Tmax more than after 12 hours. *Strata: month, hours since disruption start.* Test: remaining_warming vs disruption duration × month.

**WCT-COOL-018** — By wind sub-sector, cooling rate within S/SE differs: pure S (180–210°) is colder and drier than SE (135–160°, maritime moist); their Tmax suppression patterns differ. *Strata: month, S vs SE sub-sector.* Test: Tmax anomaly distribution by S vs SE sub-sector × month.

**WCT-COOL-019** — Temperature inversion strength at dawn (temperature rises with height in the stable surface layer) constrains morning warming until the inversion is eroded by surface heating; proxy = (T_dawn - T_pre_dawn) / time, combined with wind. *Strata: month, inversion proxy.* Test: correlation of inversion proxy with morning warming rate × month.

**WCT-COOL-020** — DTR by month and regime is a distributional anchor: constrained DTR is not uniquely southerly_disrupted — maritime stable days also have low DTR. The DTR distribution overlap between regimes by month must be documented. *Strata: month, regime.* Test: compute DTR distributions per (month, regime) and document overlaps.

---

### WIND Domain (20 theses)

> Compact form. Full expansions in WIND domain report.

**WCT-WIND-001** — N/NNE (330–045°) warm sector vs W (260–290°) cold sector heating effects must be quantified separately by month; the 135° NW arc conflates them. *Test: Tmax anomaly by 30° sub-sectors × month × speed bin.*

**WCT-WIND-002** — Wind direction persistence (% obs in same ±30° band during window) correlates more strongly with Tmax outcome than instantaneous direction at any single obs. *Test: persistence metric vs Tmax anomaly × month × CP; compare effect size to instantaneous direction.*

**WCT-WIND-003** — NW/N wind speed has a non-linear (inverted-U or plateau) relationship with Tmax; 15–30 kt is the sweet spot, >35 kt reduces Tmax via mechanical mixing. *Test: median Tmax anomaly by 5 kt speed bins × month × NW sector flag.*

**WCT-WIND-004** — The summer afternoon sea breeze onset time (~14:00–15:00) acts as a Tmax limiter; when it arrives early or strongly, it caps Tmax below the foehn-only expectation. *Test: days with detectable afternoon S/SE shift vs Tmax timing and magnitude × month.*

**WCT-WIND-005** — Morning wind rotation direction (veering N→E→S vs backing S→W→N) predicts whether a NW event is developing or decaying with higher fidelity than a scalar direction metric. *Test: rotation direction flag vs next-period wind regime × Tmax anomaly × month.*

**WCT-WIND-006** — Monthly NZWN wind rose (12 monthly roses) must be produced as a foundational artifact before any wind sector hypothesis is interpreted. *Test: compute roses, document dominant sectors, identify seasonal shifts.*

**WCT-WIND-007** — NE wind (045–090°) imports maritime moisture from Cook Strait entrance, suppressing Tmax differently from both N/NW foehn and S maritime; this sector has not been tested as a cool/neutral category. *Test: Tmax anomaly distribution for NE sector × month vs NW and S sectors.*

**WCT-WIND-008** — Wind direction IQR during morning window (steadiness proxy) predicts afternoon state persistence: variable direction = turbulent mixed day with lower Tmax; steady direction = sustained regime. *Test: direction IQR quartiles vs Tmax anomaly × month × regime.*

**WCT-WIND-009** — Calm (<5 kt) wind direction observations should be masked before computing sector share; their inclusion adds directional noise that degrades regime classification on days with mixed calm and directional obs. *Test: compare regime label consistency with and without calm-obs masking × month.*

**WCT-WIND-010** — The effective foehn sector (where Tmax anomaly peaks for NW-sector wind) is narrower than 270–045°; the peak sector is likely 340–030° (N–NNE), consistent with Tararua/Rimutaka orographic descent. *Test: Tmax anomaly by 10° bins for winds in 270–045° × month.*

**WCT-WIND-011** — W sector (260–280°) wind crossing cold Cook Strait waters is a neutral-to-cooling flow sector, not a warming sector; including it in the NW arc inflates foehn score for maritime W flow. *Test: Tmax anomaly for 260–280° vs 280–310° vs 310–045° × month.*

**WCT-WIND-012** — Wind speed acceleration during the morning window (strengthening by CP vs weakening by CP) predicts afternoon wind state continuation; strengthening NW by CP23 = continued warming; weakening = decay before Tmax. *Test: speed trend direction flag vs post-CP Tmax timing × month (leakage warning: Tmax timing is ex-post).*

**WCT-WIND-013** — SE/E winds (090–160°) suppress Tmax without triggering southerly_disrupted (since they are outside the 135–225° southerly sector); these days may be a hidden suppression class. *Test: Tmax anomaly for SE/E sector days vs climatology × month; quantify frequency.*

**WCT-WIND-014** — Wind vector components (u = zonal, v = meridional) as continuous predictors may outperform discrete sector bins in ML models; the circular discontinuity at 0°/360° makes sector bins noisy at boundaries. *Test: ML model comparison with sector features vs (u, v) features × CP × month.*

**WCT-WIND-015** — Post-southerly recovery direction (N via anticlockwise through W) has a different warming trajectory than direct NW recovery; the path of recovery encodes the synoptic driver. *Test: classify recovery path (anticlockwise vs direct NW); compare post-recovery Tmax anomaly × month.*

**WCT-WIND-016** — The Cook Strait channeling effect amplifies airport NW/N speeds relative to regional open-country wind; speed thresholds calibrated at the airport are not portable to regional models without a site correction factor. *Test: document speed distribution by direction at NZWN; compare to available nearby stations (blocked if no secondary station data).*

**WCT-WIND-017** — By month, the sweet-spot NW speed (producing maximum positive Tmax anomaly) shifts; summer may require higher speeds for the same anomaly because sea breeze competes. *Test: Tmax anomaly by speed bin × month for NW sector; find optimal speed by month.*

**WCT-WIND-018** — Northerly gust factor (max/mean speed) in the morning window correlates with foehn intensity; gustier mornings suggest stronger and more pulsed NW flow that may peak earlier and drop more sharply. *Test: gust factor vs tmax_hour and Tmax anomaly × month.*

**WCT-WIND-019** — Count of southerly-sector obs by CP (0, 1, 2, 3, 4+) predicts remaining cooling potential more reliably than the binary southerly_share ≥ 0.5; the count is a continuous depth measure. *Test: southerly obs count vs remaining_warming × CP × month.*

**WCT-WIND-020** — NE–E sector (030–090°) suppresses Tmax by importing moist Pacific marine air; this mechanism has not been independently tested from data. *Test: Tmax anomaly for all NE/E sector days × month; compare to N/NW and S distributions.*

---

### FOEHN_DRYING Domain (15 theses)

**WCT-FOEHN-001** through **WCT-FOEHN-015** — *See compact entries in registry above. Domain report should expand: (1) foehn_score decomposition into speed-driven vs dryness-driven; (2) month-calibrated threshold analysis; (3) dewpoint collapse rate by season; (4) foehn collapse timing and its effect on Tmax; (5) false foehn sector analysis; (6) multi-day foehn Tmax trajectory; (7) pre-foehn cloud burn-off signature; (8) NW/W sector false foehn; (9) summer superadditive vs winter dominant contribution; (10) foehn-suppressed cloud mechanism; (11) dewpoint×sector interaction; (12) CP23 detectability advantage; (13) adiabatic descent QNH proxy; (14) foehn end and dewpoint recovery; (15) Protocol-14 warming ratio test by month.*

---

### RAIN_CLEARING Domain (15 theses)

**WCT-RAIN-001** through **WCT-RAIN-015** — *See compact entries in registry above. Domain report should expand: (1) rain timing window effect on Tmax suppression; (2) clearing rate as late-spike predictor; (3) D-1 soil moisture proxy; (4) orographic drizzle vs frontal rain discrimination; (5) pre-frontal NW rain vs post-frontal southerly rain; (6) month-dependent recovery speed; (7) heavy-rain + rapid clearing late-warming signature; (8) 3-day cumulative precip as soil proxy; (9) post-frontal clearing window duration by month; (10) morning rain / afternoon clear underforecasting; (11) NW orographic airport rain pattern; (12) sequential rain events; (13) historical clearing probability from pressure rise rate; (14) thermal recovery rate threshold; (15) post-clearing Tmax overshoot by season.*

---

### CLOUD Domain (15 theses)

**WCT-CLOUD-001** through **WCT-CLOUD-015** — *See compact entries in registry above. Domain report should expand: (1) cloud base height suppression scaling; (2) seasonal cloud base climatology; (3) cloud trajectory vs cloud state at CP; (4) H23 month-stratified re-test; (5) fog burn-off warming trajectory; (6) SCT/BKN base height air mass stability encoding; (7) high cloud vs winter solar angle; (8) clear-sky Tmax driven by wind not cloud; (9) mixed cloud day timing delay; (10) cloud persistence rate by month/regime; (11) orographic cloud airport shadow; (12) multi-layer cloud persistent suppression; (13) cloud base height trend; (14) summer convective cloud risk; (15) CB convective cap effect.*

---

### PRESSURE Domain (12 theses)

**WCT-PRES-001** through **WCT-PRES-012** — *See compact entries in registry above. Domain report should expand: (1) tide-corrected pressure trend vs raw 3h trend; (2) absolute QNH air mass encoding; (3) pressure rise rate post-frontal discriminator; (4) QNH anomaly vs absolute; (5) compound QNH-stable feature; (6) regime-specific pressure profiles; (7) 6h pre-frontal window; (8) BLOCKED Cook Strait pressure gradient; (9) high QNH in winter = stable but not high Tmax; (10) post-frontal stabilization → clearing timing; (11) QNH trend sign × wind sector interaction; (12) 12h QNH delta for synoptic discriminator.*

---

### HUMIDITY Domain (12 theses)

**WCT-HUM-001** through **WCT-HUM-012** — *See compact entries in registry above. Domain report should expand: (1) dewpoint anomaly vs absolute depression; (2) maritime cap quantification; (3) RH×T combination interpretation; (4) dewpoint trend direction as foehn development signal; (5) NW + high Td contradiction flag; (6) overnight saturation → slow warm start; (7) Td decline rate on foehn days; (8) moist vs dry southerly; (9) Td trend direction binary test; (10) seasonal Td climatology prerequisite; (11) foehn-end Td recovery rate; (12) overnight dew formation × month × regime.*

---

### TMAX_TIMING Domain (18 theses)

**WCT-TIMING-001** through **WCT-TIMING-016** — *See compact entries in registry above. Key test plan for TIMING-001 (prerequisite): produce a 12 × 4 table of q10/q25/q50/q75/q90 tmax_hour by (month, regime), flag cells with n < 30, and publish as a mandatory artifact before any other TIMING thesis proceeds.*

**WCT-TIMING-017** — By month, the within-day Tmax timing distribution is approximately unimodal in summer and bimodal (polarized between clear early-peak and cloudy/late-peak days) in winter. *Test: fit distribution models by month; compute bimodality coefficient; document modality by month.*

**WCT-TIMING-018** — expected_remaining_warming_time = q50_train(tmax_hour | month, regime) − CP_hour provides a direct timing runway estimate that reformulates H2 correctly. *Test: compute this feature using train-only priors; test effect size at each CP × month × regime.*

---

### LATE_SPIKE Domain (18 theses)

**WCT-SPIKE-001** through **WCT-SPIKE-018** — *See compact entries in registry above. Critical prerequisite: WCT-TIMING-001 table must exist before any SPIKE thesis can be tested. SPIKE-001 must be resolved first because it defines the threshold for all other SPIKE theses.*

*Key test plan for SPIKE-001: For each (month, regime) cell, compute q90_train(tmax_hour) on training windows only. Compare the resulting threshold to the static 17:00 rule. Quantify how many historical events would be reclassified. Document the resulting late_tmax_event rate per (month, regime) cell.*

---

### CP_LEAD_TIME Domain (8 theses)

**WCT-CP-001** through **WCT-CP-008** — *See compact entries in registry above. Domain report structure: (1) feature maturation curve from CP20 to CP23 by feature and month; (2) CP-specific validation table; (3) sunrise hour by month and its relationship to CP regime stability; (4) G4 flag audit for causal purity; (5) information gain by CP step × month; (6) 3-obs minimum effect on CP20 in winter; (7) near-boundary CP sensitivity test; (8) MAE vs CP lead time curve by month.*

---

### DATA_QUALITY Domain (8 theses)

**WCT-DQ-001** through **WCT-DQ-008** — *See compact entries in registry above. Domain report: (1) temperature rounding sensitivity analysis; (2) wind direction discretization boundary test; (3) p01i light rain gap documentation; (4) morning window gap frequency by hour × month; (5) DST transition day flagging; (6) calm direction missing value handling; (7) day_complete audit for selection bias; (8) SPECI density by hour × month.*

---

## GAP Domain — 50 Theses (Full Expansions)

### WCT-GAP-001
**Claim:** No cooling mechanism taxonomy exists; the classifier cannot be properly repaired until the 4+ physical types of cooling currently captured by the −2 C/h rule are formally classified and their Tmax distributions documented.

**Physical rationale:** The 2026-06-06 trigger audit showed 94.6% of southerly_disrupted rows are cooling-triggered. Without knowing whether that cooling is (A) radiative, (B) frontal, (C) post-frontal, or (D) rain-evaporative, any classifier repair is guesswork.

**Observable evidence:** Cooling trigger flag, cooling hour, wind sector during cooling, cloud codes, precip, dewpoint trend.

**Causal availability:** All features are pre-CP.

**Target relation:** southerly_disrupted sub-type composition, regime classifier repair path.

**Strata:** month, cooling type.

**Test plan:** Build a cooling event taxonomy using decision rules on (cooling hour, wind sector, precipitation, dewpoint trend). Assign each southerly_disrupted cooling-trigger row to a cooling type. Compute Tmax distributions per type per month.

**Leakage risk:** None — all discriminators are pre-CP.

**Status:** E0_candidate

---

### WCT-GAP-002
**Claim:** No monthly wind rose has been produced for NZWN; every wind sector thesis in this atlas is implicitly averaging across months with materially different wind climatologies.

**Physical rationale:** Wellington's wind regime shifts with season: more southerlies in winter, more N/NW in spring and autumn, more variable in summer. Without documenting these seasonal shifts, any wind sector finding is a seasonal average that may not apply to any specific month.

**Observable evidence:** `wind_dir_deg`, `sknt`, month.

**Causal availability:** Fully causal — wind observations are pre-CP.

**Target relation:** All WIND, FOEHN, REGIME, and TIMING theses.

**Strata:** month (1–12).

**Test plan:** Compute 12 monthly wind roses from obs.parquet. For each month: direction frequency by 10° bin, mean speed by direction sector, dominant sector identification. Publish as a mandatory artifact.

**Leakage risk:** None.

**Status:** E0_candidate

---

### WCT-GAP-003
**Claim:** No `tmax_hour` distribution table by month × regime exists; this table is the mandatory prior for all TIMING and SPIKE domain theses.

**Physical rationale:** The late Tmax definition in ADR-011 is `tmax_hour > q90_train(tmax_hour | month, regime)`. This formula cannot be operationalized without first computing the conditional distribution. All threshold decisions are circular until this table exists.

**Observable evidence:** `tmax_hour` (labels.parquet), `regime_label` (features.parquet), `date_local` month.

**Causal availability:** `tmax_hour` is a full-day outcome — it is an evaluation target, NOT a CP feature. The distribution table is a train-only prior.

**Target relation:** late_tmax_event definition, all TIMING/SPIKE theses.

**Strata:** month (1–12), regime (4 labels).

**Test plan:**
1. Join labels and features on date_local.
2. For each (month, regime) cell: compute q10/q25/q50/q75/q90 of tmax_hour.
3. Count n per cell; flag n < 30 as underpowered.
4. Compute the deviation of each cell's q90 from the static 17:00 rule.
5. Publish as mandatory atlas prerequisite artifact.

**Leakage risk:** Use train-only windows inside walk-forward loop for operational use. Full-dataset table is for atlas documentation only and must not be used as a model feature.

**Status:** E0_candidate

---

### WCT-GAP-004
**Claim:** There is no systematic catalog of "clear sky + below-average Tmax" events; the hypothesis that these days exist (WCT-CLOUD-008) is currently unverifiable without an enumerated event list.

**Physical rationale:** Sunny days can produce below-average Tmax through: cold advection, maritime cap, previous-day effects. These days are the most misleading for casual analysis (no cloud, yet cold). Understanding their mechanism is critical for calibrating the cloud-cover suppression feature.

**Observable evidence:** Sky condition codes (SKC/FEW), `tmax_int`, DOY climatology baseline.

**Causal availability:** Cloud codes are pre-CP; Tmax is the evaluation target.

**Target relation:** cloud_cover_suppression feature calibration, regime misclassification.

**Strata:** month, Tmax anomaly threshold (e.g., Tmax < p25 for the month).

**Test plan:**
1. Filter for: sky condition = SKC or FEW at all CP observations, day_complete = True, Tmax anomaly < −2 C.
2. Catalog these events by month and wind sector.
3. Compute their regime distribution (are they mainly calm_radiative? standard_nw?).
4. Identify the wind sector at CP for these events.
5. Propose the physical mechanism for each identified group.

**Leakage risk:** Tmax anomaly is ex-post (evaluation). Cloud at CP is causal.

**Status:** E0_candidate

---

### WCT-GAP-005
**Claim:** No regime transition probability matrix (Markov structure) has been computed; the conditional probability P(D-0 regime | D-1 regime, month) is a fundamental prior for all sequential prediction approaches.

*Compact — see WCT-REGIME-005 for full expansion. This gap registers the MISSING ARTIFACT, not the thesis concept. The artifact must be produced before WCT-REGIME-005 can be tested.*

**Test plan:** Build 4×4 transition matrices per month from features.parquet. Compute Shannon entropy of transition rows. Identify highest-information transitions. Publish matrix as atlas artifact.

**Status:** E0_candidate

---

### WCT-GAP-006
**Claim:** No post-frontal recovery time study exists; the median hours from frontal passage to Tmax by month is the core independent variable for late Tmax prediction on southerly_disrupted recovery days.

**Physical rationale:** The post-frontal period (pressure rising, wind backing NW, skies clearing) has a characteristic duration that varies by season and frontal speed. Without knowing this distribution by month, the late-spike risk for southerly recovery days cannot be quantified.

**Observable evidence:** Pressure rise onset (proxy for frontal passage), final tmax_hour (ex-post evaluation).

**Causal availability:** Pressure trend is pre-CP. Frontal passage timing and tmax_hour are ex-post.

**Target relation:** tmax_hour on southerly recovery days, late spike probability.

**Strata:** month, frontal passage hour (where detectable).

**Test plan:**
1. For southerly_disrupted rows: identify pressure turning-point hour as frontal passage proxy.
2. Compute (tmax_hour − frontal_passage_hour) by month.
3. Compute mean, P25, P75 of this recovery lag by month.
4. Plot distribution of recovery lags by month.

**Leakage risk:** Frontal passage time must be estimated from pre-CP pressure observations only. tmax_hour is evaluation only.

**Status:** E0_candidate

---

### WCT-GAP-007
**Claim:** METAR reporting gap frequency by hour of day has not been audited; missing observations are not random and may cluster at specific hours (e.g., early morning) with direct impact on feature quality.

**Test plan:** Compute hourly observation count vs expected hourly count by month and year. Identify hours with systematically lower obs. Cross-reference with feature computation windows to identify which features are most affected by gaps.

**Status:** E0_candidate

---

### WCT-GAP-008
**Claim:** The foehn_score threshold of 60 is uncalibrated by month; the optimal threshold that separates Tmax anomaly > +3 C events must be derived from data separately for each month.

**Test plan:** For each month, compute median Tmax anomaly by foehn_score bin (0–10, 10–20, ..., 80+). Identify the bin above which the median anomaly is > +3 C. Compare the empirical threshold to 60 with 95% bootstrap CI.

**Status:** E0_candidate

---

### WCT-GAP-009
**Claim:** No clear-sky radiation proxy exists in the feature set; a calculated potential solar radiation (function of DOY, latitude, and cloud attenuation) would be a more physically grounded suppression measure than the binary cloud cover code.

**Physical rationale:** Clear-sky potential radiation at NZWN (latitude −41.3°) varies from approximately 550 W/m² at summer solstice to 200 W/m² at winter solstice at solar noon. Cloud attenuation scales with cloud fraction and base height. The current cloud_cover_suppression feature uses okta codes as a rough proxy.

**Test plan:** Compute clear-sky potential radiation by DOY × hour. Apply cloud attenuation scaling by okta and base height. Correlate the resulting daily integrated radiation estimate with Tmax anomaly × month × regime. Compare effect size to cloud_cover_suppression (H12) by month.

**Status:** E0_candidate

---

### WCT-GAP-010
**Claim:** No multi-day heat event characterization has been produced; Wellington's rare but significant 3+ day above-normal temperature events have distinct precondition patterns.

**Test plan:** Define heat event as 3+ consecutive days with Tmax > p75 for that DOY. Catalog all events in the dataset. Document regime sequences during events. Compute regime transition patterns within events. Test whether events start preferentially in specific months and with specific D-1 synoptic patterns.

**Status:** E0_candidate

---

### WCT-GAP-011
**Claim:** The H6 validated feature (tmin_delta_tmax) masks sub-group structure; the Tmin–Tmax correlation by month and regime should be decomposed to reveal: (A) high Tmin + high Tmax (maritime warm air mass), (B) low Tmin + high Tmax (foehn day with clear night), (C) low Tmin + low Tmax (cold clear winter day).

**Test plan:** Compute (Tmin, Tmax) scatter by (month, regime). Test whether the correlation structure differs by regime × month. Identify distinct sub-clusters within the validated H6 effect.

**Status:** E0_candidate

---

### WCT-GAP-012
**Claim:** No catalog of intraday temperature reversals (≥2 C mid-day temperature drop followed by recovery ≥1 C) exists; these events are a primary source of double-peak days and a specific late-spike mechanism.

**Test plan:** Scan intraday temperature profiles for: local minimum between 11:00 and 15:00 with preceding decrease ≥2 C and subsequent recovery ≥1 C. Catalog these events by month and regime. Quantify their frequency and final Tmax anomaly.

**Leakage risk:** Intraday profile analysis is ex-post; use only for evaluation and historical catalog, not as a CP feature.

**Status:** E0_candidate

---

### WCT-GAP-013
**Claim:** H8 (wind_dir_change_S_to_N) was rejected as coded; the circular directional algebra used to compute the direction change may have been incorrect (e.g., ignoring the 360°/0° boundary); the direction rotation ORDER (S→SW→W→NW = recovery vs NW→W→S = frontal approach) has never been tested with proper circular statistics.

**Test plan:** Recompute wind rotation direction using circular statistics (sign of the cross product of consecutive direction vectors). Classify morning window as backing (CW rotation) or veering (CCW rotation). Test Tmax anomaly vs rotation direction × month. Compare to H8's original effect size.

**Status:** E0_candidate

---

### WCT-GAP-014
**Claim:** The Cook Strait channeling speed amplification at NZWN has not been quantified; airport wind speed may systematically overrepresent the regional NW flow strength at specific channel-aligned directions.

**Physical rationale:** Wellington Airport is in the narrowest part of Cook Strait. The Venturi effect of terrain channeling can amplify wind speeds by 20–50% above the free-stream regional speed. Speed thresholds calibrated from NZWN may not apply to NWP model grid-point speeds without a correction factor.

**Test plan:** BLOCKED unless secondary station data (e.g., Wellington Kelburn or satellite wind retrieval) is available. Document as blocked thesis with external data requirement.

**Status:** E0_candidate (BLOCKED — requires secondary station data)

---

### WCT-GAP-015
**Claim:** Cloud base height trend during the morning (rising = improving conditions, falling = deteriorating) predicts afternoon cloud state better than the instantaneous base height at CP; this trajectory feature is absent from the H1–H23 catalog.

**Test plan:** Compute cloud base height linear trend over the CP observation window. Test whether positive base height trend correlates with: (a) lower cloud cover suppression at Tmax hour (ex-post evaluation), (b) earlier clearing, (c) higher Tmax anomaly. Stratify by month and regime.

**Status:** E0_candidate

---

### WCT-GAP-016
**Claim:** The distributional baseline — P10/P50/P90 of remaining_warming by (regime, month, CP) — has never been documented; this distribution is the fundamental denominator for interpreting any feature's effect size.

**Test plan:** From features.parquet + labels.parquet: compute remaining_warming = tmax_int − tmp_c_int_at_CP for each (regime, month, CP). Tabulate P10/P25/P50/P75/P90. Identify cells with high spread (unpredictable) vs low spread (highly predictable). Publish as mandatory atlas artifact.

**Status:** E0_candidate

---

### WCT-GAP-017
**Claim:** The distribution of Tmax anomaly (Tmax minus DOY climatology) by month has not been analyzed; basic statistics (mean, variance, skewness, kurtosis) and tail behavior are undocumented.

**Test plan:** Compute Tmax anomaly for all day_complete=True days. By month, compute: mean, std, P5/P95, skewness, kurtosis. Test normality (Shapiro-Wilk). Plot anomaly distribution by month. Document evidence of non-normality and identify the cause (bimodal? Heavy tail?).

**Status:** E0_candidate

---

### WCT-GAP-018
**Claim:** No systematic fog occurrence analysis exists; fog presence (very low cloud base with FG or MIFG METAR code or ceiling < 300 ft) changes the morning warming trajectory fundamentally and has not been analyzed separately from low cloud.

**Test plan:** Extract fog-condition days (METAR present weather codes BR, FG, MIFG or visibility < 1000 m or cloud base < 300 ft). Compute fog frequency by month. Compute Tmax anomaly on fog days. Compare warming rate before and after fog lifts. Stratify by NW wind flag (fog burning off under NW is faster than under S flow).

**Status:** E0_candidate

---

### WCT-GAP-019
**Claim:** H3 (regime_label) was validated only pooled across all regimes at CP23; per-regime predictive performance of the label has not been evaluated; certain regimes (strong_nw_foehn) may carry strong signal while others (calm_radiative, n=625) are underpowered.

**Test plan:** Re-run H3 validation separately per regime (regime = southerly_disrupted, standard_nw, strong_nw_foehn, calm_radiative). Document effect size, CI, and sample size for each regime × CP cell. Flag underpowered cells (n < 50 days).

**Status:** E0_candidate

---

### WCT-GAP-020
**Claim:** No sensitivity analysis of the −2 C/h cooling threshold has been performed; the southerly_disrupted population at −1.5 C/h and −2.5 C/h has not been compared; the threshold-Tmax outcome relationship is undocumented.

**Test plan:** Re-run the regime classifier simulation with thresholds at −1.0, −1.5, −2.0, −2.5, −3.0 C/h. For each threshold, compute: southerly_disrupted count, mean Tmax anomaly within the class, and fraction of cooling-trigger rows with no southerly wind. Identify the threshold that minimizes within-class Tmax variance by month.

**Status:** E0_candidate

---

### WCT-GAP-021
**Claim:** H21 (pre-frontal warming window) was rejected without root-cause analysis; it is unknown whether the feature was poorly constructed or the physical phenomenon is absent in Wellington data.

**Test plan:** Identify days where: QNH falling >0.5 hPa/h AND no precipitation AND N/NW wind present. Count these days. Compute Tmax anomaly for these days × month. Compare to all NW days of the same month. If Tmax anomaly on pre-frontal window days is NOT higher than NW-all, the phenomenon is absent in data. If it IS higher but the H21 feature shows no effect, the feature construction was wrong.

**Status:** E0_candidate

---

### WCT-GAP-022
**Claim:** No analysis of precipitation type (frontal vs convective) exists; these types have different duration, intensity, and post-event clearing characteristics that affect Tmax differently.

**Test plan:** Frontal precipitation proxy: rain + southerly wind + pressure drop. Convective precipitation proxy: rain + summer (Dec–Feb) + relatively high temperature + NW or calm. Classify p01i rain events by type. Compare post-rain clearing speed and Tmax recovery by type × month.

**Status:** E0_candidate

---

### WCT-GAP-023
**Claim:** No wind direction uncertainty analysis exists; days where wind direction alternates between two sectors in adjacent observations (e.g., 160° then 280° then 170°) should be flagged as "directionally ambiguous" and their effect on regime classification documented.

**Test plan:** For each day's morning window: compute the interquartile range and standard deviation of wind direction (using circular statistics). Flag days with direction IQR > 60° as "directionally ambiguous." Compute regime classification stability (how often does adding/removing one obs change the regime?) for ambiguous vs non-ambiguous days by month.

**Status:** E0_candidate

---

### WCT-GAP-024
**Claim:** ENSO/IOD effects on Wellington Tmax are not registered in the thesis atlas; interannual Tmax variability partly explained by ENSO phase may create multi-year drift in feature-Tmax relationships.

**Physical rationale:** El Niño tends to bring more NW flow and warmer-than-average temperatures to New Zealand. La Niña brings more southerlies and cooler anomalies. This creates a multi-year cycle that could shift the regime frequency distribution and the conditional Tmax distributions.

**Observable evidence:** Requires ENSO index (MEI, ONI, or SOI). BLOCKED until external data is available.

**Status:** E0_candidate (BLOCKED — requires external ENSO index data)

---

### WCT-GAP-025
**Claim:** No physical Tmax ceiling study has been conducted for NZWN; upper bounds on Tmax by month and regime (SST cap for maritime flow, mixing cap for strong wind, solar cap for winter) are undocumented.

**Test plan:** For each (month, regime) cell: compute P95 and P99 of observed Tmax. Identify the mechanism that plausibly creates the ceiling: for southerly = SST cap (requires SST data, BLOCKED); for NW foehn = mixing cap at high speed (testable with speed data); for calm = solar cap (testable from DOY × cloud). Document the nature of each ceiling.

**Status:** E0_candidate (partially BLOCKED for SST cap)

---

### WCT-GAP-026
**Claim:** No observation count effect analysis has been performed; features computed from windows with 2–4 observations have higher noise than those from 8–10 observation windows; this heteroskedasticity affects feature reliability estimates.

**Test plan:** Compute the number of valid observations per CP window by day. Group days by obs count bucket (2–3, 4–5, 6–7, 8+). Compute feature noise (feature value variance for days with similar regime/month) by obs count bucket. Test whether effect sizes on validated features are lower in sparse-obs windows.

**Status:** E0_candidate

---

### WCT-GAP-027
**Claim:** No catalog of "near-miss southerlies" (brief southerly surge → quick recovery, morning classified as southerly_disrupted but Tmax near-normal) has been produced; these days are likely the most under-predicted group in the current model.

**Test plan:** Filter southerly_disrupted days. Apply: southerly duration < 3 hours AND pressure trend turns positive within the window AND temperature recovery > 1 C/h before CP. Compute Tmax anomaly for this sub-set. Compare to all southerly_disrupted. Quantify model error on these days specifically.

**Status:** E0_candidate

---

### WCT-GAP-028
**Claim:** The Onda 4 R2 block has not been analyzed by month; the dead regime failures for calm_radiative and standard_nw may be concentrated in specific months with sparse data, not universal across all months.

**Test plan:** Re-run Onda 4 R2 check separately for each month. Identify the months where calm_radiative and standard_nw have no passing feature. Test whether the failure is due to small n (underpowered segment) or genuine lack of predictive signal.

**Status:** E0_candidate

---

### WCT-GAP-029
**Claim:** D-1 regime type (not D-1 Tmax value) has not been tested as a predictor of D-0 Tmax; H5 (D-1 Tmax value) was rejected, but the regime sequence (D-1 = strong_nw_foehn → D-0 = calm_radiative) may carry signal that the scalar temperature missed.

**Test plan:** Create D-1 regime feature (causal: D-1 pre-CP regime label). Interact with D-0 CP regime. Test effect size of the D-1 regime × D-0 regime cell on remaining_warming × month. Compare to H5 (D-1 Tmax scalar) effect size.

**Status:** E0_candidate

---

### WCT-GAP-030
**Claim:** No sea breeze onset timing distribution has been documented; the afternoon SSE wind shift that caps Tmax on summer days is a recurring but unstudied phenomenon.

**Test plan:** For summer months (Nov–Mar), identify days with afternoon wind direction shift from N/NW to S/SE between 13:00 and 17:00 with speed increase > 5 kt. Compute onset time distribution. Correlate onset time with final Tmax. Test whether earlier sea breeze onset is associated with lower Tmax. Stratify by morning NW flow strength.

**Leakage risk:** Sea breeze onset time is ex-post (afternoon observation). Use for evaluation and historical prior development only.

**Status:** E0_candidate

---

### WCT-GAP-031
**Claim:** No analysis of convective days (summer afternoon thunderstorm → convective inhibition → Tmax cap) exists for NZWN; convective initiation limits Tmax by vertical mixing and cloud shading in ways that morning obs cannot predict directly.

**Test plan:** BLOCKED unless convective activity proxy (lightning strike density, radiosonde instability index, or NWP CAPE) is available. Register as blocked thesis with external data requirement (radiosonde or model instability index).

**Status:** E0_candidate (BLOCKED — requires upper-air or CAPE data)

---

### WCT-GAP-032
**Claim:** No warming trajectory shape analysis has been performed; deviations from the expected sinusoidal warming shape (foehn onset = early steep rise, cloud interruption = plateau, clearing = late steep rise) are informative but uncaptured.

**Test plan:** Fit a sinusoidal model to the daily temperature profile. Compute residuals by hour. Define shape features: early-onset deviation (T06–T09 above model), mid-day plateau (residuals near zero from 10:00–13:00), late-rise deviation (T14–T18 above model). Test each shape feature vs tmax_hour and Tmax anomaly × month.

**Leakage risk:** Shape features derived from intraday obs past CP are ex-post. Pre-CP shape features (using only CP-window obs) are causal.

**Status:** E0_candidate

---

### WCT-GAP-033
**Claim:** No anticyclone age effect study exists; day 2 and day 3 of a multi-day anticyclone may have different Tmax than day 1 due to progressive boundary layer drying and changing wind patterns.

**Test plan:** Define anticyclone persistence: QNH > 1018 for 2+ consecutive days. For each day within a persistent anticyclone event, record the sequence position (day 1, 2, 3, 4+). Compute Tmax anomaly by sequence position × month. Test whether later days show higher or lower Tmax than day 1.

**Status:** E0_candidate

---

### WCT-GAP-034
**Claim:** Wellington Tmax percentile climatology (P5/P25/P50/P75/P95 by month) is available from ADR-008 but has not been used for EDA stratification; anomaly contextualization requires these as denominators for all threshold analyses.

**Test plan:** Extract monthly percentile table from the existing climatology baseline. Add P5/P25/P75/P95 to all EDA anomaly plots. Use them to define "extreme", "warm", "near-normal", and "cool" strata for stratified analysis.

**Status:** E0_candidate

---

### WCT-GAP-035
**Claim:** CP22 (22:00 local) is rarely studied or validated independently; whether it adds information over CP21 is unanswered, despite being one of the four settlement checkpoints.

**Test plan:** For each validated feature (H1, H6, H10, H12, H17, H20, H23), compare effect size at CP22 vs CP21. Test whether CP22 effect size is within CI of CP21, or whether the additional hour adds independent signal in any month or regime. Document explicitly.

**Status:** E0_candidate

---

### WCT-GAP-036
**Claim:** No analysis of hourly temperature profile DURING precipitation has been performed; the evaporative cooling signature (temperature drop pattern while rain falls vs temperature before and after) carries information about rain intensity and type.

**Test plan:** For rain days, extract the temperature profile in 2-hour windows before rain onset, during rain, and after rain cessation. Compute the cooling rate during rain by month. Test whether cooling rate during rain predicts the depth of Tmax suppression. Stratify by rainfall intensity (p01i buckets).

**Leakage risk:** Rain cessation time and post-rain profile are ex-post. Only the pre-CP portion of the rain profile is causal.

**Status:** E0_candidate

---

### WCT-GAP-037
**Claim:** No systematic catalog of extreme Tmax days (top 5% per month) exists; their meteorological preconditions have not been enumerated.

**Test plan:** Identify top 5% Tmax days per month (P95 threshold). Compute regime distribution within extreme days. Compute wind sector at CP, dewpoint depression, cloud cover, QNH for extreme days. Compare to the full distribution for the same month. Identify the synoptic conditions most strongly associated with extreme Tmax.

**Status:** E0_candidate

---

### WCT-GAP-038
**Claim:** No southerly disruption duration distribution by month exists; duration (hours from southerly onset to wind backing/clearing) determines whether a morning southerly becomes a full-day event; this distribution is needed for late-spike risk estimation on southerly days.

**Test plan:** For each southerly_disrupted day, estimate: (1) southerly onset hour, (2) hour when southerly_share drops below 0.3 (backing indicator). Compute duration = (2) − (1). By month: compute P25/P50/P75 of duration. Test whether short-duration southerlies (< 4 hours) have higher Tmax than long-duration (> 8 hours) by month.

**Leakage risk:** Southerly end time (backing hour) is ex-post. Use for historical prior development only.

**Status:** E0_candidate

---

### WCT-GAP-039
**Claim:** H18 (nocturnal_plateau_flag — Tmax already past at CP) was rejected as coded (effect size 0) but the phenomenon (Tmax before CP in some months) structurally exists; the root cause of rejection was the feature construction, not the physical absence of the phenomenon.

**Test plan:** Count the number of days where `tmax_hour` < CP hour by month and regime. This is an ex-post audit. If the frequency is non-trivial (> 5%), the feature concept is important even though H18's implementation failed. Propose a revised causal proxy (e.g., temperature already declining by CP = potential past-Tmax flag).

**Status:** E0_candidate

---

### WCT-GAP-040
**Claim:** No feature importance temporal stability check has been performed; features validated in aggregate (2009–2026) may have unstable importance across early vs recent walk-forward windows due to data non-stationarity or sample size growth.

**Test plan:** Extract per-window feature effect sizes from the walk-forward results (if stored). Plot effect size of each validated feature vs window start year. Test for monotone trend (Kendall τ) and structural break. Features with significant temporal instability should be flagged.

**Status:** E0_candidate

---

### WCT-GAP-041
**Claim:** No non-stationarity test on the Wellington Tmax series (2009–2026) has been performed; climate trends, measurement equipment changes, or land use changes could create temporal drift.

**Test plan:** Compute annual mean Tmax and DOY-detrended Tmax residuals by year (2009–2026). Apply Mann-Kendall test for monotone trend. Apply Pettitt test for structural break. If significant trend exists: quantify magnitude, document potential causes, and assess impact on walk-forward feature validity.

**Status:** E0_candidate

---

### WCT-GAP-042
**Claim:** No northerly surge event detection has been implemented; a rapid wind speed increase from ~10 to ~25 kt in the NW/N sector over 2–3 hours is a specific synoptic event generating rapid Tmax increase that is not represented in any current feature.

**Test plan:** For NW/N sector days, compute wind speed increment over 2-hour windows. Flag days where increment > 12 kt within any 2-hour window. Compute Tmax anomaly for surge days × month. Compare to standard_nw and strong_nw_foehn distributions.

**Status:** E0_candidate

---

### WCT-GAP-043
**Claim:** No cloud cover persistence study during post-frontal recovery has been performed; whether cloud clears rapidly (1–2 hours) or persists (4–6 hours) after frontal passage directly determines Tmax recovery potential.

**Test plan:** For southerly_disrupted days: track cloud cover codes over time during the observation window. Compute cloud clearing rate (time from OVC/BKN to FEW/SKC). By month: compute P25/P50/P75 of clearing time. Test whether fast clearing (< 3 hours) is associated with higher Tmax than slow clearing (> 5 hours).

**Leakage risk:** Post-CP cloud clearing is ex-post. Clearing rate at and before CP is causal.

**Status:** E0_candidate

---

### WCT-GAP-044
**Claim:** Validated features H1, H6, H10, H12, H17, H20, H23 have not been tested for inter-correlation; some may be proxies for the same underlying phenomenon (e.g., H1 slope_3h and H17 warming_rate_06_09 appear structurally similar).

**Test plan:**
1. Compute pairwise Pearson and Spearman correlation among the 7 validated features × CP.
2. For highly correlated pairs (|r| > 0.7), test whether they carry independent information in a joint model.
3. Document which pairs are redundant vs complementary.
4. Identify the "minimal validated feature set" that captures most of the combined signal.

**Status:** E0_candidate

---

### WCT-GAP-045
**Claim:** No diurnal temperature range (DTR = Tmax − Tmin) analysis by month and regime has been produced; DTR encodes the integrated effect of cloud, wind, and advection and may be a stronger Tmax predictor than either component alone.

**Test plan:** Compute DTR for all day_complete days. By (month, regime): compute P10/P50/P90 of DTR. Test correlation of DTR with Tmax anomaly. Decompose: is high DTR associated with high Tmax (clear calm days) or are there exceptions (foehn days with moderate DTR but high Tmax)?

**Leakage risk:** DTR uses final Tmax (ex-post). Can only use Tmin (available pre-CP) as a predictor. Document the asymmetry.

**Status:** E0_candidate

---

### WCT-GAP-046
**Claim:** No "Wellington southerly buster" sub-type analysis has been performed; a rapid, intense southerly with sharp temperature drop (>5 C in 1 hour), sudden wind shift, and squall is a specific event type that may warrant its own southerly_disrupted sub-class.

**Physical rationale:** Southerly busters are well-documented in NZ literature. They are more intense and shorter-duration than regular southerly changes. Their Tmax suppression is deep but brief; recovery potential depends on how quickly the post-buster air mass clears.

**Observable evidence:** Maximum cooling rate (most negative delta_t_per_h), southerly onset speed, max southerly speed, pressure drop before and rise after.

**Test plan:**
1. Define buster threshold: max cooling rate < −4 C/h in a single hour AND max southerly speed > 25 kt AND pressure fall > 3 hPa followed by rise > 3 hPa in same window.
2. Identify buster days by month.
3. Compute post-buster Tmax anomaly vs standard southerly.
4. Test whether buster days have different Tmax distribution from regular southerly.

**Status:** E0_candidate

---

### WCT-GAP-047
**Claim:** No temperature inversion analysis exists for NZWN; inversion strength at dawn (proxy from near-surface Td vs T spread + wind stability) constrains morning warming amplitude; when the inversion is strong, warming is delayed until the inversion erodes.

**Physical rationale:** A surface temperature inversion (temperature increases with height in the lowest 100–200 m) is a lid on surface warming. Solar heating at the surface must overcome the inversion before warming propagates upward. Strong inversions delay the morning warming onset.

**Observable evidence:** METAR surface temperature and dewpoint (inversion proxy); wind speed (turbulent erosion proxy). Note: actual profile data (radiosonde) is BLOCKED.

**Test plan:** Proxy for inversion: T − Td < 3 C (near-saturated) + wind speed < 5 kt (stable) at 03:00–05:00. Compare morning warming rate (06:00–10:00) on inversion-proxy days vs non-inversion days × month. Document the average warming delay associated with the proxy.

**Status:** E0_candidate (direct inversion measurement BLOCKED — requires radiosonde)

---

### WCT-GAP-048
**Claim:** No sample-size power map for the full thesis atlas exists; month × regime × CP cells with n < 30 are underpowered for all statistical tests in this atlas; a mandatory cell-size audit must precede all stratified testing.

**Test plan:**
1. For each (month, regime, CP) cell in features.parquet: compute n.
2. Produce a heat map: rows = months, columns = regimes, cells = n.
3. Flag all cells with n < 30 as "underpowered."
4. Publish as mandatory atlas prerequisite; all stratified analyses must reference this map.

**Status:** E0_candidate — this is a mandatory prerequisite thesis (must be produced before all others)

---

### WCT-GAP-049
**Claim:** No systematic study of the Tararua rain shadow effect on Wellington Airport cloud observations exists; the orographic sheltering of the airport from NW-generated cloud creates site-specific cloud readings that may not represent the regional cloud field, directly affecting the reliability of all cloud-based features.

**Physical rationale:** The Tararua Range lies NE of Wellington. Under NW flow, the airport is in the rain shadow/descent zone of the range. Cloud that forms on the Tararua windward side may reduce regional sky exposure while the airport METAR shows FEW or SCT. The reverse applies under NE flow (airport may be more cloudy than the regional field suggests).

**Test plan:** Identify strong NW days (nw_share > 0.7, foehn_score > 40). Compare cloud codes on these days vs expectation for the same pressure/moisture levels on light wind days. If cloud codes are systematically lower on NW days than similar moisture days with light wind, the shadow effect is present. Quantify the bias.

**Status:** E0_candidate

---

### WCT-GAP-050
**Claim:** No joint leakage risk assessment has been performed for the combination of validated features; individual features have documented leakage risks, but the compound leakage risk of using multiple features simultaneously in a model (where information from one partially-causal feature augments another's apparent skill) has not been assessed.

**Physical rationale:** Feature interaction may allow a model to reconstruct information about the full day from multiple partially-causal features, even if no single feature leaks directly. For example, if feature A contains information about morning cloud and feature B contains information about morning wind, their combination may allow the model to infer post-CP clearing timing that neither alone would reveal.

**Test plan:**
1. For each pair of validated features: compute their joint information about remaining_warming vs each feature alone (mutual information analysis).
2. Test whether joint effect size exceeds the sum of individual effect sizes (synergistic leakage).
3. Apply the G4 (nowcast suspect) logic to the joint feature set, not just individual features.

**Status:** E0_candidate

---

## Atlas Summary Statistics

| Domain | Theses | E0_candidate | BLOCKED |
|---|---|---|---|
| REGIME | 20 | 20 | 0 |
| COOLING | 20 | 20 | 0 |
| WIND | 20 | 20 | 0 |
| FOEHN | 15 | 15 | 0 |
| RAIN | 15 | 15 | 0 |
| CLOUD | 15 | 15 | 0 |
| PRES | 12 | 11 | 1 |
| HUM | 12 | 12 | 0 |
| TIMING | 18 | 18 | 0 |
| SPIKE | 18 | 18 | 0 |
| CP | 8 | 8 | 0 |
| DQ | 8 | 8 | 0 |
| IX | 20 | 20 | 0 |
| **Subtotal** | **201** | **200** | **1** |
| GAP | 50 | 45 | 5 |
| **TOTAL** | **251** | **245** | **6** |

### BLOCKED theses (require external data)

| ID | Blocked on |
|---|---|
| WCT-PRES-008 | Secondary station pressure data for Cook Strait gradient |
| WCT-GAP-024 | ENSO/IOD index (MEI, ONI, or SOI) |
| WCT-GAP-025 | SST data for maritime cap quantification |
| WCT-GAP-031 | Radiosonde or NWP CAPE data for convective instability |
| WCT-GAP-014 | Secondary wind station for channeling calibration |
| WCT-GAP-047 | Radiosonde for direct inversion profiling |

---

## Mandatory Prerequisite Artifacts

The following artifacts must be produced before the majority of domain theses can advance from E0 to E1:

| Artifact | Required by | Produces |
|---|---|---|
| Monthly regime frequency table (12 × 4) | WCT-REGIME-019 | All REGIME, TIMING, SPIKE theses |
| Monthly wind rose (12 roses) | WCT-GAP-002 | All WIND, FOEHN, COOLING theses |
| tmax_hour distribution table by (month × regime): P10/P25/P50/P75/P90 | WCT-GAP-003 | All TIMING, SPIKE theses |
| remaining_warming distribution by (month × regime × CP): P10/P25/P50/P75/P90 | WCT-GAP-016 | Feature effect size context for all theses |
| Month × regime × CP sample size power map | WCT-GAP-048 | All stratified analyses |
| Cooling mechanism taxonomy (4 types) | WCT-GAP-001 | All COOLING theses, REGIME-020 |
| Tmax anomaly distribution by month | WCT-GAP-017 | Normality assumption for all tests |

---

## Key Methodological Rules (enforced across all theses)

1. **Late Tmax threshold is NEVER 17:00 (fixed).** It is always `q90_train(tmax_hour | month, regime)` computed on training data only inside the walk-forward loop.

2. **Every finding must be stratified by month AND regime.** An aggregate finding (regime=all, no month split) is only a weighted average and does not constitute deep understanding.

3. **Full-day outcomes (tmax_hour, tmax_int) appear only as evaluation targets, never as model features or CP evidence.** This rule is absolute and cannot be relaxed to gain predictive signal.

4. **Effect sizes must be reported with 95% bootstrapped CI and stratified by CP lead time.** An effect seen only at CP23 and not at CP20 is a different thesis from one seen at all CPs.

5. **Theses in underpowered cells (n < 30 per month × regime × CP) must be flagged; statistical conclusions from these cells carry high uncertainty.**

6. **Every thesis that passes E1 must explicitly state what it cannot tell you** (leakage risk, confounders, unavailable data at CP time).

---

*Atlas version 1.0 — Onda 2E draft — 2026-06-06*  
*Next step: produce mandatory prerequisite artifacts (7 tables above) before advancing any thesis to E1.*
