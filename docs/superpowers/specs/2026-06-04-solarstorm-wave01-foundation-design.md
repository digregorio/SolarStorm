# SolarStorm — Onda 0+1: Fundação Estatística & EDA

**Status:** spec, await review
**Date:** 2026-06-04
**Scope:** Bootstrap repo + baseline ladder + EDA-driven hypothesis catalog + walk-forward leaderboard
**DoD:** De 10+ anos de METAR, um comando produz um leaderboard walk-forward de baselines pontuado por CP/regime/janela recente, com gates congelados e um catálogo de hipóteses EDA testadas com IC.

## Contexto (por que este spec existe)

O projeto anterior (Wellington) acumulou complexidade de automação/operação sobre um centro preditivo que perdia para `dminus1` (MAE 2.32 vs 2.00, fallback marginal 92.9%, nowcaster reativo). O rebuild é **repo novo, port cirúrgico** — preserva módulos-fundação com evidência quantitativa (ingestão METAR, labels Tmax/CP, harness walk-forward, contratos causais, climatologia, NWP/LGBM/Ridge para Onda 3) e reconstrói o centro preditivo como **NWP-residual-first, probabilístico, guiado por baseline ladder**.

**Onda 0+1 é a fundação.** Ela entrega o leaderboard que julga tudo que vier depois. Sem ela, repetimos a falha de construir sobre areia.

---

## 1. Quatro princípios fundacionais (regem todo o rebuild)

### P1 — Decimal-até-o-último-momento
Internamente tudo opera em espaço decimal. O arredondamento para inteiro (bracket Polymarket) e a feature `risco_de_flip` (distância à fronteira ×.5°C) são aplicados **apenas na camada de output financeiro**. Scores conformais e métricas de erro são contínuos. Isto resolve a tensão "target inteiro vs calibração decimal" e implementa o princípio "never discretize before the last moment" da literatura.

### P2 — Zero hardcoded meteorológico
Horário de Tmax, regimes, janelas: tudo provado por EDA e expresso como distribuição ou intervalo com IC. A **única exceção** são constantes contratuais: CPs de mercado, regras de settlement Polymarket, fuso horário NZST. `tmax=12h` é proibido; só entra se EDA por mês×regime provar.

### P3 — Todo achado é hipótese gated
EDA gera hipóteses H1..Hn. Cada uma roda através do harness walk-forward e devolve efeito + IC bootstrap + pass/fail contra best-null por CP. Só integra no modelo se bater o melhor baseline disponível. Anti-cosmético por construção.

### P4 — Foco financeiro no bracket
A métrica de verdade é o bracket inteiro que o Polymarket settla. 0.1°C cruza fronteira de 1°C inteiro. Incerteza alta → `stay_out`. O sistema pode (e deve) ficar fora do mercado; não pode fingir edge.

### P5 — Documentação como produto primário
Toda onda entrega documentação versionada junto com o código — não como afterthought. O projeto anterior era ruim em tudo, mas documentou tão bem as próprias falhas que a auditoria forense foi possível sem re-executar nada. Esse é o **piso**: relatórios de baseline/hipótese são gerados e commitados automaticamente pelo CLI; CHANGELOG é atualizado a cada merge; decisões de design (como este spec) vivem em `docs/specs/`; hipóteses que falham são documentadas com o mesmo rigor das que passam — failures são ativos de conhecimento. Nenhum resultado de leaderboard ou teste de hipótese existe apenas em stdout; tudo produz artefato versionado.

---

## 2. Estrutura do repo

```
solarstorm/
  __init__.py
  __main__.py              # CLI: tmax ingest | baselines | leaderboard | eda
  _contracts.py            # P1+P2 firewall causal + constantes contratuais
  _config.py               # centraliza paths, constantes contratuais, seed
  data/
    __init__.py
    _metar.py              # [PORT] parsing integer-truth do METAR cru + cross-check tmpf
    _labels.py             # [PORT+EXT] Tmax/dia, CPs (20-23Z, op=23Z), k_cp, remaining_warming
    _calendar.py           # [PORT] dia-local NZST, DST, definição de CP contratual
    _iem.py                # [NOVO] cliente IEM ASOS para backfill 10+ anos NZWN
    _settlement.py         # [NOVO] P4: rounding contratual, risco_de_flip, bracket mapping
  baselines/
    __init__.py
    _persistence.py        # [NOVO] t_so_far, dminus1, mean_so_far_by_hour
    _climatology.py        # [PORT+EXT] DOY-smoothed, CP×mês, Tmax-hour×mês×regime
    _empirical.py          # [PORT, rebaixado] residual condicional — apenas baseline, nunca produção
    _ladder.py             # [NOVO] orquestra degraus + best-null-por-CP
  eval/
    __init__.py
    _walkforward.py        # [PORT+EXT] splits expansivos, holdouts recentes (7/14/30d, 2026-04-01+)
    _metrics.py            # [PORT+EXT] MAE/RMSE/bias, CRPS/RPS/Brier, bracket, reliability/ECE/PIT
    _segments.py           # [NOVO] slicing por CP, regime, janela, gap natural
    _gates.py              # [NOVO] gates congelados (G1-G5) + juiz best-null-por-CP
    _leaderboard.py        # [NOVO] placar permanente — o artefato de saída
    _bootstrap.py          # [NOVO] CIs via bootstrap pareado por CP
  eda/
    __init__.py
    _regimes.py            # [NOVO] classificador heurístico calm/transition/late-warming/foehn
    _hypotheses.py         # [NOVO] registro H1..Hn + runner gated por walk-forward
    _catalog.py            # [NOVO] catálogo de features candidatas com fonte e veredito EDA
tests/
  conftest.py              # fixtures METAR sintéticas (calmo, late-warming, dado faltante)
  test_causal_firewall.py  # P1+P2: closed='left' levanta exceção com timestamp futuro
  test_baselines.py        # persistence, climatology reproduzem valores esperados
  test_ladder.py           # best-null-por-CP, líder correto por segmento
  test_metrics.py          # CRPS/RPS/Brier em distribuições de resultado conhecido
  test_gates.py            # G1-G5: null não batido mata, fallback gera NOT_OPERATIONAL, corr_diff detecta nowcast
notebooks/
  00_metar_sanity.ipynb    # [EDA-relâmpago] cobertura, missingness, distribuição por CP
  01_regime_explore.ipynb  # [EDA-relâmpago] taxonomia de dias, transições intradiárias
  02_tmax_hour.ipynb       # [EDA-relâmpago] hora de Tmax por mês×regime (P2)
  03_baseline_leaderboard.ipynb  # [EDA-relâmpago] visualização do leaderboard
reports/
  leaderboard/             # gerado: JSON+MD do leaderboard por data
  hypotheses/              # gerado: relatório H1..Hn com efeito + IC + pass/fail
docs/
  specs/                   # specs de design de cada onda (este documento e futuros)
  decisions/               # registros de decisão de arquitetura (ADR) datados
CHANGELOG.md               # atualizado a cada merge; uma linha por mudança significativa
README.md                  # visão geral, instalação, uso rápido, link para specs
```

> Convenção: módulos internos com underscore prefix (`_metar.py`) indicam API não-estável; re-exportados publicamente em `__init__.py` se necessário.

---

## 3. Componentes e decisões-chave

### 3.1 Ingestão METAR — Onda 0

- **Fonte histórica:** IEM ASOS (Iowa Environmental Mesonet) — dados NZWN desde ~2009, cobertura consistente.
- **Fonte live (backlog Onda 4):** Aviation Weather API, cadência ~30 min.
- **Parsing integer-truth:** regex sobre texto METAR cru (`T01270134` → 12.7°C), não `tmpf` arredondado. Cross-check com `tmpf` e registro de divergência. Isto é crítico para settlement Polymarket (o contrato settlement usa o inteiro do METAR, mas internamente precisamos do decimal para evitar viés de arredondamento cumulativo — P1).
- **Scan 24h obrigatório:** verificar se há Tmax em hora atípica — definido como Tmax ocorrendo fora de 06Z-06Z+1 do dia local (i.e., entre 00Z-06Z ou após 06Z+1). Registra `tmax_hour` e flag `tmax_atypical_hour` para auditoria. Dias com Tmax na madrugada ou跨越 dois dias locais são sinalizados como potencialmente mal rotulados.
- **Dataset:** 10+ anos (2009-01 a 2026-06), ~6200 dias.

### 3.2 Labels — Onda 0

- `tmax_int`: inteiro arredondado conforme contrato Polymarket (P4)
- `tmax_dec`: melhor estimativa decimal interna (P1)
- `Tmax_final`: valor do dia completo (após 06Z do dia seguinte — garante último METAR incluso)
- `tmax_hour`: hora UTC em que `Tmax_final` foi atingido (P2 — data-driven, nunca hardcoded)
- `day_complete`: flag de dia fechado (todos os METARs disponíveis)
- `k_cp`: temperatura no checkpoint CP (inteiro METAR)
- `remaining_warming = Tmax_final - k_cp`: alvo operacional (Onda 3+, mas computado desde já)
- `cp_utc`: timestamp UTC de cada CP contratual (20, 21, 22, 23Z)
- `risco_de_flip`: distância de `tmax_dec` à fronteira ×.5°C mais próxima (P1+P4)

### 3.3 Contratos — Onda 0

- **CPs contratuais** (fixos, exceção a P2): 20Z, 21Z, 22Z, 23Z. CP operacional = 23Z.
- **Firewall causal** (`_contracts.py`): `closed='left'` em todas as janelas temporais; `feature_max_ts < cp_utc`; levanta exceção em violação.
- **Settlement** (`_settlement.py`): `round(tmax_dec)` → bracket; `risco_de_flip = 0.5 - abs(tmax_dec - round(tmax_dec))` — valores próximos de 0 indicam alto risco de flip por 0.1°C.
- **Constantes geofísicas permitidas** (exceções a P2, todas referenciadas com fonte): coordenadas NZWN (-41.327, 174.805), fuso NZST (Pacific/Auckland), DST rules.

### 3.4 Baseline ladder — Onda 1

Degraus, do mais simples ao mais informado:

| Nível | Nome | Fonte | Descrição |
|---|---|---|---|
| L0 | Persistência pura | `_persistence.py` | `Tmax = T_so_far` (temperatura no CP) |
| L1 | dminus1 | `_persistence.py` | `Tmax = Tmax(D-1)` — temperatura máxima de ontem |
| L2 | Climatologia DOY | `_climatology.py` | Média Tmax ±7 dias do ano, 10+ anos |
| L3 | Climatologia CP×mês | `_climatology.py` | Média Tmax condicionada em CP e mês |
| L4 | Empirical condicional | `_empirical.py` | `E[Tmax - T_so_far \| month, CP, k_cp]` com fallback `E[Tmax - T_so_far \| month, CP]` |
| L5 | NWP raw (backlog Onda 2) | futuro | ECMWF, GFS, blend — placeholder no leaderboard |
| L6 | Blend linear ótimo (backlog Onda 2) | futuro | α·Persistence + β·ECMWF + γ·GFS |

O **best-null por CP** é o mínimo dos degraus disponíveis para aquele CP. Nenhum modelo promove se `MAE_model >= MAE_best_null_cp`.

### 3.5 EDA e catálogo de hipóteses — Onda 1

**EDA-relâmpago** (~1-2 dias, notebooks/): orientação visual, geração de hipóteses candidatas. Não é load-bearing — o que vale são as hipóteses codificadas em `eda/_hypotheses.py`.

**Hipóteses iniciais (catálogo seed, do brainstorm auditado):**

| ID | Hipótese | Fonte | Veredito EDA esperado |
|---|---|---|---|
| H1 | Slope 3h (ΔT/hora) melhora previsão de remaining_warming | Reestruturação Achado 13 | — |
| H2 | Hora esperada do pico (por mês×regime) melhora MAE no CP | Reestruturação Achado 13 | — |
| H3 | Regime (calm/transition/late-warming) separa erro de forma significativa | model_error_taxonomy.md | — |
| H4 | Dewpoint depression no CP carrega sinal para Tmax | Wilson & Fovell 2018 | — |
| H5 | T(D−1) agrega além de dminus1 puro | Auditoria #19 | — |
| H6 | Tmin do dia influencia delta Tmax por regime×mês | Auditoria #20 | — |
| H7 | Transições intradiárias de regime geram erro sistemático | Auditoria #14 | — |
| H8 | Mudança de direção do vento (S→N) precede late-warming | EDA projeto, foehn lit | — |
| H9 | Sequências de dias (A→B→C) têm estrutura preditiva | Auditoria #16 | — |
| H10 | Chuva/clearing/recovery pós-frontal causam erros de regime | Auditoria #11, #15 | — |
| H11 | Horário de Tmax varia significativamente por mês×regime (P2) | Auditoria #12, #22 | — |
| H12 | Cobertura de nuvens reduz Tmax vs expectativa do mês×regime | Auditoria #15 | — |
| H13 | Pressão atmosférica (tendência 3h) sinaliza mudança de regime | Foehn lit, Reestruturação | — |

**Framework de hipótese:**
```python
@dataclass
class Hypothesis:
    id: str
    description: str
    feature_column: str        # qual coluna/característica está sendo testada
    test: Callable             # função que recebe (train, test) walk-forward e devolve resultado
    effect_size: float | None  # preenchido após execução
    ci95: tuple[float, float] | None
    p_value: float | None
    passes: bool | None        # IC95 não cruza zero E direção é benéfica
```

Cada hipótese roda no harness walk-forward (expanding splits 2023/2024/2025 + holdout recente), com bootstrap CI95. Passa se o IC95 do efeito não inclui zero e a direção é benéfica. Hipóteses que passam são candidatas a feature na Onda 3; as que falham ficam como documentação negativa (tão valiosa quanto).

### 3.6 Classificador de regime — Onda 1

Heurístico (não ML), data-driven (P2), baseado em thresholds do METAR:

| Regime | Definição | Relevância |
|---|---|---|
| `calm` | T estável (±1°C/h), vento < 10kt, sem precipitação | Maioria dos dias; mais fácil prever |
| `transition` | ΔT > 1°C/h sustentado por ≥2h, ou mudança de vento > 90° | Dia mudando de regime; erro concentrado aqui |
| `late_warming` | ΔT > 1.5°C após 21Z (horário local) | O problema central do modelo anterior |
| `foehn_nw` | Vento NW sustentado + dewpoint depression > 4°C | Subclasse de late_warming com assinatura física |
| `disrupted` | Precipitação, rajada, ou queda de T > 2°C/h | Evento que quebra a tendência |

Flags adicionais: `intraday_regime_change` (True se regime muda durante o dia) — hipótese H7.

**P2 aplicado:** os thresholds (1°C/h, 1.5°C, 4°C, 10kt) são calibrados na EDA sobre os dados NZWN e expressos com justificativa no notebook `01_regime_explore.ipynb`. Não são hardcoded — são documentados com a distribuição que os gerou.

### 3.7 Leaderboard — Onda 1 (artefato principal)

```text
$ python -m solarstorm leaderboard --window 30d
SolarStorm Baseline Leaderboard — 2026-06-04
Window: últimos 30 dias (2026-05-05 a 2026-06-04)

CP=20Z (n=30)
  Best null: climatology_cp_month (MAE 1.82)
  L0 persistence:          MAE 2.14  BM 0.23  RPS 2.14  CRPS 1.67  fallback=N/A
  L1 dminus1:              MAE 1.95  BM 0.27  RPS 1.95  CRPS 1.52  fallback=N/A
  L2 climatology_doy:      MAE 1.88  BM 0.33  RPS 1.88  CRPS 1.44  fallback=N/A
  L3 climatology_cp_month:  MAE 1.82  BM 0.37  RPS 1.82  CRPS 1.41  fallback=N/A   ← BEST NULL
  L4 empirical_cond:       MAE 1.90  BM 0.30  RPS 1.90  CRPS 1.48  fallback=22/30 (73%)

CP=23Z — operacional (n=30)
  Best null: persistence (MAE 1.24)
  ...

Segmentos críticos (CP=23Z):
  late_warming days (n=8):   best null=persistence MAE 1.67
  calm days (n=18):          best null=climatology_cp_month MAE 1.02
  disrupted days (n=4):      best null=dminus1 MAE 2.41

Gates:
  G1 (null_not_beaten):  N/A (apenas baselines)
  G2 (fallback_dominance): empirical_cond FAIL (fallback 73% > 50%) → status=NOT_OPERATIONAL
  G3 (p50_collapse):     todos PASS
  G4 (corr_diff):        persistence WARN (corr_diff=-0.01, nowcast boundary)
  G5 (per_cp):           L0-L3 todos PASS

Resumo: best-null por CP varia com hora e regime. Nenhum baseline único domina.
```

### 3.8 Gates congelados — Onda 1

Fixados a partir dos baselines, **antes** de qualquer modelo treinado ser avaliado:

| Gate | Regra | Violação → |
|---|---|---|
| G1 — Null não batido | `MAE_model >= MAE_best_null_cp` em qualquer CP | KILL (não promove) |
| G2 — Fallback dominante | `fallback_marginal_rate > 0.50` em janela recente | NOT_OPERATIONAL |
| G3 — Collapse de p50 | `p50_mode_share > 0.50` | COLLAPSE_ALERT |
| G4 — Anti-nowcaster | `corr_diff < 0.05` (corr(T_pred, T_truth) − corr(T_pred, T_now)) | NOWCAST_SUSPECT (CI95 deve excluir zero) |
| G5 — Best-null por CP | MAE model < MAE best-null **para cada CP** individualmente | `stay_out` nos CPs onde perde |

**G4 é duro e não-rebaixável.** Foi exatamente o gate que o projeto anterior demoteu para diagnóstico (`phase4_evaluate.py:95`). A lição aprendida é estrutural.

---

## 4. Disciplina de port (anti-quarentena)

O rebuild do zero já falhou uma vez (a `quarentena/`). O guard-rail é:

1. **Portar módulo por módulo**, com os testes do módulo rodando **antes** de portar o próximo.
2. Cada módulo portado é verificado contra fixture sintética que reproduz o comportamento esperado (ex.: `test_causal_firewall.py` com timestamp futuro deve levantar exceção).
3. Módulos portados do projeto anterior: `_metar.py` (parsing), `_labels.py` (Tmax/CP), `_calendar.py` (NZST/DST), `_climatology.py` (DOY-smoothed, CP×mês), `_empirical.py` (só como baseline), `_walkforward.py` (splits), `_metrics.py` (MAE/CRPS/RPS/Brier/reliability), `_contracts.py` (firewall causal).
4. Testes com **fixtures sintéticas** cobrem: dia calmo, dia late-warming, dia com dado faltante, e baseline deliberadamente vazado disparando corr_diff.

---

## 5. Onda 0 tasks (bootstrap & port)

| # | Task | Output | Dependências |
|---|---|---|---|
| 0.1 | Criar estrutura de diretórios + `pyproject.toml` + dev-deps + `README.md` + `CHANGELOG.md` | Repo funcional com `pytest` passando (vazio), README com visão geral e link para specs | — |
| 0.2 | Portar + testar `_calendar.py` (NZST/DST/CPs) | `test_calendar.py` verde | 0.1 |
| 0.3 | Portar + testar `_metar.py` (parsing integer-truth) | `test_metar.py` verde (fixtures METAR sintéticos) | 0.1 |
| 0.4 | Construir + testar `_iem.py` (backfill 10+ anos NZWN) | Download e cache de ~6200 dias NZWN; `test_iem.py` com mock | 0.3 |
| 0.5 | Portar + estender + testar `_labels.py` (Tmax, CPs, remaining_warming, risco_de_flip, tmax_hour, scan 24h) | `test_labels.py` verde | 0.2, 0.3 |
| 0.6 | Implementar + testar `_contracts.py` (firewall causal + constantes contratuais) | `test_causal_firewall.py` verde (timestamp futuro → raise) | 0.2 |
| 0.7 | Implementar + testar `_settlement.py` (P1+P4: rounding, risco_de_flip, bracket mapping) | `test_settlement.py` verde (0.1°C cruza fronteira) | 0.5 |
| 0.8 | Portar + testar `_climatology.py` (DOY-smoothed, CP×mês) sobre 10+ anos | `test_climatology.py` verde | 0.5 |

## 6. Onda 1 tasks (EDA + baseline ladder + leaderboard)

| # | Task | Output | Dependências |
|---|---|---|---|
| 1.1 | Implementar + testar `_persistence.py` (L0, L1) | `test_baselines.py` cobre persistence | Onda 0 |
| 1.2 | Portar + testar `_empirical.py` (L4, rebaixado a baseline) | `test_baselines.py` cobre empirical | Onda 0 |
| 1.3 | Implementar + testar `_ladder.py` (best-null-por-CP) | `test_ladder.py` verde | 1.1, 1.2 |
| 1.4 | Portar + estender `_walkforward.py` (expanding splits + holdouts 7/14/30d) | `test_walkforward.py` verde | Onda 0 |
| 1.5 | Portar + estender `_metrics.py` (bootstrap CIs) + `_bootstrap.py` | `test_metrics.py` verde (CRPS/RPS/Brier em distribuições conhecidas) | 1.4 |
| 1.6 | Implementar + testar `_segments.py` (slice por CP/regime/janela/gap) | `test_segments.py` verde | 1.3, 1.5 |
| 1.7 | Implementar + testar `_gates.py` (G1-G5 congelados) | `test_gates.py` verde (ex.: baseline vazado → G4 dispara, fallback→G2) | 1.5, 1.6 |
| 1.8 | Implementar + testar `_leaderboard.py` (output JSON+MD) | `test_leaderboard.py` verde | 1.3, 1.5, 1.6, 1.7 |
| 1.9 | EDA-relâmpago: notebooks/ 00-03 (~1-2 dias) | Hipóteses candidatas + thresholds de regime calibrados | 0.4, 0.5 |
| 1.10 | Implementar + testar `eda/_regimes.py` (classificador heurístico com thresholds data-driven) | `test_regimes.py` verde | 1.9 |
| 1.11 | Implementar + testar `eda/_hypotheses.py` + `eda/_catalog.py` (H1-H13) | `test_hypotheses.py` verde; cada Hn roda no harness e devolve efeito+IC+pass/fail | 1.4, 1.5, 1.10 |
| 1.12 | CLI `__main__.py`: comandos `ingest`, `baselines`, `leaderboard`, `eda` — todo comando que produz output gera artefato versionado em `reports/` automaticamente (P5); stdout é só eco | `python -m solarstorm leaderboard` funcional, arquivo em `reports/leaderboard/` commitado | 1.8, 1.11 |
| 1.13 | Gerar leaderboard baseline sobre 2026 + relatório de hipóteses + atualizar `CHANGELOG.md` com o marco Onda 0+1 | Artefatos versionados em `reports/leaderboard/` e `reports/hypotheses/`; CHANGELOG registra a entrega | 1.12 |

---

## 7. Backlog tagueado (ondas futuras)

Estes itens foram julgados pertinentes mas pertencem a ondas posteriores:

**Onda 2 (NWP + blend):**
- Open-Meteo multi-modelo (ECMWF+GFS+ICON, ~31 membros)
- Pipeline causal NWP: `run_time_utc <= cp_utc - safety_margin`
- Ingestão features de nuvem/precipitação (H10, H12)
- DEB-style blend (1/MAE com decaimento temporal — PolyWeather)
- Features de foehn do NWP: vento 850hPa, gradiente cross-strait (#8, #11)
- L5+L6 no ladder

**Onda 3 (núcleo residual probabilístico):**
- Alvo `remaining_warming = Tmax_final - k_cp` (mata nowcasting por construção)
- NWP-anchor + residual LGBM
- Bake-off: NGBoost vs LGBM-quantile (H4, #25)
- CQR via MAPIE (#25)
- Analog no espaço NWP (não observações — Delle Monache, #6)
- Two-stage detector (sem nome "oracle", #2)
- Late-spike feature em todos os regimes (#21)
- Lição FIRM: janela sazonal ≥12 meses (#24)
- Stacking decimal com meta-learner Ridge (#25)

**Onda 4 (forecast sequencial intradiário):**
- Atualização a cada METAR (06, 09, 12, 15, 18, 20, 21, 22, 23Z)
- Checkpoints flexíveis de alto valor por regime/hora-esperada (#13, #18)
- Assimilação peak-aware (PolyWeather)
- Piso `max_so_far` — nunca probabilidade abaixo do já observado
- Dead-market lock — pico já passou → probabilidade 1.0 no observado
- Plateau detect (#13)

**Onda 5 (governança forense contínua):**
- Auditoria anti-nowcasting (7 fases forenses) como CI gates
- Drift detection
- Ladder diário automático
- Fase 7 (edge econômico) — apenas quando forecast_value > 0 comprovado

**Backlog experimental (sem onda, requer validação prévia):**
- TAF parser como supressão-only (#13)

---

## 8. Deliverables de documentação (P5)

Cada marco de Onda produz:

| Artefato | Formato | Local | Trigger |
|---|---|---|---|
| Leaderboard baseline | JSON + Markdown | `reports/leaderboard/YYYY-MM-DD-leaderboard.{json,md}` | `solarstorm leaderboard` |
| Relatório de hipóteses | JSON + Markdown | `reports/hypotheses/YYYY-MM-DD-hypotheses.{json,md}` | `solarstorm eda` |
| Spec de design | Markdown | `docs/specs/YYYY-MM-DD-<wave>-design.md` | Antes de cada onda (este documento é o primeiro) |
| ADR (decisões de arquitetura) | Markdown | `docs/decisions/YYYY-MM-DD-<slug>.md` | Quando uma decisão de design não-óbvia é tomada |
| CHANGELOG | Markdown | `CHANGELOG.md` (raiz) | A cada merge; uma linha por mudança significativa |
| README | Markdown | `README.md` (raiz) | Atualizado a cada onda — visão geral, instalação, link para specs |

Regras:
- **Hipóteses que falham são documentadas com o mesmo rigor das que passam.** Um catálogo de "o que não funciona e por quê" é ativo de conhecimento — evita repetir becos sem saída e é exatamente o que permitiu auditar o projeto anterior.
- **Leaderboard é versionado.** Todo `solarstorm leaderboard` escreve arquivo datado em `reports/leaderboard/`. O histórico de leaderboards no git mostra a evolução do poder preditivo ao longo do tempo.
- **CHANGELOG é linha do tempo, não lista técnica.** Uma entrada típica: `2026-06-10 — Onda 0 completa: ingestão METAR 2009-2026 (6371 dias), labels Tmax/CP/remaining_warming, climatologia DOY+CP×mês`.
- **README nunca fica desatualizado.** Após cada onda, a seção "Quick Start" é verificada — um novo dev deve conseguir rodar o CLI em < 5 minutos.

---

## 9. O que NÃO está neste spec (explicitamente)

- Qualquer automação de trading, shadow ops, decisão, Kelly sizing
- Calibração conformal, IC80, confidence scores
- Modelos ML (Ridge, LGBM, NGBoost) — entram na Onda 3
- Ingestão NWP — Onda 2
- Live serving, atualização intradiária — Onda 4
- Interface web, dashboards, APIs
- Deploy, CI/CD além de `pytest` no commit

O escopo é a fundação. Sem ela, tudo acima é torre em areia.
