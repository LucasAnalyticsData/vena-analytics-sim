"""
Ponto de entrada do Dagster. Roda com:
    dagster dev -f src/dagster_project/definitions.py

TODO (semana 2 -> 3): adicionar um sensor que escuta o topico Pub/Sub
(PUBSUB_TOPIC_NOVO_ARQUIVO do .env) e dispara o job automaticamente
quando um novo arquivo pousa em Cloud Storage — em vez de so rodar no
horario fixo do schedule abaixo. Documentado como proximo passo, nao
implementado agora (ver docs/).

Executor in_process (nao o multiprocess padrao do Dagster): no Windows, o
multiprocess usa spawn e reimporta tudo do zero em cada subprocesso — com
varios steps de I/O de rede rodando em paralelo (raw_vendas_api,
raw_fechamento_financeiro, raw_precos_concorrente), e comum um subprocesso
crashar silenciosamente ao inicializar libs nativas (grpc/google-api-core)
ao mesmo tempo. Pra um pipeline pequeno local, rodar tudo sequencial no
mesmo processo e mais confiavel que a paralelizacao vale a pena.
"""
from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    in_process_executor,
)

from src.dagster_project import assets, checks

todos_os_assets = [
    assets.raw_vendas_api,
    assets.raw_fechamento_financeiro,
    assets.raw_precos_concorrente,
    assets.staging_vendas,
    assets.staging_fechamento_financeiro,
    assets.staging_precos_concorrente,
    assets.curated_dre_gerencial,
    assets.curated_curva_abc,
]

todos_os_checks = [
    checks.check_staging_vendas_quantidade_positiva,
    checks.check_staging_vendas_chaves_nao_nulas,
    checks.check_fechamento_valor_positivo,
    checks.check_fechamento_categoria_valida,
    checks.check_dre_valores_nao_negativos,
    checks.check_precos_concorrente_positivo,
]

pipeline_completo_job = define_asset_job(
    name="pipeline_painel_multi_loja",
    selection=AssetSelection.all(),
    executor_def=in_process_executor,
)

pipeline_diario = ScheduleDefinition(
    name="pipeline_diario_6h",
    job=pipeline_completo_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Sao_Paulo",
)

defs = Definitions(
    assets=todos_os_assets,
    asset_checks=todos_os_checks,
    jobs=[pipeline_completo_job],
    schedules=[pipeline_diario],
)