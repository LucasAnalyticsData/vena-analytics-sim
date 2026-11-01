"""
Qualidade de dado via Dagster Asset Checks.

Diferenca pra um teste pytest comum (ver tests/test_assets.py): um teste
roda no CI, contra dado sintetico controlado, pra validar que a LOGICA esta
certa. Um asset_check roda dentro do proprio pipeline, contra o DADO REAL
que acabou de ser gerado, pra validar que a EXECUCAO daquele dia nao trouxe
lixo (API fora do ar devolvendo vazio, CSV com valor negativo por erro de
digitacao, scraping trazendo preco zerado, etc). As duas coisas sao
complementares, nenhuma substitui a outra.

Rodar localmente: aparecem na aba "Checks" de cada asset na UI do Dagster
(http://localhost:3000).
"""
import pandas as pd
from dagster import AssetCheckResult, asset_check

from src.dagster_project.assets import (
    curated_dre_gerencial,
    staging_fechamento_financeiro,
    staging_precos_concorrente,
    staging_vendas,
)


@asset_check(asset=staging_vendas, description="Nenhuma linha de venda deve ter quantidade <= 0")
def check_staging_vendas_quantidade_positiva(staging_vendas: pd.DataFrame) -> AssetCheckResult:
    invalidas = staging_vendas[staging_vendas["quantidade"] <= 0]
    return AssetCheckResult(
        passed=len(invalidas) == 0,
        metadata={
            "linhas_invalidas": len(invalidas),
            "total_linhas": len(staging_vendas),
        },
    )


@asset_check(asset=staging_vendas, description="loja_id e produto_id nao podem ser nulos")
def check_staging_vendas_chaves_nao_nulas(staging_vendas: pd.DataFrame) -> AssetCheckResult:
    nulos = int(staging_vendas["loja_id"].isna().sum() + staging_vendas["produto_id"].isna().sum())
    return AssetCheckResult(
        passed=nulos == 0,
        metadata={"total_nulos": nulos},
    )


@asset_check(
    asset=staging_fechamento_financeiro,
    description="Valor de lancamento financeiro deve ser sempre positivo (sinal vem de categoria/tipo, nao do valor)",
)
def check_fechamento_valor_positivo(staging_fechamento_financeiro: pd.DataFrame) -> AssetCheckResult:
    df = staging_fechamento_financeiro
    invalidos = df[df["valor"].astype(float) <= 0]
    return AssetCheckResult(
        passed=len(invalidos) == 0,
        metadata={
            "linhas_invalidas": len(invalidos),
            "total_linhas": len(df),
        },
    )


@asset_check(
    asset=staging_fechamento_financeiro,
    description="categoria so pode ser 'receita' ou 'despesa' (protege contra erro de digitacao no CSV)",
)
def check_fechamento_categoria_valida(staging_fechamento_financeiro: pd.DataFrame) -> AssetCheckResult:
    categorias_validas = {"receita", "despesa"}
    encontradas = set(staging_fechamento_financeiro["categoria"].unique())
    invalidas = encontradas - categorias_validas
    return AssetCheckResult(
        passed=len(invalidas) == 0,
        metadata={"categorias_invalidas_encontradas": sorted(invalidas)},
    )


@asset_check(
    asset=curated_dre_gerencial,
    description="receita_total e despesa_total nunca podem ser negativos num DRE",
)
def check_dre_valores_nao_negativos(curated_dre_gerencial: pd.DataFrame) -> AssetCheckResult:
    df = curated_dre_gerencial
    invalidas = df[(df["receita_total"].astype(float) < 0) | (df["despesa_total"].astype(float) < 0)]
    return AssetCheckResult(
        passed=len(invalidas) == 0,
        metadata={"linhas_invalidas": len(invalidas)},
    )


@asset_check(
    asset=staging_precos_concorrente,
    description="preco_coletado deve ser sempre positivo",
)
def check_precos_concorrente_positivo(staging_precos_concorrente: pd.DataFrame) -> AssetCheckResult:
    df = staging_precos_concorrente
    invalidos = df[df["preco_coletado"].astype(float) <= 0]
    return AssetCheckResult(
        passed=len(invalidos) == 0,
        metadata={"linhas_invalidas": len(invalidos), "total_linhas": len(df)},
    )