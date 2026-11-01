import pandas as pd

from src.scraping.scrape_precos_concorrente import _parse_catalogo_html, _parse_preco

HTML_EXEMPLO = """
<table>
  <tr class="produto"><td class="nome">Perfume Floral 100ml</td><td class="preco">R$ 189.90</td></tr>
  <tr class="produto"><td class="nome">Sabonete Liquido Refil</td><td class="preco">R$ 24.90</td></tr>
</table>
"""


def test_parse_catalogo_html_extrai_produtos():
    linhas = _parse_catalogo_html(HTML_EXEMPLO, "perfumax", pd.Timestamp("2026-08-01"))
    assert len(linhas) == 2
    assert linhas[0]["produto_nome"] == "Perfume Floral 100ml"
    assert linhas[0]["concorrente"] == "perfumax"
    assert linhas[0]["preco_coletado"] == 189.90


def test_parse_preco_formato_br():
    assert _parse_preco("R$ 1.234,56") == 1234.56
    assert _parse_preco("R$ 24,90") == 24.90
    assert _parse_preco("R$ 24.90") == 24.90