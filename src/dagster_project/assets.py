"""
Semana 2 — Orquestracao com Dagster.

Modelo de "Software-Defined Assets": cada funcao abaixo declara o DADO que
produz (nao so o passo que executa). O Dagster calcula a ordem de execucao
a partir das dependencias entre os parametros (raw_vendas -> staging_vendas
-> curva_abc, por exemplo) — isso E o DAG, so que descrito em Python em vez
de desenhado manualmente.

Rodar localmente (interface web do Dagster):
    dagster dev -f src/dagster_project/definitions.py

Os TODOs marcam exatamente onde cada peca da JD entra:
    - Cloud Storage  -> leitura/escrita de raw
    - BigQuery       -> staging e curated
    - Pub/Sub        -> gatilho entre ingestao e processamento (ver definitions.py)
"""
import decimal
import os

import pandas as pd
from dagster import asset, AssetExecutionContext
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()


def _write_staging_table(df: pd.DataFrame, table_name: str) -> None:
    """Escreve um DataFrame numa tabela ja existente em staging (WRITE_TRUNCATE).

    Usa o schema ja definido pela DDL (src/sql/schema_staging.sql) em vez de
    deixar o BigQuery inferir — autodetect pode divergir do tipo real da
    coluna (ex: DATE virando STRING), o que so aparece como erro mais tarde,
    na camada curated.

    WRITE_TRUNCATE (nao WRITE_APPEND): a fonte (API mock / CSV / scraping)
    devolve o estado completo a cada chamada, nao um incremento. Com
    WRITE_APPEND, materializar o Dagster varias vezes (normal durante
    desenvolvimento) empilha os mesmos dados repetidas vezes na tabela,
    inflando qualquer SUM() nas camadas seguintes sem nenhum erro aparente —
    foi exatamente isso que gerou receita 4x maior que o real no DRE.
    TRUNCATE garante que a tabela sempre reflete so a ultima execucao,
    idempotente por materialize.
    """
    project_id = os.environ["GCP_PROJECT_ID"]
    dataset = os.environ["BQ_DATASET_STAGING"]
    table_id = f"{project_id}.{dataset}.{table_name}"

    client = bigquery.Client(project=project_id)
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # espera terminar e levanta excecao se falhar


@asset(group_name="raw")
def raw_vendas_api(context: AssetExecutionContext) -> pd.DataFrame:
    """Le vendas da API mock e pousa em Cloud Storage (raw).

    Busca a lista de lojas primeiro (/lojas) e depois itera uma chamada por
    loja — assim a ingestao nao fica hardcoded numa loja so e generaliza pra
    qualquer numero de lojas cadastradas na API mock, sem precisar mexer
    neste codigo quando uma loja nova for adicionada.

    base_url vem de MOCK_API_URL (.env) — aponta pro servico real no Cloud
    Run (https://mock-api-xxx.run.app) em vez de localhost fixo. Sem a
    variavel definida, cai no default localhost:8000 (pra nao quebrar quem
    ainda nao fez o deploy do Cloud Run).

    TODO (semana 1 -> 2): trocar chamada direta por leitura do blob que
    o Pub/Sub avisou ter chegado, em vez de buscar na API toda execucao.
    """
    import requests

    base_url = os.environ.get("MOCK_API_URL", "http://localhost:8000")
    context.log.info(f"Consultando API mock em {base_url}")

    lojas = requests.get(f"{base_url}/lojas").json()
    context.log.info(f"{len(lojas)} loja(s) encontrada(s) na API mock")

    todas_vendas = []
    for loja in lojas:
        resp = requests.get(
            f"{base_url}/vendas/ultimos-dias",
            params={"loja_id": loja["loja_id"], "dias": 7},
        )
        resp.raise_for_status()
        todas_vendas.extend(resp.json()["vendas"])

    df = pd.DataFrame(todas_vendas)
    context.log.info(f"{len(df)} linhas de venda coletadas da API mock, {len(lojas)} loja(s)")
    return df


@asset(group_name="raw")
def raw_fechamento_financeiro(context: AssetExecutionContext) -> pd.DataFrame:
    """Le o CSV de fechamento mensal (ja deveria estar em Cloud Storage
    apos src/ingestion/load_csv_to_gcs.py rodar)."""
    df = pd.read_csv("data/sample/fechamento_mensal_loja_01.csv")
    context.log.info(f"{len(df)} linhas de fechamento financeiro carregadas")
    return df


@asset(group_name="raw")
def raw_precos_concorrente(context: AssetExecutionContext) -> pd.DataFrame:
    """Scraping dos precos de concorrentes (mock local, porta 8001).

    Reaproveita a tecnica do projeto pessoal de monitoramento de precos:
    requests + BeautifulSoup, sem headless browser, porque o alvo e um
    catalogo HTML simples (sem JS). Pra um site real que renderiza preco via
    JS, a troca seria por Playwright, nao por reescrever o parser.
    """
    from src.scraping.scrape_precos_concorrente import coletar_precos_concorrente

    df = coletar_precos_concorrente()
    context.log.info(f"{len(df)} preco(s) de concorrente coletado(s) via scraping")
    return df


@asset(group_name="staging")
def staging_vendas(context: AssetExecutionContext, raw_vendas_api: pd.DataFrame) -> pd.DataFrame:
    """Padroniza o schema de vendas e grava em `staging.vendas` no BigQuery.

    A API mock devolve a coluna `data`; a tabela staging espera `data_venda`
    (nome mais claro pra quem for consultar depois) — por isso o rename
    explicito, em vez de deixar a carga falhar por coluna inexistente.
    """
    df = raw_vendas_api.copy()
    df = df.rename(columns={"data": "data_venda"})
    df["data_venda"] = pd.to_datetime(df["data_venda"]).dt.date
    df["fonte"] = "api_mock"
    df["data_ingestao"] = pd.Timestamp.utcnow()

    df["preco_unitario"] = df["preco_unitario"].apply(lambda x: decimal.Decimal(str(x)))

    _write_staging_table(df, "vendas")
    context.log.info(f"{len(df)} linhas gravadas em staging.vendas")
    return df


@asset(group_name="staging")
def staging_fechamento_financeiro(
    context: AssetExecutionContext, raw_fechamento_financeiro: pd.DataFrame
) -> pd.DataFrame:
    """Padroniza o schema de fechamento financeiro e grava em
    `staging.fechamento_financeiro` no BigQuery."""
    df = raw_fechamento_financeiro.copy()
    df["fonte"] = "csv_fechamento_mensal"
    df["data_ingestao"] = pd.Timestamp.utcnow()

    df["valor"] = df["valor"].apply(lambda x: decimal.Decimal(str(x)))

    _write_staging_table(df, "fechamento_financeiro")
    context.log.info(f"{len(df)} linhas gravadas em staging.fechamento_financeiro")
    return df


@asset(group_name="staging")
def staging_precos_concorrente(
    context: AssetExecutionContext, raw_precos_concorrente: pd.DataFrame
) -> pd.DataFrame:
    """Padroniza e grava em `staging.precos_concorrente` no BigQuery."""
    df = raw_precos_concorrente.copy()
    df["preco_coletado"] = df["preco_coletado"].apply(lambda x: decimal.Decimal(str(x)))
    _write_staging_table(df, "precos_concorrente")
    context.log.info(f"{len(df)} linhas gravadas em staging.precos_concorrente")
    return df


@asset(group_name="curated")
def curated_dre_gerencial(
    context: AssetExecutionContext, staging_fechamento_financeiro: pd.DataFrame
) -> pd.DataFrame:
    """Equivalente em pandas ao src/sql/curated_dre_gerencial.sql — util pra
    testar a regra de negocio localmente antes de rodar como query no BigQuery."""
    df = staging_fechamento_financeiro
    resultado = (
        df.groupby(["loja_id", "competencia"])
        .apply(
            lambda g: pd.Series(
                {
                    "receita_total": g.loc[g["categoria"] == "receita", "valor"].sum(),
                    "despesa_total": g.loc[g["categoria"] == "despesa", "valor"].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    resultado["resultado_liquido"] = resultado["receita_total"] - resultado["despesa_total"]
    resultado["margem_liquida_pct"] = resultado["resultado_liquido"] / resultado["receita_total"]
    context.log.info(f"DRE gerencial calculado para {len(resultado)} loja(s)/competencia(s)")
    return resultado


@asset(group_name="curated")
def curated_curva_abc(context: AssetExecutionContext, staging_vendas: pd.DataFrame) -> pd.DataFrame:
    """Equivalente em pandas ao src/sql/curated_curva_abc.sql."""
    df = staging_vendas.copy()
    df["preco_unitario"] = df["preco_unitario"].astype(float)
    df["faturamento"] = df["quantidade"] * df["preco_unitario"]

    faturamento_produto = (
        df.groupby(["loja_id", "produto_id", "produto_nome"])["faturamento"].sum().reset_index()
    )
    faturamento_produto = faturamento_produto.sort_values(
        ["loja_id", "faturamento"], ascending=[True, False]
    )
    faturamento_produto["faturamento_acumulado"] = faturamento_produto.groupby("loja_id")[
        "faturamento"
    ].cumsum()
    faturamento_produto["faturamento_total_loja"] = faturamento_produto.groupby("loja_id")[
        "faturamento"
    ].transform("sum")
    faturamento_produto["pct_acumulado"] = (
        faturamento_produto["faturamento_acumulado"] / faturamento_produto["faturamento_total_loja"]
    )
    faturamento_produto["pct_acumulado_anterior"] = (
        faturamento_produto["pct_acumulado"]
        - faturamento_produto["faturamento"] / faturamento_produto["faturamento_total_loja"]
    )

    def classificar(pct_anterior: float) -> str:
        if pct_anterior < 0.80:
            return "A"
        if pct_anterior < 0.95:
            return "B"
        return "C"

    faturamento_produto["classe_abc"] = faturamento_produto["pct_acumulado_anterior"].apply(classificar)
    context.log.info(f"Curva ABC calculada para {len(faturamento_produto)} produto(s)/loja(s)")
    return faturamento_produto