# Sumario executivo do projeto Wellington Tmax

Gerado em: 2026-06-11  
Status: `EXPERIMENT_ONLY`

Este documento consolida o estado atual do projeto de previsao de Tmax para Wellington antes de qualquer promocao operacional. Nenhum resultado abaixo libera producao, EV, pricing, shadow trading ou execucao automatizada. O valor do trabalho ate aqui e experimental: medir baselines, separar ganhos reais de ruido e definir a proxima iteracao com Open-Meteo sem vazamento temporal.

## Conclusao executiva

O projeto ja tem dois baselines relevantes.

O baseline local pre-Open-Meteo e a Onda 3F pooled temporal/regime: ela usa pooling entre CPs e meses, features ciclicas de tempo, macro-regimes binarios e interacoes continuas com regime. Em validacao aninhada 2023-2025, foi selecionada em todos os folds e obteve MAE medio de 1.062 C. Esse e o baseline local atual.

O baseline experimental com Open-Meteo ainda nao e final de producao, mas ja e claramente superior em MAE. A melhor evidencia consolidada atual vem da revisao expandida 2022-2025: a politica selecionada obteve MAE 0.783 C contra 0.824 C do modelo aumentado bruto, uma melhora de 0.040 C, com ganho de 1.30 pp em exact bracket. A politica `always_season` foi a melhor observada globalmente, com MAE 0.762 C, mas ainda deve ser carregada como candidata, nao como decisao final isolada.

O maior avanco tecnico nao foi simplesmente adicionar mais features. Foi mudar a arquitetura de avaliacao: primeiro estabelecer um harness nested walk-forward, depois usar pooling para reduzir fragmentacao, e so entao integrar NWP/Open-Meteo com auditoria de cobertura, calibracao e maturidade causal.

## Linha do tempo dos modelos

| Etapa | Ideia testada | Resultado principal | Decisao |
| --- | --- | ---: | --- |
| Onda 3 baseline local | Ridge contra media de treino | MAE 1.349 vs null 2.812 | Seguir para Onda 4/model rerun |
| Onda 3D | Interacoes com macro-regime binario | -0.030 MAE vs sem interacao | Ganho pequeno, mas real |
| Sensibilidade 2009 vs 2012 | Remover anos historicos esparsos | -0.002 MAE, -0.09 pp exact | Nao resolveu sozinho |
| Onda 3F pooled | Pooling por CP/mes/regime com features ciclicas | MAE 1.062, any-CP exact 44.43%, CP23 exact 31.48% | Baseline local forte |
| Onda 3H nested | Selecao Onda 3D vs Onda 3F | Onda 3F selecionada em 3/3 folds | Harness nested promovido |
| Open-Meteo piloto | Features NWP adicionadas ao modelo | -0.280 MAE vs local em mesmas linhas | Promover para nova iteracao experimental |
| Open-Meteo nested inicial | Selecao local vs augmented | MAE selecionado 0.851, mas so 1 fold | Evidencia promissora, limitada |
| Calibracao inicial | Bias recente/global | MAE 0.826 selecionado, augmented simples 0.761 | Manter em revisao |
| Forense OM-M6 | Diagnostico por ano/regime | Calibracao recente piorou non-southerly 2025 | Falha de drift, nao so media |
| Cobertura 2022-2025 | Backfill para mais folds | 2 folds estritos disponiveis | Desbloqueou avaliacao mais robusta |
| Selecao defensiva 2022-2025 | Politicas calibradas com gate | MAE 0.782 vs augmented 0.824 | Promover para proxima iteracao experimental |
| Revisao expandida OM-M13 | Politicas recentes/sazonais/selecionadas | selected 0.783, always_season 0.762 | Levar ambas adiante |
| Forward collection OM-M14 | Coleta causal futura | 1 linha `pending`, auditoria causal `EXPERIMENT_ONLY` | Comecar maturacao sem leakage |

## Baseline local pre-Open-Meteo

A primeira comparacao util foi simples: um Ridge local contra uma media de treino. O Ridge reduziu o MAE de 2.812 C para 1.349 C, mostrando que as features locais tinham sinal real. Esse resultado, porem, ainda nao respondia se a arquitetura era robusta por tempo, mes, CP e regime.

A Onda 3D adicionou interacoes com macro-regime binario e melhorou o MAE medio em 0.030 C contra a versao sem interacao. Foi uma melhora modesta, mas coerente com a hipotese meteorologica: dois macro-regimes funcionam melhor como switch estrutural, enquanto `foehn_score`, supressao de nuvem e outras variaveis continuas explicam a variancia residual.

A tentativa de simplesmente truncar o treino para 2012 nao foi a grande solucao. A remocao do periodo 2009-2011 praticamente empatou com a janela legada: -0.002 C em MAE e -0.09 pp em exact bracket. A conclusao e importante: os dados historicos esparsos eram um risco de amostragem, mas nao eram a causa principal da dificuldade de modelar regimes.

O salto local veio com a Onda 3F: em vez de fatiar demais por mes e CP, o modelo passou a compartilhar dados via features ciclicas de mes, dia do ano e CP, mantendo regimes e interacoes como features. Nos testes 2023-2025:

| Ano de teste | MAE Onda 3F | Any-CP exact | CP23 exact |
| --- | ---: | ---: | ---: |
| 2023 | 1.040 | 44.93% | 31.78% |
| 2024 | 1.070 | 43.72% | 31.15% |
| 2025 | 1.077 | 43.84% | 30.41% |
| Media nested | 1.062 | - | - |

Na auditoria direta contra Onda 3D, a Onda 3F melhorou MAE em 0.111 C e melhorou CP23 exact em 1.55 pp, mas perdeu 0.73 pp em any-CP exact. Isso criou a disciplina correta: MAE sozinho nao basta, e bracket exact deve continuar como metrica de decisao secundaria.

## Regimes e fatiamento

A evidencia ate aqui favorece dois macro-regimes discretos, nao porque Wellington tenha so dois estados meteorologicos, mas porque o volume de dados nao sustenta muitos regimes discretos independentes em walk-forward. A tentativa conceitual de regimes ricos e muito fatiamento por CP x mes x regime reduzia suporte demais e criava celulas historicas pequenas.

A solucao que funcionou melhor foi pooling: manter `southerly_flow` e `non_southerly` como macro-switches, e usar features continuas dentro deles. Isso permite que `foehn_score`, supressao de nuvem, tendencia de pressao, aquecimento matinal e interacoes com macro-regime capturem caudas quentes/frias sem criar classes discretas fragilizadas.

Em Onda 3F, os regimes tiveram desempenho semelhante:

| Macro-regime | MAE | Exact bracket por linha |
| --- | ---: | ---: |
| `macro_non_southerly` | 1.065 | 30.51% |
| `macro_southerly_flow` | 1.054 | 32.01% |

Nao ha evidencia de que um terceiro regime discreto teria sido mais robusto com os dados atuais. Ha evidencia de que features continuas e pooling moveram o projeto para frente.

## Integracao Open-Meteo

A integracao Open-Meteo trouxe o maior ganho de ordem de grandeza do projeto. O piloto all-CP reduziu MAE em 0.280 C contra o modelo local nas mesmas linhas. Em nested inicial, o candidato com Open-Meteo foi selecionado, com MAE 0.851 C contra 1.092 C do local. A limitacao era seria: havia apenas 1 fold externo estrito.

A investigacao multi-provider mostrou que os provedores brutos tinham sinal, mas tambem vies frio amplo:

| Provedor bruto | Linhas | MAE | Bias assinado | Exact bracket |
| --- | ---: | ---: | ---: | ---: |
| `icon_seamless` | 2848 | 1.084 | -0.697 | 28.65% |
| `gem_global` | 2848 | 1.167 | -0.613 | 24.02% |
| `ecmwf_ifs025` | 2788 | 1.399 | -1.242 | 17.50% |
| `gfs_seamless` | 4304 | 1.421 | -1.202 | 15.24% |
| `ecmwf_aifs025_single` | 1268 | 1.750 | -1.635 | 15.77% |
| `jma_seamless` | 4384 | 1.787 | -1.659 | 15.24% |

Isso justificou calibracao por bias, mas a calibracao global/recent-bias nao foi automaticamente melhor. A forense OM-M6 mostrou o problema: a calibracao recente teve MAE 0.773 contra 0.761 do augmented no pareamento principal, e piorou especificamente `2025|macro_non_southerly` em 0.107 C de MAE e -6.47 pp em exact bracket. O erro era drift por ano/regime, nao falta de media global.

O backfill de cobertura 2022-2025 foi o desbloqueio metodologico. Ele aumentou a validacao para 2 folds estritos. Com isso, a selecao defensiva calibrada obteve:

| Modelo/politica | MAE medio |
| --- | ---: |
| Local | 1.057 |
| GFS previous runs bruto | 1.426 |
| Open-Meteo augmented | 0.824 |
| Calibrado selecionado | 0.782 |

Na revisao expandida OM-M13, a politica selecionada passou o gate definido: MAE 0.783 contra 0.824 do augmented, ganho de 0.040 C, exact bracket +1.30 pp, CP23 sem degradacao e sem piora material de regime. Ao mesmo tempo, a politica `always_season` foi a melhor observada globalmente, com MAE 0.762 e exact bracket 42.42%. A decisao correta e levar `selected_policy` e `always_season` para a proxima iteracao, com avaliacao causal futura.

## Experimentos que falharam ou ficaram bloqueados

1. Fatiamento fino por mes x CP x regime: tecnicamente atraente, mas reduziu suporte demais e fragilizou regimes raros. O aprendizado foi migrar para pooling com representacoes ciclicas.

2. Truncar 2009-2011 como solucao principal: melhorou MAE so 0.002 C e piorou exact bracket em 0.09 pp. O problema real era mais arquitetura/avaliacao do que apenas anos esparsos.

3. Calibracao recente/global: parecia promissora em media, mas falhou em slices, especialmente non-southerly em 2025. O aprendizado foi calibrar menos globalmente e usar regras defensivas de selecao.

4. Open-Meteo Single Runs: ficou bloqueado por contrato de request/disponibilidade. A estrategia atual prioriza endpoints com cobertura auditavel e maturidade temporal.

5. Promocao com 1 fold: os primeiros resultados Open-Meteo eram fortes, mas insuficientes para decisao. O projeto so avancou quando a cobertura 2022-2025 permitiu 2 folds estritos.

## O que realmente moveu os resultados

Os ganhos mais importantes vieram de quatro mudancas:

1. Nested walk-forward como harness de selecao, evitando escolher modelos diretamente no teste.

2. Pooling temporal/regime em vez de fatiamento excessivo por mes, CP e regime.

3. Open-Meteo/NWP como fonte externa de sinal, com auditoria de disponibilidade por endpoint, provedor e periodo.

4. Calibracao defensiva e forense por ano/regime, em vez de confiar em bias global.

## Estado atual e proximas entregas

O baseline local atual e Onda 3F, com MAE nested 1.062 C em 2023-2025. O melhor baseline experimental com Open-Meteo e a familia expandida 2022-2025, onde a politica selecionada atinge MAE 0.783 C e a melhor politica observada (`always_season`) atinge 0.762 C. A melhora real contra o local e grande, mas ainda experimental: aproximadamente 0.279 C quando se compara Onda 3F local 1.062 contra a politica selecionada 0.783, e aproximadamente 0.300 C contra `always_season`.

As proximas entregas mensuraveis devem ser:

1. Rodar a proxima iteracao carregando `selected_policy` e `always_season` como candidatas lado a lado, sem decidir por uma so no papel.

2. Expandir a coleta forward OM-M14 ate haver linhas maduras suficientes, preservando auditoria causal e marcando linhas `pending`, `usable` ou `blocked`.

3. Reportar MAE, exact bracket, any-CP exact e CP23 exact por ano, mes e macro-regime para confirmar se o ganho nao esta concentrado em um unico slice.

4. Manter qualquer integracao Open-Meteo em `EXPERIMENT_ONLY` ate que a politica venca em folds suficientes e em dados forward maduros.

## Fontes internas principais

- `reports/onda3/onda3_baseline_model_report_v1.md`
- `reports/onda3-interactions/onda3_interaction_decision_update_v1.csv`
- `reports/onda3-train-start-sensitivity/onda3_train_start_decision_update_v1.csv`
- `reports/onda3-pooled/onda3_pooled_model_report_v1.md`
- `reports/onda3-audit-comparison/onda3_audit_decision_update_v1.csv`
- `reports/onda3-nested-validation/onda3_nested_test_selected_summary_v1.md`
- `reports/onda3-open-meteo-pilot-daily-all-cp/onda3_open_meteo_pilot_decision_update_v1.csv`
- `reports/onda3-open-meteo-nested-validation-daily-all-cp/onda3_open_meteo_nested_decision_update_v1.csv`
- `reports/open-meteo-provider-error-atlas-multi-provider/open_meteo_provider_error_metrics_v1.csv`
- `reports/open-meteo-forensics/open_meteo_forensics_decision_v1.csv`
- `reports/open-meteo-coverage-expansion-2022-2025/open_meteo_coverage_expansion_decision_v1.csv`
- `reports/onda3-open-meteo-defensive-selection-2022-2025/onda3_open_meteo_calibrated_nested_decision_update_v1.csv`
- `reports/open-meteo-expanded-decision-review-2022-2025/open_meteo_expanded_policy_decision_v1.csv`
- `reports/open-meteo-expanded-decision-review-2022-2025/open_meteo_expanded_policy_metrics_v1.csv`
- `reports/open-meteo-forward-collection/open_meteo_forward_collection_report_v1.md`
