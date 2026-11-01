"""
Semana 2 — site falso de concorrente, pra treinar scraping sem depender de
rede externa (sem risco de ToS, instabilidade ou IP block durante a demo).
Simula uma pagina de catalogo HTML que um concorrente real exporia.

Rodar localmente:
    uvicorn src.scraping.mock_concorrente_site:app --reload --port 8001
"""
import random

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Mock Concorrente")

PRODUTOS_BASE = [
    ("Perfume Floral 100ml", 189.90),
    ("Perfume Amadeirado 100ml", 219.90),
    ("Hidratante Corporal 400ml", 59.90),
    ("Sabonete Liquido Refil", 24.90),
    ("Desodorante Colonia", 44.90),
    ("Shampoo Nutritivo 300ml", 39.90),
    ("Condicionador Reparador", 42.90),
    ("Creme para Maos", 19.90),
    ("Oleo Corporal Seco", 54.90),
    ("Kit Presente Banho", 89.90),
]

# Fator de preco por concorrente — BelezaJa roda ~7% mais barato, de proposito
CONCORRENTES = {"perfumax": 1.00, "belezaja": 0.93}


@app.get("/{concorrente}/catalogo", response_class=HTMLResponse)
def catalogo(concorrente: str) -> str:
    fator = CONCORRENTES.get(concorrente.lower())
    if fator is None:
        return "<html><body><p>Concorrente nao encontrado</p></body></html>"

    random.seed(concorrente)  # precos estaveis entre chamadas, nao muda a cada scrape
    linhas = ""
    for nome, preco_base in PRODUTOS_BASE:
        preco = round(preco_base * fator * random.uniform(0.95, 1.05), 2)
        linhas += f'<tr class="produto"><td class="nome">{nome}</td><td class="preco">R$ {preco:.2f}</td></tr>\n'

    return f"""
    <html>
      <body>
        <h1>Catalogo - {concorrente.title()}</h1>
        <table id="catalogo">
          <thead><tr><th>Produto</th><th>Preco</th></tr></thead>
          <tbody>
            {linhas}
          </tbody>
        </table>
      </body>
    </html>
    """