"""
Semana 2 — coleta de precos de concorrentes via scraping (BeautifulSoup).

Aponta para o mock_concorrente_site.py local por padrao (porta 8001) — pra
apontar num concorrente real, so trocar BASE_URL e, se a estrutura do HTML
for diferente, ajustar os seletores CSS abaixo (tr.produto / td.nome / td.preco).
Para um site que renderiza preco via JavaScript (nao aparece no HTML cru),
a troca certa e Playwright, nao reescrever este parser.
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8001"
CONCORRENTES = ["perfumax", "belezaja"]


def _parse_preco(texto: str) -> float:
    """Converte "R$ 189.90" ou "R$ 1.234,56" (formato BR) pra float."""
    limpo = texto.replace("R$", "").strip()
    if "," in limpo and "." in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")
    return float(limpo)


def _parse_catalogo_html(html: str, concorrente: str, agora: pd.Timestamp) -> list[dict]:
    """Logica pura de parsing, separada da chamada de rede — assim da pra
    testar sem precisar do mock_concorrente_site rodando (ver tests/test_scraping.py)."""
    soup = BeautifulSoup(html, "html.parser")
    linhas = []
    for tr in soup.select("tr.produto"):
        nome = tr.select_one("td.nome").get_text(strip=True)
        preco_texto = tr.select_one("td.preco").get_text(strip=True)
        linhas.append({
            "produto_nome": nome,
            "concorrente": concorrente,
            "preco_coletado": _parse_preco(preco_texto),
            "data_coleta": agora,
            "fonte": "scraping",
        })
    return linhas


def coletar_precos_concorrente() -> pd.DataFrame:
    agora = pd.Timestamp.utcnow()
    todas_linhas = []
    for concorrente in CONCORRENTES:
        resp = requests.get(f"{BASE_URL}/{concorrente}/catalogo", timeout=10)
        resp.raise_for_status()
        todas_linhas.extend(_parse_catalogo_html(resp.text, concorrente, agora))
    return pd.DataFrame(todas_linhas)