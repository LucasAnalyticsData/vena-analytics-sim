"""
Teste basico da regra de negocio (curva ABC e DRE), rodando sobre
dado sintetico controlado — sem precisar de GCP real pra validar a logica.
Isso e o que o CI (semana 3) executa a cada push.

Usa `build_asset_context()` do proprio Dagster (nao um mock caseiro) —
e a forma correta de invocar um asset diretamente em teste unitario,
sem subir o pipeline inteiro. Vale citar isso na entrevista: mostra que
voce sabe testar um pipeline Dagster, nao so escrever um.
"""
import pandas as pd
from dagster import build_asset_context

from src.dagster_project import assets


def test_curva_abc_classifica_top_produto_como_a():
    staging_vendas = pd.DataFrame(
        [
            {"loja_id": 1, "produto_id": 1, "produto_nome": "A", "quantidade": 100, "preco_unitario": 10.0},
            {"loja_id": 1, "produto_id": 2, "produto_nome": "B", "quantidade": 5, "preco_unitario": 5.0},
            {"loja_id": 1, "produto_id": 3, "produto_nome": "C", "quantidade": 1, "preco_unitario": 2.0},
        ]
    )
    resultado = assets.curated_curva_abc(build_asset_context(), staging_vendas)

    produto_top = resultado.sort_values("faturamento", ascending=False).iloc[0]
    assert produto_top["classe_abc"] == "A"


def test_dre_gerencial_resultado_liquido_correto():
    staging_fechamento = pd.DataFrame(
        [
            {"loja_id": 1, "competencia": "2026-09", "categoria": "receita", "valor": 1000.0},
            {"loja_id": 1, "competencia": "2026-09", "categoria": "despesa", "valor": 600.0},
        ]
    )
    resultado = assets.curated_dre_gerencial(build_asset_context(), staging_fechamento)

    linha = resultado.iloc[0]
    assert linha["resultado_liquido"] == 400.0
    assert round(linha["margem_liquida_pct"], 2) == 0.4
