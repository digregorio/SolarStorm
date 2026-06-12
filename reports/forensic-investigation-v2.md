# Investigação Forense v2: Wellington Tmax (SolarStorm)

Status do projeto: `EXPERIMENT_ONLY` (mantido)
Data: 2026-06-12
Método: auditoria adversarial do repositório atual, com a premissa inicial de
que o modelo poderia estar "trapaceando" (nowcast disfarçado, persistência
implícita, leakage temporal). Todos os números abaixo foram verificados contra
código e artefatos do repo; cálculos novos são reproduzíveis a partir de
`data/labels.parquet` e dos CSVs citados.

---

## 0. Veredicto sobre o relatório forense anterior

`reports/forensic-investigation-report.md` (autor "Antigravity", 2026-06-11)
**mistura dois codebases**. As falhas G1 (empirical servindo em produção com
MAE 2.32 e 92.9% de fallback), G2 (CQR/"Fase 5"/LightGBM) e G4 (ECMWF
single_runs 35.8% de cobertura) referem-se ao **projeto antigo em
`/quarentena/Wellington/`**, não ao SolarStorm atual:

- O SolarStorm não usa LightGBM nem CQR (`pyproject.toml`: polars, numpy,
  typer, tzdata). Só existe ridge NumPy.
- `reports/phase5_closure.md` não existe no repo.
- Não há caminho de serving/produção rodando — o repo é 100% offline.
- Os arquivos `solarstorm/serving/`, `solarstorm/calib/emos_calibrator.py` e
  `scripts/*.py` (backtest_trading_ev, ecmwf_backfill_full,
  live_nwp_availability_audit) **existem mas não estão rastreados no git** e
  não passaram pela disciplina TDD/ADR do projeto. Devem ser tratados como
  rascunhos não auditados da sessão anterior, não como infraestrutura.

Os números experimentais citados (Onda 3F 1.062; selected 0.783; season 0.762;
augmented 0.824) **conferem** com os artefatos. As direções propostas
(EMOS/CRPS, multi-pass, stay-out) são boas ideias, mas o diagnóstico de
causa-raiz estava errado porque descrevia o projeto errado.

---

## 1. Causa-raiz dos "resultados fracos": o problema não é o modelo, é a régua

### C1. O lift reportado é ilusório — o null oficial é um espantalho

O gate M3 (Onda 4M) compara o ridge contra a **média de treino do Tmax**
(`solarstorm/onda3/_pooled_iteration.py:318-321`): null MAE 2.812 → challenger
1.06-1.35, "lift" 1.46-1.78. Mas o null honesto para esse problema é
**`k_cp` (máxima já observada até o CP) + aquecimento restante climatológico**.

O próprio projeto já tinha essa evidência e a ignorou nos gates:
`BEXP-L4-MONTH-CP-REGIME-001` (mês×CP×regime, train-only) = **MAE 1.176**
(`reports/foundation-experiments/foundation_experiment_results_v1.csv`).

Recalculei o null trivial no protocolo do nested (treino ≤2022, teste
2023-2025, `pred = k_cp + mediana_mensal(restante)`):

| CP (UTC) | Null trivial MAE | Null exact | Onda 3F MAE (slice) | Onda 3F CP23 exact |
|---|---:|---:|---:|---:|
| 20:00 | 1.619 | 21.0% | 1.137 | — |
| 21:00 | 1.392 | 22.8% | 1.054 | — |
| 22:00 | 1.096 | 28.5% | 1.028 | — |
| 23:00 | **0.850** | **36.5%** | 1.028 | 31.5% |
| média | 1.239 | — | 1.062 | — |

(Onda 3F slices: `reports/onda3-pooled/onda3_pooled_slice_diagnostics_v1.csv`.)

**Conclusões:**
- O modelo local Onda 3F **perde para o null trivial no CP 23:00** (1.028 vs
  0.850 de MAE; 31.5% vs 36.5% de exact) e empata no CP 22:00.
- O lift local real médio é ~0.18 °C sobre o null trivial — não 1.75 °C.
- Anos de iterações (3B…3H) otimizaram contra uma régua que qualquer
  termômetro + climatologia vence. É por isso que "várias tentativas" deram
  melhoras mínimas: o sinal local restante é pequeno mesmo.

### C2. Nowcast estrutural: a resposta já está parcialmente no input

Os CPs 20:00-23:00 UTC = **08:00-12:00 local** do dia alvo. Computado de
`data/labels.parquet` (5.439 dias):

| CP | Tmax já realizada | Restante ≤1 °C | Mediana restante | p90 restante |
|---|---:|---:|---:|---:|
| 20:00 | 13.4% | 27.4% | 3.0 | 6.0 |
| 21:00 | 14.5% | 31.2% | 2.0 | 5.0 |
| 22:00 | 17.8% | 42.6% | 2.0 | 4.0 |
| 23:00 | **26.1%** | **62.0%** | 1.0 | 3.0 |

No CP final, em 1 de cada 4 dias o "forecast" é leitura de termômetro, e em
62% dos dias o jogo inteiro é ±1 °C. O target é `tmax_int` do dia cheio
(`solarstorm/data/_labels.py:71-79`), incluindo horas pré-CP, e `k_cp` é
feature permitida (`solarstorm/onda3/_nested_validation.py:21-39`). Isso é
**causal e legítimo** — mas significa que MAE agregado mistura duas tarefas de
dificuldade muito diferente (nowcast fácil + forecast difícil), e qualquer
métrica agregada superestima a habilidade de *forecast*.

**Os gates anti-nowcast existentes não testam nada disso:**
- M7 do Onda 4M é **hardcoded PASS** com detail
  `target_proxy_columns_blocked_by_manifest`
  (`solarstorm/robustness/_model_review.py:159-165`). Não computa nada.
- O lead-time check do Onda 4 passa se existir **≥1 dia** (`min_days=1`) com
  Tmax após o CP (`solarstorm/robustness/_lead_time.py:128`). Não mede de onde
  vem a skill.
- G4 (anti-nowcaster de features, `solarstorm/eval/_gates.py`) audita features
  individuais da Onda 2, não o modelo da Onda 3.

**Resposta direta às perguntas da investigação:**
- *"O modelo foi treinado com tmax como feature?"* **Não.** O manifest bloqueia
  `tmax_int`, `tmax_hour`, `remaining_warming`, `tmax_anomaly`
  (`solarstorm/onda3/_feature_manifest.py:5-10`). `tmax_dminus1` (ontem) e
  `k_cp` (máxima até o CP) são causais e permitidos.
- *Leakage estrutural?* Não encontrado nos splits (treino/teste por ano,
  imputação por média de treino, one-hot train-only). O macro binário é regra
  direcional sobre obs pré-CP, não usa o dia cheio.
- *Nowcast disfarçado?* **Parcialmente sim, por construção do protocolo de
  avaliação** — não por fraude de feature, mas por null fraco + target que
  inclui o passado + métricas agregadas sem estratificação por
  `remaining_warming`.

### C3. O valor está em dois lugares diferentes — e ninguém combina os dois

- Nos **CPs cedo**, o problema é forecast atmosférico: NWP domina
  (política Open-Meteo 0.76-0.78 vs null trivial 1.62 no CP20).
- Nos **CPs tardios**, o problema é nowcast: o null trivial domina
  (0.85 no CP23) e o NWP cru agrega pouco.
- As políticas Open-Meteo produzem **uma previsão por dia repetida nos 4 CPs**
  — métricas idênticas por CP em
  `reports/open-meteo-expanded-decision-review-2022-2025/open_meteo_expanded_policy_slice_metrics_v1.csv`.
  A informação intradiária crescente (k_cp, slope, vento) é descartada
  exatamente onde ela é mais valiosa.
- **6.8-9.0% das previsões dos melhores candidatos violam o piso físico
  `pred ≥ k_cp`** (computado de
  `reports/open-meteo-forensics-2022-2025/open_meteo_forensics_pairwise_rows_v1.csv`
  + labels). Prever abaixo da máxima já observada é erro grátis.

### C4. O mercado liquida distribuição; o projeto otimiza ponto

A liquidação é por bracket inteiro de °C. O projeto inteiro otimiza MAE de uma
previsão pontual; exact-bracket é métrica secundária; não existe distribuição
preditiva calibrada; a "regra de abstenção" é uma **string**
("abstain when pooled CP/regime slice support is weak",
`reports/onda3-pooled/onda3_pooled_uncertainty_abstention_v1.csv`) e o gate M6
só verifica `bool(abstention_rule.strip())`
(`solarstorm/robustness/_model_review.py:150-158`). Não há entropia, não há
spread inter-modelo, não há `forecast_valid`.

### C5. Regimes: o deadlock foi provado; não é o gargalo principal

A evidência é conclusiva e deve ser aceita: METAR da manhã **não separa** mais
de 2 macro-estados (estabilidade GMM 0.0799; 82% low-confidence; calm_radiative
0/92 em R2 — `reports/regime-design/regime_deadlock_pivot_decision_v1.md`).
O macro binário southerly/non-southerly + features contínuas foi a resposta
certa. Parar de procurar a "ontologia perfeita" com os dados atuais; regimes
melhores virão de **campos sinóticos do NWP** (vento/pressão previstos), não de
mais clustering sobre a mesma estação.

### C6. Late spikes: quantificados, não modelados

De `reports/robustness-v2_1/late_spike_candidates.json` + labels: no CP23,
**4.1% dos dias sobem ≥4 °C depois do CP** (verão: jan 39, fev 28, dez 22
casos) e 31% sobem ≥2 °C. São exatamente os dias que destroem apostas de
bracket. Não existe classificador de risco de late spike nem uso do baseline
q90 mês/regime já gerado pelo Onda 4 (R9).

### C7. Dados: o teto do dataset atual é baixo; as fontes certas existem

- 1 estação METAR + Previous Runs day-1 determinístico de 6 modelos globais.
- Profundidade histórica da Open-Meteo Previous Runs: maioria dos modelos só
  desde **jan/2024** (GFS desde mar/2021, JMA desde 2018) — por isso o eterno
  problema de "1-2 folds". Isso é um **limite estrutural**: mais fórmulas de
  calibração não criam folds.
- Não usados hoje: **Ensemble API da Open-Meteo** (31 membros GFS, ECMWF ENS —
  é o que os bots de referência usam para distribuição), **UKMO Global**,
  **BOM ACCESS-G** (cobre NZ), e **MetService** (provedor oficial NZ,
  Point Forecast API em data.metservice.com, WRF 4 km próprio, free tier;
  histórico de forecast limitado a ~5 dias ⇒ precisa coleta forward, que o
  OM-M14 já sabe fazer).

### C8. Engenharia: não há produção para falhar

Não existe serving, scheduler, mercado ou EV no repo auditado (CLI é 100%
offline). O fracasso não é "erro de engenharia de produção" (diagnóstico do
relatório anterior, válido para o projeto antigo); é **protocolo de avaliação
que mediu a coisa errada** + **teto de informação dos dados locais**.

---

## 2. O que NÃO é o problema (parar de iterar nisso)

1. Mais ontologia de regimes sobre METAR matinal — deadlock provado (C5).
2. Truncar/expandir anos de treino — Onda 3E provou efeito ~0.002 °C.
3. Mais uma fórmula de calibração de bias global/recente — OM-M6/M8 provaram
   que o erro é drift por ano/regime, e o ganho marginal é <0.05 °C.
4. Mais interações handcrafted locais — Onda 3D rendeu 0.03 °C.
5. Hiperparâmetros do ridge — o sinal local restante é ~0.1-0.2 °C no total.

---

## 3. Roadmap para produção

Princípio: por horizonte, o problema muda de natureza. Produção = um sistema
que (a) nos CPs cedo extrai o máximo do NWP, (b) nos CPs tardios degrada
graciosamente para nowcast+climatologia, (c) emite **distribuição** por
bracket, (d) sabe quando ficar de fora, e (e) é medido contra o null honesto.

### Fase P0 — Régua honesta (1 sprint; pré-requisito de tudo)

1. Promover o null `k_cp + climatologia do restante (mês×CP, train-only)` a
   **null oficial por CP** em todos os gates (substituir train-mean no M3).
2. Reescrever M7: exigir (a) curva de degradação por lead — skill vs null por
   bucket de `hours_to_tmax`; (b) ablação do bloco persistência (k_cp,
   tmax_dminus1, warming_rate, slope_3h): reportar quanto da skill sobrevive;
   (c) avaliação estratificada por `remaining_warming ≥ 2 °C` (dias onde só
   forecast importa). **Prova matemática de antecipação** = vencer o null
   nesses estratos, não no agregado.
3. Impor o piso físico `pred ≥ k_cp` em todo candidato (ganho grátis em 7-9%
   das linhas).
4. Gate de promoção: nenhum modelo avança se não vencer o null oficial **em
   cada CP** e no estrato `remaining_warming ≥ 2`.

### Fase P1 — Modelo híbrido por horizonte (target = restante, não Tmax)

1. Trocar o target para `remaining_warming = tmax - k_cp` (já definido em
   `solarstorm/data/_labels.py:31`) e prever `tmax = k_cp + restante`. Isso
   remove a variância nowcast do target e força o modelo a aprender só o que
   falta acontecer.
2. Blend NWP+local com peso por lead: nos CPs cedo o âncora é o Tmax previsto
   pelos provedores (calibrado por família, como OM-M4/M7 já fazem); nos CPs
   tardios o âncora é k_cp + restante condicional. Um único modelo com
   interação lead×fonte resolve isso dentro do próprio ridge.
3. Atualização intradiária real: a previsão do CP t+1 deve condicionar em
   tudo observado até t+1 (hoje as políticas Open-Meteo repetem o mesmo número
   o dia todo — C3).

### Fase P2 — Distribuição calibrada (EMOS/CRPS), não ponto

1. Coletar **Ensemble API** da Open-Meteo (membros GFS/ECMWF) na coleta
   forward OM-M15, além do Previous Runs determinístico.
2. EMOS/NGR: `Tmax ~ N(μ, σ²)` com `μ = a + b·blend` e
   `σ² = c + d·spread_ensemble + e·lead + f·regime`, treinado minimizando CRPS
   (Gneiting et al. 2005). Alternativa não-paramétrica que respeita
   mês/regime: **Analog Ensemble** (Delle Monache et al. 2013) — busca de dias
   análogos train-only por predictores NWP+locais, ponderada por mês/regime —
   atende diretamente a tese de "active analog search" e dá distribuição
   empírica de graça.
3. Probabilidade por bracket: `P(bracket b) = F(b+0.5) − F(b−0.5)` na escala
   de liquidação inteira.
4. Gates de calibração (herdar a régua do projeto antigo, agora com método
   certo): PIT uniforme, cobertura IC80 ∈ [0.78, 0.84] por CP e por ano,
   CRPS < CRPS do null climatológico em todo CP.

### Fase P3 — Risco de late spike + abstenção operacional

1. Classificador de late spike (target: `delta_after_cp ≥ 2` no CP em
   questão), features: q90 mês/regime do R9, pressão/tendência, setor de
   vento, foehn_score, nebulosidade, e spread/disagreement inter-modelo NWP.
2. Abstenção executável substituindo a string: `forecast_valid = false` quando
   (a) entropia da distribuição acima do limiar, (b) spread inter-modelo acima
   do limiar (a a regra "evening scout" dos bots de referência), ou (c) risco
   de late spike alto com mercado em bracket vizinho. Limiares congelados
   **antes** de olhar resultado financeiro (disciplina anti-gaming do projeto).

### Fase P4 — Dados (paralela a P1-P3)

1. **OM-M15** (já especificado): scheduler live da coleta forward — agora
   incluindo Forecast API + Ensemble API + **MetService Point Forecast API**
   (provedor oficial, WRF 4 km; só forward, sem histórico profundo).
2. Backfill Previous Runs de UKMO Global e BOM ACCESS-G a partir de 2024 para
   ampliar a família de provedores na janela 2024+.
3. Aceitar que folds históricos são limitados; a partir daqui, evidência nova
   vem majoritariamente de **dados forward maduros** (OM-M14 lifecycle).

### Fase P5 — EV realizado e shadow trading (só após P0-P3 passarem)

1. Harness de backtest financeiro contra brackets (o rascunho
   `scripts/backtest_trading_ev.py` precisa ser auditado/reescrito sob TDD):
   edge = P_model − P_market, Kelly fracionário com cap, custo/spread, CLV.
2. Referências práticas dos bots públicos: operar só com edge mínimo (~8%),
   quarter-Kelly, consenso multi-sinal com **stay-out default** (um bot de
   referência fica de fora em 48% dos dias), e a constatação empírica de que
   mercados de temperatura superprecificam incerteza (~1.27×) — o edge
   sustentável é mais "vender incerteza com calibração superior" do que
   "prever melhor o ponto".
3. Shadow trading por uma estação completa de verão (maior densidade de late
   spikes) antes de qualquer capital real.

### Gates de saída do EXPERIMENT_ONLY

| Gate | Critério |
|---|---|
| Skill honesta | Vence null `k_cp+climatologia` em todos os CPs e no estrato `restante ≥ 2 °C`, em ≥2 folds + dados forward maduros |
| Anticipação | Skill sobrevive à ablação do bloco persistência nos CPs cedo |
| Calibração | PIT uniforme; IC80 ∈ [0.78,0.84]; CRPS < null em todo CP/ano |
| Física | 0 violações de `pred ≥ k_cp` |
| Abstenção | Regra executável, congelada ex-ante, com taxa de stay-out reportada |
| Financeiro | EV realizado positivo + CLV ≥ 0 em shadow trading de 1 estação |

---

## 4. Fontes externas consultadas

- Open-Meteo Previous Runs API e profundidade por modelo:
  https://open-meteo.com/en/docs/previous-runs-api
- Open-Meteo UKMO (Global 10 km cobre NZ; UKV só UK/IE):
  https://open-meteo.com/en/docs/ukmo-api
- Open-Meteo Ensemble API (membros GFS/ECMWF):
  https://open-meteo.com/en/docs/ensemble-api
- MetService Data & APIs (Point Forecast API, WRF 4 km, free tier):
  https://data.metservice.com/ e
  https://data.metservice.com/product/point-forecast-api
- EMOS/NGR: Gneiting et al. 2005 (MWR); aplicação espacial NGR:
  https://journals.ametsoc.org/view/journals/mwre/143/3/mwr-d-14-00210.1.xml
- Analog Ensemble: Delle Monache et al. 2013 (MWR):
  https://www.semanticscholar.org/paper/4bd66fcb37ec387b03b96c81b499a0d915c3d578 ;
  implementação: https://github.com/Weiming-Hu/AnalogsEnsemble
- Bots de referência (padrões: ensemble, edge mínimo, Kelly fracionário,
  stay-out):
  https://github.com/suislanchez/polymarket-kalshi-weather-bot ,
  https://github.com/Stewyboy1990/weatheredge-bot ,
  https://github.com/Oalkhadra/prediction-market-trading (superprecificação
  de incerteza 1.27×),
  https://github.com/gopher-lab/kalshi-go (consenso/stay-out 48%).

---

## 5. Apêndice: comandos de verificação

```bash
# Fração de dias com Tmax já realizada por CP + null trivial (seção C1/C2)
uv run python - <<'PY'
import polars as pl
lab = pl.read_parquet('data/labels.parquet').with_columns(
    pl.col('date_local').dt.year().alias('year'),
    pl.col('date_local').dt.month().alias('month'))
for cpcol in ['k_cp__cp_2000','k_cp__cp_2100','k_cp__cp_2200','k_cp__cp_2300']:
    df = lab.select(['year','month','tmax_int',cpcol]).drop_nulls().with_columns(
        (pl.col('tmax_int')-pl.col(cpcol)).alias('rw'))
    train, test = df.filter(pl.col('year')<=2022), df.filter(pl.col('year')>=2023)
    med = train.group_by('month').agg(pl.col('rw').median().alias('m'))
    t = test.join(med, on='month').with_columns((pl.col(cpcol)+pl.col('m').round(0)).alias('pred'))
    print(cpcol, 'ja_visto%', round((df['rw']==0).mean()*100,1),
          'null_mae', round((t['pred']-t['tmax_int']).abs().mean(),3),
          'null_exact%', round((t['pred']==t['tmax_int']).mean()*100,1))
PY
```
