# Arquitetura — Vena Analytics Sim

Este documento detalha decisões arquiteturais que não cabem no README —
trade-offs, limites conhecidos e o que mudaria em escala de produção real.

## Fluxo de dado, passo a passo

1. **Ingestão (raw)** — três fontes heterogêneas, três formatos diferentes
   (JSON de API, CSV, HTML de scraping), unificadas em DataFrames pandas
   dentro de assets Dagster independentes (`raw_vendas_api`,
   `raw_fechamento_financeiro`, `raw_precos_concorrente`). Nenhuma lógica de
   negócio aqui — só coleta.
2. **Padronização (staging)** — cada asset `staging_*` recebe o DataFrame raw
   correspondente, aplica tipagem (ex: `Decimal` pra colunas monetárias,
   `datetime` pra datas), adiciona metadados de proveniência (`fonte`,
   `data_ingestao`) e grava em uma tabela BigQuery já com schema fixo
   (`src/sql/schema_staging.sql`) — não deixamos o BigQuery inferir schema
   via autodetect, porque inferência pode divergir silenciosamente do tipo
   real esperado (ex: DATE virando STRING), erro que só aparece mais tarde.
3. **Regra de negócio (curated)** — três tabelas, cada uma rodada
   manualmente via SQL após o pipeline Dagster popular o staging:
   `curated_dre_gerencial.sql` (margem líquida por loja/competência),
   `curated_curva_abc.sql` (classificação ABC por faturamento acumulado) e
   `curated_comparativo_precos.sql` (gap entre preço próprio e preço de
   mercado). Essas tabelas são o contrato com quem consome (BI, outros
   times); staging nunca é consultado fora da engenharia.
4. **Consumo (BI)** — Looker Studio lê direto de `curated.*`.

## Por que Software-Defined Assets (e não jobs imperativos)

Num pipeline imperativo tradicional (ex: um script sequencial, ou uma DAG
Airflow baseada em `PythonOperator`), você descreve *passos*: "rode essa
função, depois essa, depois essa". No Dagster, cada função decora o *dado*
que produz como retorno, e as dependências vêm dos parâmetros de tipo da
própria assinatura da função — o grafo de execução é derivado
automaticamente, não desenhado à mão. Consequência prática: dá pra testar
qualquer asset isoladamente com `build_asset_context()`, sem subir o
orquestrador inteiro, e o lineage (quem depende de quem) está sempre
sincronizado com o código, nunca desatualizado numa documentação à parte.

## Classificação ABC — a armadilha do acumulado inclusivo vs. exclusivo

A regra de negócio padrão de Curva ABC classifica um item como:
- **A** se está entre os produtos que, somados em ordem decrescente de
  faturamento, respondem por até 80% do total;
- **B** até 95%;
- **C** o restante.

A armadilha: se você calcular o "percentual acumulado" *incluindo* o próprio
produto na soma (acumulado inclusivo), um único produto responsável por 97%
do faturamento de uma loja cairia em **C** — porque o acumulado dele já
passa de 95% no momento em que ele é somado. Isso está errado: esse produto
é obviamente o maior responsável pelo faturamento, deveria ser **A**.

A correção: classificar pelo acumulado *antes* daquele produto entrar na
soma (acumulado exclusivo — `ROWS BETWEEN UNBOUNDED PRECEDING AND 1
PRECEDING` em SQL, ou o equivalente deslocado em pandas). O primeiro produto
sempre começa com acumulado anterior = 0%, então sempre cai em A,
independente de quão dominante seu faturamento for.

## Idempotência: por que TRUNCATE, não APPEND

Documentado também no README, mas vale o detalhe técnico aqui: um pipeline
de produção precisa ser seguro pra re-executar. Com `WRITE_APPEND`, rodar o
mesmo job duas vezes (cenário comum durante desenvolvimento, debug, ou um
retry automático depois de falha) duplica os dados — e o pior tipo de bug:
sem erro, sem log de alerta, só um número errado em produção. `WRITE_TRUNCATE`
garante que cada materialização reflete exatamente o estado atual da fonte,
nunca acumula execuções anteriores.

## Comparativo de preços: por que o JOIN é só por produto, não por loja

`staging.precos_concorrente` não tem `loja_id` — preço de concorrente é
informação de mercado (o que o concorrente cobra, de modo geral), não uma
variação por loja sua. Por isso `curated_comparativo_precos.sql` junta
`staging.vendas` (que tem `loja_id`) com `staging.precos_concorrente` (que
não tem) usando só `produto_nome` como chave — o resultado é "preço desta
loja, para este produto, comparado ao preço médio de mercado para o mesmo
produto". Uma consequência direta: nomes de produto entre as duas fontes
precisam bater exatamente, byte a byte — isso quebrou na primeira versão do
projeto (o catálogo do site mock de concorrente usava nomes parecidos, mas
não idênticos, ao catálogo real do mock API) e foi corrigido alinhando os
nomes entre as duas fontes.

## Limites conhecidos desta versão (escopo de demo, não produção)

- **Schedule, não evento real** — o pipeline roda por cron diário
  (`0 6 * * *`), não por um gatilho de "arquivo novo chegou". Eventarc já
  dispara a Cloud Function de validação por evento; o próximo passo natural
  é um sensor Dagster no mesmo tópico Pub/Sub, substituindo o schedule por
  reação em tempo real.
- **Scraping contra alvo mockado** — pra garantir confiabilidade da demo
  (sem depender de disponibilidade/ToS de site externo real), o scraper
  aponta pra um serviço FastAPI local que simula um catálogo de concorrente.
  A lógica de parsing (`_parse_catalogo_html`) é desacoplada da chamada de
  rede justamente pra poder trocar o alvo (incluindo um site real) sem
  reescrever a lógica de extração.
- **Sem autenticação no Cloud Run do mock API** — `--allow-unauthenticated`
  é aceitável aqui porque o dado é 100% sintético e não há nada sensível
  exposto; numa API de produção real isso exigiria IAM/autenticação
  (service-to-service auth via Cloud Run invoker role, por exemplo).
- **CI sem deploy automatizado** — ver tabela de decisões no README
  (WIF documentado como próximo passo).
- **Comparativo de preço sem granularidade de loja** — o preço de
  concorrente coletado hoje é único por produto (mercado), não varia por
  loja/região; isso é limitação do mock, não da arquitetura do `JOIN`.

## O que mudaria numa escala de produção real (não implementado aqui, por propósito)

- Particionamento por mês (não por dia) se o volume de dado crescesse muito além do escopo de demo, pra não estourar o limite de partições do BigQuery.
- Alertas automáticos quando um `asset_check` falha (hoje só aparece na UI do Dagster — em produção, isso dispararia Slack/PagerDuty).
- Observabilidade centralizada (Cloud Logging + Cloud Monitoring com dashboards de SLA de pipeline), não só logs locais do Dagster.
- Ambientes separados (dev/staging/prod) com datasets BigQuery distintos, em vez de um único projeto GCP pra tudo.
