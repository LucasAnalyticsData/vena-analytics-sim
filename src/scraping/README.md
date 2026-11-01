# Scraping (Semana 2)

Fonte de "Web Scraping" da JD. Em vez de duplicar esforço, este módulo
reaproveita o scraper que você já está construindo no projeto de monitor
de preços de concorrentes — aponte a saída dele para
`staging.precos_concorrente` (ver `src/sql/schema_staging.sql`).

Checklist de integração:
- [ ] Exportar a saída do scraper existente em formato tabular (CSV/JSON)
      com as colunas: `produto_nome`, `concorrente`, `preco_coletado`, `data_coleta`
- [ ] Criar `load_scraping_to_gcs.py` aqui, no mesmo padrão de
      `src/ingestion/load_csv_to_gcs.py`
- [ ] Criar o asset Dagster `raw_precos_concorrente` em
      `src/dagster_project/assets.py`, seguindo o mesmo padrão dos outros raw assets
- [ ] Decidir frequência de coleta (diária? a cada X horas?) — isso vira
      o schedule do Dagster, outro ponto que a JD cobra
      ("gerenciar e otimizar a execução de fluxos de dados")

Não construa um scraper novo do zero aqui — é retrabalho.
