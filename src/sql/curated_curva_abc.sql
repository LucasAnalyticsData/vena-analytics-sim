-- Camada CURATED (BigQuery) — Curva ABC de produtos por loja.
-- Classifica produtos em A (80% do faturamento), B (proximos 15%) e C (5% restante),
-- a partir de staging.vendas.
--
-- Pratica pedida na JD: window functions (SUM() OVER, percentual acumulado).
-- Conecta direto com "Analise de dados de compras para revenda, com
-- classificacao de produtos por Curva ABC" da sua experiencia real na Rancho Dallas.
--
-- CLUSTER BY loja_id, classe_abc: relatorios tipicos filtram "me mostra os
-- produtos classe A da loja X" — clusterizar pelas duas colunas juntas
-- deixa esse filtro mais barato de ler.

-- BigQuery nao deixa CREATE OR REPLACE mudar a especificacao de clustering
-- de uma tabela que ja existe sem clustering — precisa DROP antes.
DROP TABLE IF EXISTS `curated.curva_abc_produtos`;

CREATE TABLE `curated.curva_abc_produtos`
CLUSTER BY loja_id, classe_abc
OPTIONS(description="Classificacao ABC de produtos por loja, a partir do faturamento acumulado. Camada curated do projeto Vena Analytics Sim.")
AS
WITH faturamento_produto AS (
    SELECT
        loja_id,
        produto_id,
        produto_nome,
        SUM(quantidade * preco_unitario) AS faturamento
    FROM `staging.vendas`
    GROUP BY loja_id, produto_id, produto_nome
),
ranking AS (
    SELECT
        *,
        SUM(faturamento) OVER (PARTITION BY loja_id)                                   AS faturamento_total_loja,
        SUM(faturamento) OVER (
            PARTITION BY loja_id ORDER BY faturamento DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                                               AS faturamento_acumulado,
        -- Acumulado ANTES deste produto (exclusivo) — e o que decide a classe,
        -- nao o acumulado incluindo o proprio produto. Sem isso, um produto
        -- sozinho responsavel por 97% do faturamento da loja cairia em C
        -- (porque o acumulado "inclusivo" dele ja passa de 80%), quando na
        -- verdade ele E o produto A.
        SUM(faturamento) OVER (
            PARTITION BY loja_id ORDER BY faturamento DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        )                                                                               AS faturamento_acumulado_anterior
    FROM faturamento_produto
)
SELECT
    loja_id,
    produto_id,
    produto_nome,
    faturamento,
    SAFE_DIVIDE(faturamento_acumulado, faturamento_total_loja) AS pct_acumulado,
    CASE
        WHEN COALESCE(SAFE_DIVIDE(faturamento_acumulado_anterior, faturamento_total_loja), 0) < 0.80 THEN 'A'
        WHEN COALESCE(SAFE_DIVIDE(faturamento_acumulado_anterior, faturamento_total_loja), 0) < 0.95 THEN 'B'
        ELSE 'C'
    END AS classe_abc
FROM ranking;

-- Descricoes de coluna — ALTER TABLE separado pelo mesmo motivo do
-- curated_dre_gerencial.sql: CTAS nao aceita OPTIONS por coluna inline.
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN loja_id SET OPTIONS(description="ID da loja");
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN produto_id SET OPTIONS(description="ID do produto");
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN produto_nome SET OPTIONS(description="Nome do produto");
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN faturamento SET OPTIONS(description="Faturamento total do produto na loja, no periodo coletado (quantidade * preco_unitario), em R$");
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN pct_acumulado SET OPTIONS(description="Percentual acumulado do faturamento da loja, incluindo este produto, ordenado do maior pro menor faturamento");
ALTER TABLE `curated.curva_abc_produtos` ALTER COLUMN classe_abc SET OPTIONS(description="Classe ABC: A = ate 80% do faturamento acumulado, B = ate 95%, C = restante");
