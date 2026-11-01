"""
Testa a logica pura de validacao da Cloud Function (sem GCP real).
A parte que le/escreve no bucket so e validada rodando de verdade no GCP.
"""
from src.functions.validar_arquivo_raw.main import _validar_conteudo


def test_csv_fechamento_com_colunas_corretas_e_valido():
    conteudo = (
        "loja_id,competencia,categoria,tipo,descricao,valor\n"
        "1,2026-09,receita,credito,Vendas balcao,1000.00\n"
    )
    valido, motivo = _validar_conteudo("raw/fechamento_financeiro/2026-10-30/arquivo.csv", conteudo)
    assert valido is True


def test_csv_fechamento_com_coluna_faltando_e_invalido():
    conteudo = (
        "loja_id,competencia,categoria,descricao,valor\n"  # falta 'tipo'
        "1,2026-09,receita,Vendas balcao,1000.00\n"
    )
    valido, motivo = _validar_conteudo("raw/fechamento_financeiro/2026-10-30/arquivo.csv", conteudo)
    assert valido is False
    assert "tipo" in motivo


def test_csv_fechamento_vazio_e_invalido():
    valido, motivo = _validar_conteudo("raw/fechamento_financeiro/2026-10-30/arquivo.csv", "")
    assert valido is False
    assert "vazio" in motivo


def test_csv_fechamento_so_com_cabecalho_e_invalido():
    conteudo = "loja_id,competencia,categoria,tipo,descricao,valor\n"
    valido, motivo = _validar_conteudo("raw/fechamento_financeiro/2026-10-30/arquivo.csv", conteudo)
    assert valido is False
    assert "cabecalho" in motivo


def test_arquivo_fora_da_regra_especifica_passa_sem_validacao():
    valido, motivo = _validar_conteudo("raw/vendas/2026-10-30/qualquer.json", "{}")
    assert valido is True
