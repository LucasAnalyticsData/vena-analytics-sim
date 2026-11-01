"""
Cloud Function (Gen2) — valida e move o arquivo que acabou de pousar em
Cloud Storage. Fecha o item "Cloud Function validando/movendo arquivo
pousado" do roteiro da Semana 1.

Por que Cloud Function e nao Cloud Run aqui (ver README tecnico do
projeto): e uma reacao pontual a UM evento (arquivo novo no bucket), sem
rota HTTP, sem logica de negocio complexa — exatamente o caso de uso que
Cloud Function resolve melhor que um servico completo.

Gatilho: Eventarc, evento `google.cloud.storage.object.v1.finalized` no
bucket raw (configurado no deploy, ver infra/deploy_cloud_function.sh).

Fluxo:
    arquivo novo em raw/<qualquer_coisa>
        -> valida estrutura basica
        -> copia para validado/<mesmo caminho> ou rejeitado/<mesmo caminho>
        -> loga o resultado (Cloud Logging, via print — Gen2 captura stdout)

A logica de validacao pura (_validar_conteudo) nao depende de GCP e e
testada localmente em tests/test_validar_arquivo_raw.py — a parte que SO
roda em produção é a leitura/escrita real no bucket.
"""
from __future__ import annotations

import functions_framework
from google.cloud import storage

PREFIXOS_JA_PROCESSADOS = ("validado/", "rejeitado/")

COLUNAS_ESPERADAS_POR_TIPO = {
    "fechamento_financeiro": {"loja_id", "competencia", "categoria", "tipo", "descricao", "valor"},
}


def _validar_conteudo(nome_arquivo: str, conteudo: str) -> tuple[bool, str]:
    """Validacao pura, sem GCP — testavel localmente.

    Regra atual: se o arquivo for um CSV de fechamento financeiro
    (identificado pelo caminho), confere se a primeira linha (cabecalho)
    tem todas as colunas esperadas. Qualquer outro tipo de arquivo passa
    sem validacao especifica (regra a expandir conforme novas fontes
    entrarem no pipeline).
    """
    if not nome_arquivo.endswith(".csv"):
        return True, "tipo de arquivo sem regra de validacao especifica, aceito por padrao"

    if "fechamento_financeiro" not in nome_arquivo:
        return True, "CSV sem regra de validacao especifica pra este caminho, aceito por padrao"

    linhas = conteudo.splitlines()
    if not linhas:
        return False, "arquivo vazio"

    colunas_encontradas = set(linhas[0].split(","))
    colunas_esperadas = COLUNAS_ESPERADAS_POR_TIPO["fechamento_financeiro"]
    faltando = colunas_esperadas - colunas_encontradas
    if faltando:
        return False, f"colunas obrigatorias faltando no cabecalho: {sorted(faltando)}"

    if len(linhas) < 2:
        return False, "arquivo so tem cabecalho, nenhuma linha de dado"

    return True, "estrutura valida"


@functions_framework.cloud_event
def validar_arquivo_raw(cloud_event):
    """Entry point real, chamado pelo Eventarc quando um objeto e finalizado no bucket."""
    data = cloud_event.data
    bucket_name = data["bucket"]
    nome_arquivo = data["name"]

    if nome_arquivo.startswith(PREFIXOS_JA_PROCESSADOS):
        # Evita loop infinito: a propria copia pro destino tambem dispara
        # este evento. Sem este check, validado/x.csv geraria outro evento
        # que tentaria copiar validado/x.csv pra validado/validado/x.csv.
        print(f"Ignorando {nome_arquivo}: ja esta num prefixo processado.")
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(nome_arquivo)

    conteudo = blob.download_as_text()
    valido, motivo = _validar_conteudo(nome_arquivo, conteudo)

    prefixo_destino = "validado" if valido else "rejeitado"
    destino = f"{prefixo_destino}/{nome_arquivo}"
    bucket.copy_blob(blob, bucket, destino)

    status = "VALIDO" if valido else "REJEITADO"
    print(f"[{status}] {nome_arquivo} -> {destino} | motivo: {motivo}")
