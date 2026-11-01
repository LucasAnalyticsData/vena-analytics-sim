"""
Semana 1 — Ingestão de arquivo (CSV) para Cloud Storage (camada raw).

Fonte de dado: arquivo de fechamento financeiro mensal (simulando
a entrega que uma loja/franqueado manda no fim do mês).

Uso:
    python -m src.ingestion.load_csv_to_gcs --file data/sample/fechamento_mensal_loja_01.csv

Pré-requisito: GCP_PROJECT_ID e GCS_BUCKET_RAW no .env, e
`gcloud auth application-default login` já rodado localmente.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()


def upload_raw_file(local_path: str) -> str:
    """Sobe o arquivo bruto para Cloud Storage, particionado por data de ingestão.

    Padrão de nomenclatura: raw/<fonte>/<data_ingestao>/<arquivo_original>
    Isso preserva o dado exatamente como chegou — tratamento/validação
    acontece na etapa seguinte (Cloud Function ou asset Dagster de staging),
    nunca na ingestão.
    """
    bucket_name = os.environ["GCS_BUCKET_RAW"]
    client = storage.Client(project=os.environ["GCP_PROJECT_ID"])
    bucket = client.bucket(bucket_name)

    nome_arquivo = Path(local_path).name
    data_ingestao = datetime.utcnow().strftime("%Y-%m-%d")
    blob_path = f"raw/fechamento_financeiro/{data_ingestao}/{nome_arquivo}"

    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)

    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    print(f"Arquivo enviado: {gcs_uri}")
    return gcs_uri


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Caminho do CSV local")
    args = parser.parse_args()
    upload_raw_file(args.file)
