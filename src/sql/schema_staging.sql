-- Camada STAGING (BigQuery)
-- Objetivo: padronizar o schema entre fontes heterogeneas (API, CSV, scraping,
-- banco transacional) antes de qualquer indicador de negocio ser calculado.
-- Aqui ainda nao ha regra de negocio, so padronizacao e tipagem.
--
-- Particionamento/clustering: BigQuery nao permite ALTER TABLE pra adicionar
-- particao numa tabela existente — por isso DROP + CREATE em vez de CREATE
-- IF NOT EXISTS. Rodar este arquivo apaga e recria as 3 tabelas; o Dagster
-- repopula ao materializar de novo.

CREATE SCHEMA IF NOT EXISTS `staging`;

-- Vendas, vindas da API mock (fonte: src/mock_api) e do Postgres transacional.
-- Particionada por data_venda (particao de negocio: "quando a venda
-- aconteceu") e clusterizada por loja_id — a maioria das consultas do
-- projeto filtra ou agrupa por loja, entao o BigQuery organiza fisicamente
-- os dados pra essas queries lerem menos bytes.
DROP TABLE IF EXISTS `staging.vendas`;
CREATE TABLE `staging.vendas`
(
    loja_id         INT64 NOT NULL OPTIONS(description="ID da loja (FK conceitual para lojas.loja_id na fonte transacional)"),
    produto_id      INT64 OPTIONS(description="ID do produto vendido"),
    produto_nome    STRING OPTIONS(description="Nome do produto no momento da venda (snapshot, nao normalizado)"),
    categoria       STRING OPTIONS(description="Categoria do produto, ex: perfumaria_feminina"),
    quantidade      INT64 NOT NULL OPTIONS(description="Quantidade vendida nessa linha"),
    preco_unitario  NUMERIC NOT NULL OPTIONS(description="Preco unitario no momento da venda, em R$"),
    data_venda      DATE NOT NULL OPTIONS(description="Data em que a venda ocorreu (particao da tabela)"),
    fonte           STRING NOT NULL OPTIONS(description="Origem do dado: 'api_mock' ou 'postgres_transacional'"),
    data_ingestao   TIMESTAMP NOT NULL OPTIONS(description="Momento em que o pipeline gravou esta linha")
)
PARTITION BY data_venda
CLUSTER BY loja_id, produto_id
OPTIONS(description="Vendas diarias padronizadas, consolidando API mock e banco transacional. Camada staging do projeto Vena Analytics Sim.");

-- Fechamento financeiro, vindo do CSV mensal de cada loja.
-- `competencia` e STRING ('YYYY-MM'), nao DATE — por isso particionamos por
-- data_ingestao (quando o dado chegou), nao por competencia. E um padrao
-- comum quando o campo de negocio nao e um tipo particionavel nativamente.
DROP TABLE IF EXISTS `staging.fechamento_financeiro`;
CREATE TABLE `staging.fechamento_financeiro`
(
    loja_id        INT64 NOT NULL OPTIONS(description="ID da loja"),
    competencia    STRING NOT NULL OPTIONS(description="Competencia no formato YYYY-MM"),
    categoria      STRING NOT NULL OPTIONS(description="'receita' ou 'despesa'"),
    tipo           STRING NOT NULL OPTIONS(description="'credito' ou 'debito'"),
    descricao      STRING OPTIONS(description="Descricao livre do lancamento, ex: 'Aluguel'"),
    valor          NUMERIC NOT NULL OPTIONS(description="Valor do lancamento em R$, sempre positivo (sinal vem de categoria/tipo)"),
    fonte          STRING NOT NULL OPTIONS(description="Origem do dado: 'csv_fechamento_mensal'"),
    data_ingestao  TIMESTAMP NOT NULL OPTIONS(description="Momento em que o pipeline gravou esta linha (particao da tabela)")
)
PARTITION BY DATE(data_ingestao)
CLUSTER BY loja_id
OPTIONS(description="Fechamento financeiro mensal por loja, origem CSV. Camada staging do projeto Vena Analytics Sim.");

-- Preco de concorrente, vindo do scraping (semana 2 — reaproveita o
-- projeto de monitor de precos).
DROP TABLE IF EXISTS `staging.precos_concorrente`;
CREATE TABLE `staging.precos_concorrente`
(
    produto_nome    STRING NOT NULL OPTIONS(description="Nome do produto monitorado"),
    concorrente     STRING NOT NULL OPTIONS(description="Nome/identificador do concorrente monitorado"),
    preco_coletado  NUMERIC NOT NULL OPTIONS(description="Preco coletado no momento da raspagem, em R$"),
    data_coleta     TIMESTAMP NOT NULL OPTIONS(description="Momento da coleta (particao da tabela)"),
    fonte           STRING NOT NULL OPTIONS(description="Origem do dado: 'scraping'")
)
PARTITION BY DATE(data_coleta)
CLUSTER BY produto_nome
OPTIONS(description="Precos de concorrentes coletados via scraping. Camada staging do projeto Vena Analytics Sim.");
