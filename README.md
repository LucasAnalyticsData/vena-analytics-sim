# Painel Multi-Loja — Projeto de estudo (Analytics Engineering / GCP)

> Projeto pessoal de estudo, construído com **dados 100% sintéticos**.
> Nenhum dado, estrutura de planilha ou lógica de negócio real de qualquer
> empregador foi usado como base. Qualquer semelhança com números reais é
> coincidência de projeto fictício.

## Objetivo

Simular, em escala reduzida, o fluxo de dados de uma operação de varejo/
franquia multi-loja: ingestão heterogênea → padronização → indicadores de
negócio (DRE consolidado, Curva ABC, ruptura de estoque) → BI.

Construído para praticar, na prática e não só em teoria:
- Python e SQL avançado
- GCP: Cloud Storage, Cloud Functions, Cloud Run, Pub/Sub, BigQuery
- Orquestração com Dagster
- Ingestão via API, Web Scraping, arquivo e banco transacional
- CI/CD básico
- Uso de IA Generativa como parte do fluxo de desenvolvimento (ver `docs/uso-ia.md`)

## Arquitetura

```
[API mock "ERP"] ──┐
[Scraping preço]  ──┼─► Cloud Storage (raw) ─► Cloud Function (valida/move) ──┐
[CSV fechamento]  ──┤                                                         ├─► BigQuery (staging)
[Postgres transac.]──┘                                                        │
                                                                                ▼
                                                              BigQuery (curated: DRE, Curva ABC, ruptura)
                                                                                │
                                                                                ▼
                                                                      Looker Studio / Power BI
```

Dagster orquestra o pipeline completo (raw → staging → curated), chamando
os serviços GCP via Python. Pub/Sub desacopla o momento em que o dado chega
do momento em que é processado.

## Roteiro de construção (3 semanas)

- [x] **Semana 1 — Fundamentos**
  - [x] Postgres local simulando ERP transacional (`docker-compose.yml`)
  - [x] API mock de vendas por loja (`src/mock_api`)
  - [x] Ingestão de CSV/API para Cloud Storage
  - [x] Cloud Function validando/movendo arquivo pousado (`src/functions/validar_arquivo_raw`)
  - [x] BigQuery: camada staging com schema único entre "lojas", particionada e clusterizada
  - [ ] Dashboard inicial no Looker Studio
- [x] **Semana 2 — Orquestração**
  - [x] Dagster orquestrando os assets (raw → staging → curated)
  - [x] Asset checks de qualidade de dado (`src/dagster_project/checks.py`)
  - [x] Schedule diário automático
  - [ ] Pub/Sub como gatilho de processamento (hoje só o schedule; evento ainda é TODO)
  - [ ] Scraping real (reaproveitando o projeto de monitor de preços)
- [ ] **Semana 3 — Produção**
  - [ ] Cloud Run como serviço próprio de ingestão
  - [ ] CI/CD via GitHub Actions (hoje só roda teste, falta o deploy)
  - [x] Documentação do uso de IA Generativa no desenvolvimento (`docs/uso-ia.md`)
  - [ ] README técnico final com decisões de arquitetura

## Segurança e governança (adicionado fora do roteiro original)

- Service Account dedicada (`vena-sim-pipeline`) com papéis mínimos
  (`bigquery.dataEditor`, `bigquery.jobUser`, `storage.objectAdmin` só no
  bucket do projeto), configurada via impersonation — sem chave JSON
  baixada no disco.
- Lifecycle policy no bucket raw (`infra/gcs_lifecycle.json`): move pra
  classe fria depois de 30 dias, apaga depois de 90.
- Descrição de coluna em todas as tabelas BigQuery (staging e curated),
  visível em qualquer client que leia o schema.

## Estrutura do repositório

```
├── docker-compose.yml       # Postgres local simulando ERP
├── requirements.txt
├── .env.example
├── data/sample/              # dados sintéticos de exemplo
├── src/
│   ├── mock_api/              # FastAPI simulando "ERP de loja"
│   ├── ingestion/              # scripts de carga para GCS/BigQuery
│   ├── scraping/                # integração com o monitor de preços
│   ├── dagster_project/          # orquestração (assets, definitions)
│   └── sql/                       # DDL das camadas staging/curated
└── .github/workflows/              # CI/CD (semana 3)
```

## Dados

Todos os dados em `data/sample/` são gerados artificialmente para este
projeto. Nenhum valor reflete faturamento, custo ou estrutura real de
qualquer empresa.
