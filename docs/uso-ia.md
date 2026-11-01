# Registro de uso de IA Generativa no desenvolvimento

A JD pede explicitamente "aplicar e incentivar o uso de Inteligência
Artificial no ciclo de desenvolvimento". Este arquivo é o registro real
(não genérico) de onde IA generativa acelerou este projeto — é a resposta
concreta para "como você usa IA no seu fluxo de trabalho hoje".

Formato por entrada: o que eu pedi, o que a IA entregou, e — mais
importante — o que eu tive que corrigir ou validar manualmente, porque é
essa parte que mostra que a responsabilidade pelo resultado continua sendo
minha, não da ferramenta.

## 2026-10-29 — Scaffold inicial do projeto
Ferramenta: Claude.
Pedido: estrutura de um projeto de estudo simulando o fluxo de dados da
vaga (ingestão API/CSV/scraping → GCP → orquestração → indicador), a
partir da descrição da arquitetura que eu tinha desenhado.
Entregue: repositório completo — docker-compose, API mock, schema SQL das
camadas staging/curated, esqueleto dos assets Dagster, testes.
Corrigido manualmente: nomes reais de bucket/dataset do meu projeto GCP,
credenciais, e um bug real na classificação da Curva ABC que só apareceu
rodando contra dado de teste (classificação usando o acumulado inclusivo
em vez do exclusivo — um produto sozinho responsável por 97% do
faturamento caía errado na classe C). A IA errou a lógica na primeira
tentativa; o teste automatizado que ela mesma escreveu foi o que expôs o
erro.

## 2026-10-29 — Debug de integração real com BigQuery
Pedido: ajuda pra diagnosticar uma sequência de erros reais rodando o
pipeline pela primeira vez contra GCP de verdade (não mais só localmente).
Entregue: identificação e correção de 3 bugs em sequência: dependência
`pyarrow` faltando no `requirements.txt`, incompatibilidade de tipo entre
`float64` do pandas e `NUMERIC`/decimal128 do BigQuery (exigiu conversão
pra `Decimal` antes da gravação), e dado duplicado por `WRITE_APPEND` sem
idempotência (materializar o pipeline várias vezes durante o
desenvolvimento inflou a receita em 4x antes de eu perceber comparando
contra o CSV original).
Corrigido manualmente: nada ficou "por minha conta" aqui além de colar o
erro de verdade do meu terminal a cada passo — a IA não tinha acesso ao
meu ambiente, cada diagnóstico dependeu do log real que eu colei.

## 2026-10-29 — Boas práticas de Analytics Engineering (particionamento, segurança, qualidade)
Pedido: o que um Analytics Engineer Sênior acrescentaria no projeto além
do básico funcional — performance, custo, segurança, qualidade.
Entregue: particionamento e clustering nas tabelas BigQuery, descrições de
coluna, Service Account dedicada com permissões mínimas (via
impersonation, sem chave JSON baixada), Dagster Asset Checks de qualidade
de dado, schedule automático, e política de ciclo de vida no bucket.
Corrigido manualmente: um bug real no asset check de valores nulos —
`numpy.bool_` (resultado de uma comparação com `.sum()` do pandas) não é
aceito onde o Dagster exige `bool` nativo do Python, e só quebrou ao rodar
contra o pipeline de verdade, não nos testes unitários que eu tinha
escrito antes.

---

**Padrão que se repetiu em quase todo item desta lista**: o primeiro
rascunho da IA funcionava em teoria ou contra dado sintético simples, mas
quebrava ao encostar no ambiente real (GCP, tipos de dado reais, execução
repetida). O valor não foi "a IA escreveu o código" — foi usar a IA pra
acelerar o primeiro rascunho e a investigação de cada erro, enquanto eu
validava cada correção rodando de verdade antes de aceitar. É essa
distinção que vou levar pra entrevista quando perguntarem sobre uso de IA
generativa no desenvolvimento.
