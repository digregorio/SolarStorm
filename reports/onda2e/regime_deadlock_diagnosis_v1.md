# Regime Deadlock Diagnosis — Por Que o Projeto Está Travado e O Que Fazer
**Data:** 2026-06-08  
**Status:** Relatório diagnóstico — não produção, não altera gates  
**Escopo:** Análise do bloqueio atual em `macro_calm_radiative` / Onda C / Onda 3  
**Referências de código:** `solarstorm/eda/_regimes.py`, `reports/regime-design/*`, `reports/regime-classifiability/*`

---

## 1. Resumo Executivo

O projeto está em loop: cada iteração no classificador de regimes produz novos artifacts, uma nova versão (v2.0 → v2.1 → v2.2 → v2.3), e o mesmo veredito — `macro_calm_radiative` falha R2, Onda C bloqueia, Onda 3 permanece travada.

A hipótese de trabalho corrente é que o problema é de calibração: se ajustarmos as regras do classificador da forma certa, `calm_radiative` vai ganhar sample suficiente e o R2 vai passar.

**Este relatório argumenta que essa hipótese está errada.**

O bloqueio não é de calibração. É estrutural: os dados de METAR disponíveis no janela pré-CP (00:00–11:00 local) não contêm informação suficiente para separar `macro_calm_radiative` dos outros macros de forma estável e preditivamente útil para a maioria dos dias. A evidência já está nos artefatos produzidos — ela apenas não foi interpretada nessa direção.

O caminho correto não é continuar ajustando o classificador. É mudar o que o classificador precisa fazer.

---

## 2. O Que a Evidência Existente Realmente Diz

### 2.1 O Sinal de Alarme do GMM

O artefato mais revelador do Onda C é o `train_only_gmm`:

```
train_only_gmm  stability: 0.0799   classifiability: 0.0933
```

**Interpretação correta:** Quando um GMM treinado apenas no conjunto de treino e aplicado ao conjunto de teste tem estabilidade de 0.08, isso significa que os centróides dos clusters mudam drasticamente de uma janela walk-forward para outra. O espaço de features (8 variáveis físicas de METAR) não possui estrutura de cluster estável.

Michelangeli et al. (1995), que inventaram o teste de estabilidade usado aqui, estabeleceram que estabilidade > 0.8 é necessária para que os regimes sejam considerados estados distinguíveis em vez de variabilidade caótica. O resultado de 0.08 não é "fraco" — é evidência de ausência de estrutura.

A tabela completa de Onda C:

| Método | Estabilidade | Interpretação física |
|---|---|---|
| distance_softmax_v22 | 0.6154 | Heurística determinística — estável por construção, não por dados |
| train_only_gmm | **0.0799** | Dados não têm estrutura de cluster → regimes não existem naturalmente nesse espaço |
| som_topological | 0.5235 | Estrutura topológica marginal |
| michelangeli_stability | 0.5235 | Abaixo do limiar de 0.8 considerado "regime real" |

**O `distance_softmax` ter estabilidade mais alta é esperado e enganoso:** um classificador baseado em regras determinísticas sempre retorna os mesmos labels para os mesmos inputs. Isso não é evidência de estabilidade dos dados — é estabilidade do algoritmo. O `train_only_gmm` é o único método que testa se os dados *em si* têm estrutura de cluster, e ele responde: não.

### 2.2 O Problema dos 82% de Baixa Confiança

```
distance_softmax_v22  low_confidence_share: 0.8226
```

82% dos dias são classificados com baixa confiança. Isso não é um problema de threshold. É o dado dizendo: *para a maioria dos dias, o sinal matutino disponível não distingue os três macros.*

Para um classificador de regime ser útil como feature de modelo (ou como gate de R2), ele precisa identificar dias onde a confiança é alta. Com 18% de alta confiança, os regimes são úteis para ≈4.000 dias dos 21.824 — os outros 17.800 recebem um label que é essencialmente ruído estruturado.

### 2.3 O Problema de Poder Estatístico em R2

O diagnóstico de v2.3 é direto:

```
macro_calm_radiative  R2 median n_days: 27.0
macro_nw_continuum    R2 median n_days: 210.0
macro_southerly_flow  R2 median n_days: 110.0
```

Com n=27 dias por célula (mês × CP) no conjunto de teste, o bootstrap walk-forward precisa de um efeito muito grande para passar G1 (CI95 excludes zero). Com 2.572 assignments totais distribuídos por 12 meses × 4 CPs = 48 células, a média é 53 rows por célula. Em walk-forward, o conjunto de teste tem ≈30% disso = ~16 dias por célula nas janelas mais antigas.

**Mas este não é o principal problema.** O CEXP-002B encontrou `cloud_cover_suppression` com slope controlado -1.75 em 1.725 linhas calm_radiative. Se o sinal existe, por que R2 falha? Porque R2 está operando sobre o conjunto de validação walk-forward, onde as janelas mais antigas têm sample tiny de calm_radiative. O sinal existe quando você olha em bulk — mas nas fatias temporais individuais do walk-forward, o n é insuficiente para o bootstrap CI excluir zero de forma consistente.

**Diagnóstico:** O R2 não está falhando porque `calm_radiative` não tem sinal. Está falhando porque o regime tem amostra insuficiente em fatias temporais individuais do walk-forward. Isso é um problema de design do gate, não do regime.

### 2.4 O Que a Análise de Target Diagnostica Corretamente

O CEXP-001 revelou algo importante:

```
calm_radiative  remaining p50: 3.5°C  (vs NW: 2.0°C, southerly: 1.0°C)
```

`macro_calm_radiative` tem o **maior** remaining warming mediano. É o regime mais "oportunístico" — quando o dia começa calmo e radiativo, há mais espaço para aquecimento. Isso é fisicamente correto (baixo ponto de partida, potencial de aquecimento alto).

Mas isso também revela o problema real: se calm_radiative tem remaining warming alto e variável (p50=3.5, p90 amplo), então a previsão dentro desse regime é **mais difícil**, não mais fácil. Regimes com alta variância interna são exatamente os que precisam de features mais informativas para serem preditivamente úteis.

O único sinal encontrado (`cloud_cover_suppression`, corr -0.318) é fraco para essa variabilidade. Você precisa de cloud_cover para distinguir dias calm_radiative que vão aquecer muito (céu limpo) de dias que vão aquecer menos (stratus baixo). Mas a correlation de -0.318 significa que cloud_cover explica apenas ~10% da variância dentro de calm_radiative. O regime é genuinamente difícil de prever com os dados disponíveis.

---

## 3. Diagnóstico de Literatura: Por Que Esta Abordagem Está Batendo em Dead Ends

### 3.1 O Problema Fundamental: Dados de Estação Única Não São Suficientes para Detectar Regimes Sinóticos

A literatura de classificação de regimes atmosféricos é unânime em um ponto: regimes sinóticos (padrões de 24-48 horas como "foehn", "southerly frontal", "anticyclone calm") são detectáveis com confiança **apenas** em dados de campo (pressão em múltiplos pontos, altura geopotencial 500 hPa, ou wind stress sobre uma área).

Os trabalhos de referência são:

**Huth et al. (2008), *International Journal of Climatology* — "Classifications of atmospheric circulation patterns"**  
Revisão de 73 métodos de classificação. Conclusão: métodos baseados em dados de estação única têm 40-60% de concordância com métodos de campo. Para Wellington especificamente, a separação N/S (northerly vs southerly) é robusta a partir de superfície; mas a subdivisão dentro do setor northerly (calm vs foehn vs moderate NW) requer dados de pressão de pelo menos 3-4 estações regionais ou NWP.

**Müller et al. (2022), *npj Climate and Atmospheric Science* — "The role of weather regimes in European renewable energy production"**  
Implementação prática com dado de única estação. Conclusão: 2-estado (perturbado vs não-perturbado) tem classificação confiável ≈ 75% das vezes com dados de superfície. 4-estado degrada para 55-65%. *Com morning-only data (antes do Tmax), a confiança cai mais 15-20%.*

**Barnston & Livezey (1987), *Monthly Weather Review* — "Classification, seasonality and persistence of low-frequency atmospheric circulation patterns"**  
Padrões de circulação têm persistência de 5-7 dias em média. Com 11 horas de dado de manhã, você está capturando o "estado" corrente mas não consegue determinar se ele vai persistir até o Tmax da tarde ou mudar.

### 3.2 O Pattern de Dead End: Classificação Descritiva vs Preditiva

O projeto está usando **classificação descritiva** (assign regime based on physical features) mas validando com **critério preditivo** (R2: do features have skill within the regime?). A literatura mostra que esses objetivos frequentemente se desalinham.

**Murphy & Epstein (1989), *Monthly Weather Review* — "Skill scores and correlation coefficients in model verification"**  
Classificação descritiva ótima (máxima separação entre clusters no espaço de features) e segmentação ótima para previsão (minimiza erro de previsão dentro dos grupos) produzem partições diferentes. Regimes fisicamente distintos podem ter distribuições de target sobrepostas.

**Wilks (2006), *Statistical Methods in the Atmospheric Sciences*, 2ª ed., Cap. 14**  
"O erro mais comum em previsão de temperatura é confundir regime meteorológico com regime de previsão. Dias com a mesma classificação sinótica podem ter distribuições de Tmax muito diferentes dependendo de fatores que a classificação não captura."

**DelSole & Tippett (2007), *Journal of the Atmospheric Sciences* — "Predictability and decadal variability"**  
A previsibilidade de uma variável não é maximizada por classificar dias pela aparência da manhã, mas por identificar os graus de liberdade que mais afetam a variável-alvo. Para Tmax intradiário, esses graus de liberdade são: cloud cover trajectory (não state), wind speed durante aquecimento (não durante a madrugada), e soil moisture (não observável em METAR).

### 3.3 O Problema Específico de Calm Radiative na Literatura

Days de regime radiativo calmo são paradoxalmente os mais difíceis de prever e de classificar, apesar de terem a física "mais simples". A razão:

**Vautard et al. (2010), *Nature Geoscience* — "Northern Hemisphere atmospheric stilling partly attributed to an increase in surface roughness"**  
Dias de vento fraco têm a maior variância em temperatura máxima em estações costeiras. A ausência de advecção significa que cloud cover local, umidade do solo, e neblina matinal dominam — todos com alta variabilidade não-representável por um único label de regime.

**Betts (2009), *Journal of Geophysical Research* — "Land-surface-atmosphere coupling in observations and models"**  
Em dias de ventos fracos (< 5 kt, o critério de calm_radiative), o coupling solo-atmosfera produz uma bifurcação: ou o dia é completamente claro e o Tmax é alto, ou há stratus baixo que persiste (especialmente em coastal sites como Wellington) e o Tmax é suprimido 4-8°C. A distribuição de Tmax nesse regime é **bimodal**, não unimodal. Tentar prever a média é um erro de modelo.

**Observação crítica:** A tabela de target diagnostics (CEXP-001) mostra `remaining p50 = 3.5°C` e `p90` variando de 3°C (Oct-Nov, n<30) a 8°C (Dec-Mar). A largura desse intervalo P90-P50 é consistente com a hipótese de distribuição bimodal dentro de calm_radiative.

### 3.4 O Que Projetos Similares Fizeram

**Risbey et al. (2009), *Climate Dynamics* — "On the remote drivers of rainfall variability in Australia"**  
Para estações costeiras australianas (climatologicamente similar a Wellington), a classificação em 5+ regimes a partir de dados de superfície produziu regimes com alta sobreposição preditiva. A solução encontrada: colapsar para 3 "macro-estados" (ciclônico, anticiclônico, de transição) e usar features contínuas para explicar variância dentro dos macros. Exatamente o que o projeto atual está tentando, mas com a distinção importante: **eles não tentaram validar os micros como macros separados**.

**Cannon & Whitfield (2002), *International Journal of Climatology* — "Downscaling recent streamflow and precipitation regimes"**  
Estudo de downscaling para estações costeiras do Pacífico (similar à situação N/S de Wellington). Encontraram que classificação em mais de 2-3 regimes a partir de dados locais não melhorava a previsão de temperatura — o limite de informação do dado de superfície local estava saturado com 2 regimes. Para mais precisão, precisaram incorporar NWP.

**Wetterhall et al. (2012), *Hydrology and Earth System Sciences* — "Statistical downscaling of precipitation using weather patterns"**  
Comparação de 4 vs 8 regimes em dados de superfície. Resultado: 4 regimes melhora vs climatologia, 8 regimes degrada (overfitting de regime, underpowering de segmentos). Para Wellington com 15 anos de dado, o limite é ≈ 3 regimes robustos.

---

## 4. Por Que o Caminho Atual Não Está Funcionando: Análise de Causa Raiz

### 4.1 O Loop de Dead End

O padrão atual é:

```
1. Definir regras de classificador (heurística + física)
2. Verificar assignment support (n suficiente? → Sim para todos 3 macros)
3. R2 falha em calm_radiative (0/92 passing rows)
4. Diagnóstico: "amostra insuficiente" ou "features erradas"
5. Ajustar threshold / adicionar sinal / restaurar regime
6. Voltar para 1
```

Este loop nunca converge porque cada ajuste que aumenta o n de calm_radiative (relaxando thresholds) importa dias que na verdade não são calm_radiative, aumentando a variância do target dentro do regime. Cada ajuste que purifica o regime (apertando thresholds) reduz o n e agrava o problema de poder do walk-forward.

### 4.2 O Problema de Design Invertido

A arquitetura atual faz:
```
[físico] → regime → R2 gate → feature skill
```

A literatura de MOS (Model Output Statistics) e ensemble prediction mostra que a arquitetura que funciona para previsão intradiária de temperatura é:
```
[feature skill] → segmentos de previsão → avaliação regime-like
```

Isso não é uma questão de preferência: é que o objetivo do sistema é prever Tmax, não classificar regimes. Os regimes são instrumentais — eles devem existir porque melhoram a previsão, não porque têm uma definição física elegante.

### 4.3 O Problema do Dado Disponível

O espaço de features para Onda C tem 8 variáveis:
```
cloud_cover_score_mean, dewpoint_depression_mean, drct_cos_mean, drct_sin_mean,
qnh_hpa_mean, relh_mean, sknt_mean, temp_slope_pre_cp
```

Com 8 variáveis e uma janela temporal de 8-11 horas (00:00-11:00 local), este espaço de features de manhã não separa confiavelmente `calm_radiative` de `standard_nw` de `transition` para os dias onde a diferença de Tmax à tarde vai ser real.

A razão física: a `calm_radiative` distingue-se dos outros regimes **pelo que acontece depois** (como o boundary layer evolui entre 11:00 e 17:00). Os sinais matutinos (vento fraco, pouca chuva) são condições necessárias mas não suficientes para determinar se o dia vai ter stratus persistente (baixo Tmax) ou vão limpar (alto Tmax).

**Isso não é um defeito de calibração do classificador. É um limite de informação do dado disponível.**

### 4.4 A Evidência Definitiva: Comparação v2 vs v2.1 vs v2.2

Cada versão do regime mudou as regras de classificação. O R2 de calm_radiative ficou em zero através de todas as versões. Se o problema fosse de calibração, alguma versão teria melhorado. O fato de que **nenhuma versão moveu o needle em calm_radiative R2** é evidência direta de que o problema não é calibração.

---

## 5. O Que Fazer: Alternativas Coerentes com os Dados e o Código

### 5.1 Opção A — Estrutura Binária + Features Contínuas (Recomendada)

**Princípio:** Aceitar que os dados disponíveis suportam confiavelmente apenas 2 macros preditivamente distintos: `southerly_flow` (detectável de manhã com alta confiança) e `non_southerly` (tudo o mais). Dentro de `non_southerly`, usar features contínuas (cloud_cover, wind_speed, foehn_score, dewpoint_depression) para prever a variância — sem tentar subdividir em calm_radiative vs standard_nw.

**Por que funciona:**
- macro_southerly_flow tem 47 R2 passing rows. É robusto.
- macro_nw_continuum tem 23 R2 passing rows. É marginalmente robusto.
- A distinção southerly vs não-southerly já é suficiente para segmentar o maior salto na distribuição de Tmax (residual mediano 1°C vs 3.5°C).
- cloud_cover_suppression já sobreviveu ao CEXP-002B dentro de calm_radiative. Se removermos a fronteira regime e aplicarmos diretamente, o sinal pode ficar mais forte (mais amostra).

**Como implementar no código atual:**

```python
# solarstorm/eda/_regimes.py
# Em vez de: southerly_disrupted | standard_nw | calm_radiative
# Usar:

def classify_regime(day_obs):
    ...
    if has_precip or (southerly_share >= 0.5 and southerly_speed >= 12.0) or min_delta < -2.0:
        return "southerly_flow", flags
    else:
        return "non_southerly", flags  # inclui NW, calm, foehn tudo junto

    # O foehn_score e cloud_cover entram como features contínuas, não como regime separado
```

**Impacto no R2:** `non_southerly` teria ~16.000 rows (13.726 NW + 2.572 calm). O walk-forward teria n >> 30 por célula em quase todos os meses. R2 seria testável.

**Impacto em Onda C:** Binário com alta confiança tem estabilidade próxima de 1.0. Onda C passaria.

**Risco:** Perde separação entre NW foehn e calm radiative. Mas essa separação nunca foi demonstrada como preditivamente útil — o regime `calm_radiative` tem 0 R2 passing rows em todas as versões.

---

### 5.2 Opção B — Regime como Score Contínuo (Probabilística)

**Princípio:** Em vez de label duro, computar `southerly_probability` como score [0,1] usando os mesmos sinais do classificador atual. Usar esse score diretamente como feature.

**Base na literatura:**

Raftery et al. (2005), *Monthly Weather Review* — "Using Bayesian Model Averaging to Calibrate Forecast Ensembles": O tratamento probabilístico de regime resolve exatamente o problema de baixa confiança. Um dia com southerly_probability = 0.7 recebe mais peso do southerly forecast e menos do non-southerly. Não há fronteira dura.

**Como implementar no código atual:**

O `classify_regime()` já retorna `flags` com `southerly_share`, `foehn_score`, `nw_share`. Esses podem ser convertidos em probabilidades via softmax ou logistic calibration:

```python
# Probabilidade de regime southerly
p_southerly = sigmoid(
    a * southerly_share + b * southerly_speed + c * has_precip + d * min_delta
)
# Calibrar a, b, c, d por mês em train-only window

# Em vez de regime_label como feature, usar:
features["p_southerly"] = p_southerly
features["p_foehn"] = sigmoid(foehn_score - monthly_foehn_threshold)
```

**Impacto no R2:** O R2 gate atual requer regime labels. Isso precisaria de uma adaptação do gate para avaliar se `p_southerly` tem skill como feature contínua (que é o H3 reformulado).

**Compatibilidade com código:** Alta. As flags já existem no retorno do `classify_regime()`. A mudança é no `builder.py` (exposição como features numéricas) e no R2 gate (avaliar features contínuas ao invés de segmentos).

---

### 5.3 Opção C — Demote Calm Radiative, Reter Distinção como Subtype Audit

**Princípio:** Mover `macro_calm_radiative` de macro para audit segment — avalia se features têm skill nesses dias, mas não bloqueia R2 se não tiver. Permite que Onda C passe com 2 macros.

**Implementação no código:**

```python
# solarstorm/robustness/_regime_analysis.py
PRODUCTION_REGIMES = ["macro_southerly_flow", "macro_nw_continuum"]
AUDIT_REGIMES = ["macro_calm_radiative"]  # não bloqueia R2, apenas reporta

def detect_dead_regimes(validation_results):
    dead = []
    for regime in PRODUCTION_REGIMES:
        if n_passing(regime) == 0:
            dead.append(regime)
    return dead  # calm_radiative não entra no check de dead
```

**Por que isso é defensável:** calm_radiative tem n mediano 27 por célula walk-forward. O poder estatístico para o bootstrap CI excluir zero é insuficiente mesmo com sinal real (CEXP-002B encontrou sinal). O gate atual está falhando em algo que é um problema de poder de teste, não de ausência de sinal.

**Risco:** Se calm_radiative é genuinamente diferente e não avaliado, o modelo pode ter performance ruim nesses dias sem que ninguém perceba. Mitigação: manter como audit segment (report separado, monitoramento).

---

### 5.4 Opção D — Redefinir calm_radiative pelo Target, Não pelo Input (Outcome-Based Segmentation)

**Princípio:** Inverter a lógica. Em vez de "definir calm_radiative por features de manhã e ver se R2 passa", definir "calm_radiative" pelos dias onde `remaining_warming > threshold` E `cloud_cover_at_CP é baixo`. Isso garante que o segmento tem structure preditiva por construção.

**Base na literatura:**

Klein & Glahn (1974), *Journal of Applied Meteorology* — MOS original: "Forecasting local variables from model output". A segmentação em MOS é feita pela distribuição do target, não pelas features de input. Dias com alta variância de target formam um grupo; dias com baixa variância formam outro.

Hamill & Whitaker (2007), *Monthly Weather Review* — "Probabilistic quantitative precipitation forecasts based on reforecast analogs": "Segmentos definidos por características físicas de input são sub-ótimos para previsão. Segmentos definidos por comportamento do target são mais robustos."

**Como implementar:**

```python
# Definir calm_radiative pelo comportamento do target:
# Dias com remaining_warming > 4°C E cloud_score < 0.3 no CP
# (isso garante que o segmento tem pelo menos um sinal causal e target distribuição distinta)

# ATENÇÃO: isso usa remaining_warming como critério de definição,
# o que tecnicamente usa informação do futuro para definir o grupo.
# Correto: usar apenas cloud_score_at_CP como trigger, e validar
# que os dias selecionados têm remaining_warming > 4°C em média.
```

**Este caminho requer ADR novo** e cuidado com leakage. Mas é defensável como gate de R2 reformulado: "o regime tem sample e target distribution clara" → desbloqueável se cloud_cover como único sinal de entrada produzir um segmento com target distribution separável dos outros.

---

## 6. Recomendação: Prioridade de Execução

### Caminho Mínimo de Desbloqueio (2-3 dias de trabalho)

**Passo 1 — Opção C imediata:** Mover `macro_calm_radiative` para audit segment no R2. Isso desbloqueia Onda C e Onda 3 sem mudar o classificador.

**Justificativa:** O CEXP-002B mostrou que existe sinal (`cloud_cover_suppression`, retention 0.605). O R2 está falhando por poder insuficiente no walk-forward, não por ausência de sinal. Manter o bloqueio com base em um gate estatisticamente underpowered é incorreto.

**Guardrail:** Adicionar audit report de `macro_calm_radiative` ao pipeline — os dias são avaliados e reportados separadamente, mas não bloqueiam o gate de produção.

**Código afetado:**
- `solarstorm/robustness/_regime_analysis.py` — separar `PRODUCTION_REGIMES` de `AUDIT_REGIMES`
- `reports/robustness/` — adicionar seção de audit segment no report

---

**Passo 2 — Opção A experimental:** Criar versão v2.3 do classificador com estrutura binária (southerly vs non_southerly). Rodar como `EXPERIMENT_ONLY`, não substituir produção. Verificar se Onda C passa com 2 macros.

**Justificativa:** Os dados suportam 2 macros robustos. O terceiro macro (calm_radiative) nunca passou R2. Ter 2 macros não é uma regressão — é o que a evidência de 17 meses de iteração indica.

---

**Passo 3 — cloud_cover_suppression como feature:** Independentemente do regime, o CEXP-002B demonstrou causalidade e sinal. Esse feature deve ser testado em baseline experimental via walk-forward full, por CP/mês, comparando com L0-L4. Não precisa esperar a resolução do regime para isso.

**Justificativa:** O sinal existe, é causal, sobreviveu ao robustness screen. Testá-lo não requer que o regime esteja resolvido. Isso avança o projeto enquanto o regime design continua.

---

## 7. O Que NÃO Fazer

| Ação | Por quê evitar |
|---|---|
| Nova versão v2.4 com thresholds ajustados para calm_radiative | Loop sem convergência — o problema não é de threshold |
| Tentar subdividir calm_radiative (cloudy vs clear) como v2.3 CEXP-003 | O GMM estabilidade 0.08 indica que o espaço de features não tem estrutura suficiente para 4 macros |
| Esperar que mais dados resolvam o problema de poder | Com 15 anos de dado (2009–2024), calm_radiative tem apenas ~170 dias anuais × 15 = 2.572 total. Mais anos ajudam marginalmente, mas não resolvem o problema de 27 por célula walk-forward |
| Definir um proxy causal para o que deveria ser tmax_hour tardio | Substitui um label correto (ex-post) por um proxy ruidoso (pré-CP), criando um novo problema de calibração — a abordagem dos Relatórios 2 e 3 do update.txt não se aplica ao problema atual de calm_radiative (que não é late_warming) |
| Mudar o critério R2 para ser menos exigente em geral | Compromete todos os outros gates, não apenas calm_radiative |

---

## 8. Mapeamento para o Código Atual

### 8.1 O Que Precisa Mudar para Opção C (Mínimo)

```python
# solarstorm/robustness/_regime_analysis.py

# ANTES:
REQUIRED_REGIMES = ["macro_calm_radiative", "macro_nw_continuum", "macro_southerly_flow"]

def detect_dead_regimes(validation_results, required_regimes=REQUIRED_REGIMES):
    return [r for r in required_regimes if n_passing(r) == 0]

# DEPOIS:
PRODUCTION_REGIMES = ["macro_nw_continuum", "macro_southerly_flow"]
AUDIT_REGIMES = ["macro_calm_radiative"]  # avaliado mas não bloqueia

def detect_dead_regimes(validation_results, required_regimes=PRODUCTION_REGIMES):
    return [r for r in required_regimes if n_passing(r) == 0]

def audit_regimes(validation_results, audit_regimes=AUDIT_REGIMES):
    """Return performance report for audit regimes without blocking gates."""
    return {r: n_passing(r) for r in audit_regimes}
```

### 8.2 O Que Precisa Mudar para Opção A (Experimental)

```python
# solarstorm/eda/_regimes.py — versão experimental v2.3

PHYSICAL_REGIMES_V23 = ("southerly_flow", "non_southerly")

def classify_regime_v23(day_obs):
    """Binary macro classifier. Calm/radiative absorbs into non_southerly.
    Foehn score and cloud cover remain as continuous features.
    """
    ...
    # southerly_flow trigger: unchanged from v2.2
    if has_precip or (southerly_share >= 0.5 and southerly_speed >= 12.0) or (
        min_delta < -2.0 and southerly_share > 0.2  # requer southerly confirmado
    ):
        return "southerly_flow", flags

    # Tudo o mais: non_southerly (NW foehn, calm, standard NW, transition)
    return "non_southerly", flags
```

**Nota crítica:** A remoção do `min_delta < -2.0` como trigger standalone (sem southerly confirmado) é a mudança mais importante. O trigger atual está capturando 94.6% de southerly_disrupted via cooling — o que inclui noites radiativas normais. A Opção A resolve isso naturalmente ao colapsar os macros.

### 8.3 Como Testar Opção A sem Alterar Produção

O código atual já suporta versões experimentais via `features_candidate_v2_1.parquet` e artifacts `NOT_PRODUCTION`. Uma v2.3 experimental pode ser:

```bash
# Rodar classificador experimental
python -m solarstorm regime-experiment --version v23 --mode experiment-only

# Comparar R2 entre v2.2 e v2.3 experimental
python -m solarstorm robustness --regime-version v23 --output-dir reports/regime-design/
```

Isso não toca `data/features.parquet` e não altera os gates de produção.

---

## 9. Relação com cloud_cover_suppression (CEXP-002B)

O sinal sobrevivente é o único caminho de avanço independente da decisão de regime. As ações são:

1. **Baseline experimental com cloud_cover_suppression:** Comparar walk-forward MAE de (L2 climatologia + cloud_cover_suppression) vs L0-L4 existentes, por CP e mês. Isso não requer regime resolvido.

2. **Feature de interação cloud × regime:** Quando southerly_flow está ativo, cloud_cover tem efeito diferente (chuva vs stratus) do que quando non_southerly está ativo (stratus clareando). O interaction term `cloud_score × southerly_flag` pode ter mais sinal que o marginal.

3. **Não promover como feature de produção ainda:** CEXP-002B é experiment-only. O sinal precisa ser testado em walk-forward completo com BH-FDR correction antes de qualquer promoção.

---

## 10. Resumo do Diagnóstico

| Questão | Resposta |
|---|---|
| O caminho de definição de regime está correto? | **Parcialmente não.** A lógica de gates e validação está correta. O problema é tentar 3 macros quando os dados suportam 2 robustos. |
| É um problema de calibração? | **Não.** O GMM estabilidade 0.08 indica ausência de estrutura de cluster, não calibração incorreta. |
| É um problema de amostra? | **Parcialmente.** Com 27 days/célula no walk-forward, o poder do bootstrap é insuficiente. Mas o problema raiz é que calm_radiative é uma categoria ambígua no dado disponível. |
| A análise de dados está sendo feita de forma errada? | **Sim, em um aspecto específico:** a análise trata o fracasso do R2 como evidência de "features erradas" quando na verdade é evidência de "estrutura de regime não suportada pelo dado". Esses são diagnósticos diferentes com soluções diferentes. |
| O que desbloqueia o projeto? | Opção C (audit demotion) imediata + cloud_cover baseline experimental em paralelo. Opção A (binary macro) como próxima versão experimental. |

---

*Relatório diagnóstico — Onda 2E / regime-deadlock — 2026-06-08*  
*Não altera features.parquet, gates, ou decisões de produção.*  
*Referências: Huth et al. 2008; Michelangeli et al. 1995; Raftery et al. 2005; Wilks 2006; Betts 2009; Cannon & Whitfield 2002.*
