-- Camada CURATED (BigQuery) — DRE Gerencial consolidado por loja e competencia.
-- Consome staging.fechamento_financeiro, que ja chega padronizado entre lojas.
--
-- Pratica pedida na JD: SQL avancado (CASE/aggregation condicional, CTE).
-- Note a semelhanca direta com o "Elaboracao de DRE Gerencial" da sua
-- experiencia real — e exatamente esse o ponto de conectar na entrevista.
--
-- Sem PARTITION BY aqui de proposito: a tabela tem dezenas de linhas (uma
-- por loja/competencia), nao milhoes. Particionar uma tabela desse tamanho
-- adiciona overhead de metadado sem ganho de performance — a decisao
-- certa de um Analytics Engineer Senior nao e "particionar tudo", e saber
-- quando NAO vale a pena. CLUSTER BY loja_id ainda ajuda, porque a maioria
-- dos relatorios filtra por loja.

-- BigQuery nao deixa CREATE OR REPLACE mudar a especificacao de clustering
-- de uma tabela que ja existe sem clustering (mesma regra da particao) —
-- precisa DROP antes.
DROP TABLE IF EXISTS `curated.dre_gerencial`;

CREATE TABLE `curated.dre_gerencial`
CLUSTER BY loja_id
OPTIONS(description="DRE gerencial consolidado por loja e competencia. Camada curated do projeto Vena Analytics Sim.")
AS
WITH base AS (
    SELECT
        loja_id,
        competencia,
        SUM(CASE WHEN categoria = 'receita' THEN valor ELSE 0 END) AS receita_total,
        SUM(CASE WHEN categoria = 'despesa' THEN valor ELSE 0 END) AS despesa_total
    FROM `staging.fechamento_financeiro`
    GROUP BY loja_id, competencia
)
SELECT
    loja_id,
    competencia,
    receita_total,
    despesa_total,
    receita_total - despesa_total                              AS resultado_liquido,
    SAFE_DIVIDE(receita_total - despesa_total, receita_total)   AS margem_liquida_pct
FROM base;

-- CREATE OR REPLACE TABLE ... AS SELECT nao aceita OPTIONS por coluna
-- inline (o schema vem da propria SELECT) — por isso a descricao de cada
-- coluna e um ALTER TABLE separado, rodado logo em seguida.
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN loja_id SET OPTIONS(description="ID da loja");
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN competencia SET OPTIONS(description="Competencia no formato YYYY-MM");
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN receita_total SET OPTIONS(description="Soma de todos os lancamentos de categoria 'receita' no periodo, em R$");
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN despesa_total SET OPTIONS(description="Soma de todos os lancamentos de categoria 'despesa' no periodo, em R$");
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN resultado_liquido SET OPTIONS(description="receita_total - despesa_total, em R$");
ALTER TABLE `curated.dre_gerencial` ALTER COLUMN margem_liquida_pct SET OPTIONS(description="resultado_liquido / receita_total; NULL se receita_total for zero (via SAFE_DIVIDE)");
