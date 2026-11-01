"""
Mock de um "ERP de loja" expondo vendas diárias via API.
Simula a fonte "API" pedida na JD (Analytics Engineer Sênior).

Rodar localmente:
    uvicorn src.mock_api.main:app --reload --port 8000

Dado gerado sinteticamente a cada request — nenhuma relação com
faturamento real de qualquer empresa.

Semana 3: este serviço é o candidato natural para subir como
Cloud Run (é um container HTTP completo, não um evento único —
por isso NÃO é Cloud Function, ver anotação no README técnico).
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from fastapi import FastAPI, Query

app = FastAPI(title="Mock ERP de Loja - Projeto de Estudo")

LOJAS = [
    {"loja_id": 1, "nome": "Loja Centro", "rede": "franquia_a"},
    {"loja_id": 2, "nome": "Loja Setor Bueno", "rede": "franquia_a"},
    {"loja_id": 3, "nome": "Loja Aparecida", "rede": "franquia_b"},
    {"loja_id": 4, "nome": "Loja Campinas", "rede": "franquia_b"},
    {"loja_id": 5, "nome": "Loja Jardim Goiás", "rede": "franquia_a"},
]

# Catalogo fictício de perfumaria/cosmeticos. Nomes genericos e inventados —
# nao sao marcas reais. "popularidade" controla a chance de vender no dia e a
# faixa de quantidade (ver _gerar_vendas_do_dia): sem essa variacao, todo
# produto venderia parecido e a Curva ABC nao teria o que classificar — ela
# existe justamente pra separar os poucos itens que concentram faturamento
# dos muitos que vendem pouco.
PRODUTOS = [
    # --- alta popularidade (tendem a classe A) ---
    {"produto_id": 1, "nome": "Perfume Floral Intenso 100ml", "categoria": "perfumaria_feminina", "preco": 189.90, "popularidade": "alta"},
    {"produto_id": 2, "nome": "Perfume Amadeirado Noite 100ml", "categoria": "perfumaria_masculina", "preco": 199.90, "popularidade": "alta"},
    {"produto_id": 3, "nome": "Body Splash Frutas Vermelhas 200ml", "categoria": "perfumaria_feminina", "preco": 59.90, "popularidade": "alta"},
    {"produto_id": 4, "nome": "Perfume Gourmand Baunilha 75ml", "categoria": "perfumaria_feminina", "preco": 159.90, "popularidade": "alta"},
    {"produto_id": 5, "nome": "Hidratante Corporal Lavanda 400ml", "categoria": "cuidados_pele", "preco": 44.90, "popularidade": "alta"},
    {"produto_id": 6, "nome": "Protetor Solar Facial FPS50 50ml", "categoria": "cuidados_pele", "preco": 79.90, "popularidade": "alta"},
    {"produto_id": 7, "nome": "Shampoo Reparador 300ml", "categoria": "cuidados_cabelo", "preco": 39.90, "popularidade": "alta"},
    {"produto_id": 8, "nome": "Condicionador Hidratação 300ml", "categoria": "cuidados_cabelo", "preco": 39.90, "popularidade": "alta"},
    {"produto_id": 9, "nome": "Base Líquida Natural 30ml", "categoria": "maquiagem", "preco": 89.90, "popularidade": "alta"},
    {"produto_id": 10, "nome": "Batom Matte Vermelho", "categoria": "maquiagem", "preco": 49.90, "popularidade": "alta"},
    {"produto_id": 11, "nome": "Máscara de Cílios Volume", "categoria": "maquiagem", "preco": 59.90, "popularidade": "alta"},
    {"produto_id": 12, "nome": "Desodorante Aerosol Musk 150ml", "categoria": "higiene_pessoal", "preco": 24.90, "popularidade": "alta"},
    # --- media popularidade (tendem a classe B) ---
    {"produto_id": 13, "nome": "Colônia Cítrica Fresh 50ml", "categoria": "perfumaria_masculina", "preco": 69.90, "popularidade": "media"},
    {"produto_id": 14, "nome": "Desodorante Colônia Oceano 100ml", "categoria": "perfumaria_masculina", "preco": 79.90, "popularidade": "media"},
    {"produto_id": 15, "nome": "Perfume Floral Doce 50ml", "categoria": "perfumaria_feminina", "preco": 99.90, "popularidade": "media"},
    {"produto_id": 16, "nome": "Body Splash Coco 200ml", "categoria": "perfumaria_feminina", "preco": 54.90, "popularidade": "media"},
    {"produto_id": 17, "nome": "Hidratante Facial Hialurônico 50ml", "categoria": "cuidados_pele", "preco": 89.90, "popularidade": "media"},
    {"produto_id": 18, "nome": "Sabonete Líquido Aveia 250ml", "categoria": "cuidados_pele", "preco": 29.90, "popularidade": "media"},
    {"produto_id": 19, "nome": "Óleo Capilar Finalizador 60ml", "categoria": "cuidados_cabelo", "preco": 49.90, "popularidade": "media"},
    {"produto_id": 20, "nome": "Máscara Capilar Nutritiva 250g", "categoria": "cuidados_cabelo", "preco": 54.90, "popularidade": "media"},
    {"produto_id": 21, "nome": "Pó Compacto Translúcido", "categoria": "maquiagem", "preco": 54.90, "popularidade": "media"},
    {"produto_id": 22, "nome": "Delineador Líquido Preto", "categoria": "maquiagem", "preco": 34.90, "popularidade": "media"},
    {"produto_id": 23, "nome": "Desodorante Roll-on Sem Perfume 50ml", "categoria": "higiene_pessoal", "preco": 19.90, "popularidade": "media"},
    # --- baixa popularidade (tendem a classe C) ---
    {"produto_id": 24, "nome": "Água de Perfume Especiarias 100ml", "categoria": "perfumaria_masculina", "preco": 219.90, "popularidade": "baixa"},
    {"produto_id": 25, "nome": "Colônia Infantil Suave 100ml", "categoria": "perfumaria_infantil", "preco": 39.90, "popularidade": "baixa"},
    {"produto_id": 26, "nome": "Óleo Corporal Seco 100ml", "categoria": "cuidados_pele", "preco": 69.90, "popularidade": "baixa"},
    {"produto_id": 27, "nome": "Máscara Facial Argila 100g", "categoria": "cuidados_pele", "preco": 34.90, "popularidade": "baixa"},
    {"produto_id": 28, "nome": "Leave-in Anticrespo 150ml", "categoria": "cuidados_cabelo", "preco": 44.90, "popularidade": "baixa"},
    {"produto_id": 29, "nome": "Paleta de Sombras Nude", "categoria": "maquiagem", "preco": 99.90, "popularidade": "baixa"},
    {"produto_id": 30, "nome": "Loção Pós-Barba Menthol 100ml", "categoria": "higiene_pessoal", "preco": 34.90, "popularidade": "baixa"},
]

# (chance de vender no dia, faixa de quantidade) por faixa de popularidade.
_REGRAS_POPULARIDADE = {
    "alta": {"chance_venda": 0.90, "qtd_min": 15, "qtd_max": 40},
    "media": {"chance_venda": 0.55, "qtd_min": 5, "qtd_max": 18},
    "baixa": {"chance_venda": 0.25, "qtd_min": 1, "qtd_max": 6},
}


def _gerar_vendas_do_dia(loja_id: int, dia: date) -> list[dict]:
    """Gera vendas sintéticas e determinísticas o suficiente para parecer real,
    mas sem qualquer relação com dado de negócio verdadeiro."""
    random.seed(f"{loja_id}-{dia.isoformat()}")
    vendas = []
    for produto in PRODUTOS:
        regra = _REGRAS_POPULARIDADE[produto["popularidade"]]
        if random.random() < regra["chance_venda"]:
            qtd = random.randint(regra["qtd_min"], regra["qtd_max"])
            vendas.append(
                {
                    "loja_id": loja_id,
                    "produto_id": produto["produto_id"],
                    "produto_nome": produto["nome"],
                    "categoria": produto["categoria"],
                    "quantidade": qtd,
                    "preco_unitario": produto["preco"],
                    "data": dia.isoformat(),
                }
            )
    return vendas


@app.get("/lojas")
def listar_lojas():
    return LOJAS


@app.get("/vendas")
def vendas_do_dia(
    loja_id: int = Query(..., description="ID da loja"),
    dia: str | None = Query(None, description="YYYY-MM-DD, default = hoje"),
):
    """Simula o endpoint que um ERP real exporia para consulta de vendas diárias.
    Fonte de ingestão 'API' do fluxo de dados do projeto."""
    data_consulta = date.fromisoformat(dia) if dia else date.today()
    return {
        "loja_id": loja_id,
        "data": data_consulta.isoformat(),
        "vendas": _gerar_vendas_do_dia(loja_id, data_consulta),
    }


@app.get("/vendas/ultimos-dias")
def vendas_ultimos_dias(loja_id: int, dias: int = 7):
    """Facilita testar a ingestão em lote (carga inicial do pipeline)."""
    hoje = date.today()
    resultado = []
    for i in range(dias):
        dia = hoje - timedelta(days=i)
        resultado.extend(_gerar_vendas_do_dia(loja_id, dia))
    return {"loja_id": loja_id, "periodo_dias": dias, "vendas": resultado}
