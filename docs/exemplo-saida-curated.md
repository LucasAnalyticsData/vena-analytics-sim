# Exemplo de sa\u00edda \u2014 camada curated

> Amostra ilustrativa, extra\u00edda do `curated.dre_gerencial` e `curated.curva_abc_produtos`
> reais do projeto em 01/11/2026. N\u00e3o \u00e9 dado de exemplo inventado \u2014 \u00e9 o resultado real
> do pipeline rodando contra os dados sint\u00e9ticos deste projeto. Objetivo: dar uma ideia
> de como o dado fica sem precisar rodar o pipeline ou abrir o BigQuery.

## `curated.dre_gerencial`

| loja_id | competencia | receita_total | despesa_total | resultado_liquido | margem_liquida_pct |
|---|---|---|---|---|---|
| 1 | 2026-08 | 55.900,00 | 47.590,40 | 8.309,60 | 14,87% |
| 1 | 2026-09 | 60.350,30 | 49.450,95 | 10.899,35 | 18,06% |
| 2 | 2026-08 | 45.150,00 | 38.980,00 | 6.170,00 | 13,67% |
| 5 | 2026-09 | 67.950,00 | 55.440,60 | 12.509,40 | 18,41% |

*(tabela completa tem 10 linhas \u2014 5 lojas \u00d7 2 compet\u00eancias)*

## `curated.curva_abc_produtos` (top 5 por faturamento)

| loja_id | produto_nome | faturamento | classe_abc |
|---|---|---|---|
| 2 | Perfume Amadeirado Noite 100ml | 39.380,30 | A |
| 3 | Perfume Amadeirado Noite 100ml | 37.781,10 | A |
| 3 | Perfume Gourmand Baunilha 75ml | 37.736,40 | A |
| 5 | Perfume Amadeirado Noite 100ml | 36.181,90 | A |
| 4 | Perfume Amadeirado Noite 100ml | 35.782,10 | A |