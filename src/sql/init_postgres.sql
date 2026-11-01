-- Simula a tabela transacional de um ERP de loja (fonte "banco transacional" da JD).
-- Dado 100% sintético, gerado para fins de estudo.

CREATE TABLE IF NOT EXISTS lojas (
    loja_id     SERIAL PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    cidade      VARCHAR(100) NOT NULL,
    rede        VARCHAR(50)  NOT NULL  -- ex: 'franquia_a', 'franquia_b' (fictício)
);

CREATE TABLE IF NOT EXISTS produtos (
    produto_id      SERIAL PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL,
    categoria       VARCHAR(80)  NOT NULL,
    custo_unitario  NUMERIC(10,2) NOT NULL,
    preco_unitario  NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS transacoes (
    transacao_id    SERIAL PRIMARY KEY,
    loja_id         INT REFERENCES lojas(loja_id),
    produto_id      INT REFERENCES produtos(produto_id),
    quantidade      INT NOT NULL,
    data_transacao  DATE NOT NULL,
    tipo            VARCHAR(20) NOT NULL  -- 'venda' ou 'devolucao'
);

-- Seed sintético — mesmas 5 lojas e catalogo de perfumaria/cosmeticos
-- (fictício) usado em src/mock_api/main.py, pra manter a historia do
-- projeto consistente entre as duas fontes "banco transacional" e "API".
INSERT INTO lojas (nome, cidade, rede) VALUES
    ('Loja Centro',       'Goiânia', 'franquia_a'),
    ('Loja Setor Bueno',  'Goiânia', 'franquia_a'),
    ('Loja Aparecida',    'Aparecida de Goiânia', 'franquia_b'),
    ('Loja Campinas',     'Goiânia', 'franquia_b'),
    ('Loja Jardim Goiás', 'Goiânia', 'franquia_a')
ON CONFLICT DO NOTHING;

INSERT INTO produtos (nome, categoria, custo_unitario, preco_unitario) VALUES
    ('Perfume Floral Intenso 100ml',        'perfumaria_feminina',   95.00, 189.90),
    ('Perfume Amadeirado Noite 100ml',      'perfumaria_masculina', 100.00, 199.90),
    ('Body Splash Frutas Vermelhas 200ml',  'perfumaria_feminina',   28.00,  59.90),
    ('Perfume Gourmand Baunilha 75ml',      'perfumaria_feminina',   78.00, 159.90),
    ('Hidratante Corporal Lavanda 400ml',   'cuidados_pele',         20.00,  44.90),
    ('Protetor Solar Facial FPS50 50ml',    'cuidados_pele',         36.00,  79.90),
    ('Shampoo Reparador 300ml',             'cuidados_cabelo',       18.00,  39.90),
    ('Condicionador Hidratação 300ml',      'cuidados_cabelo',       18.00,  39.90),
    ('Base Líquida Natural 30ml',           'maquiagem',             40.00,  89.90),
    ('Batom Matte Vermelho',                'maquiagem',             20.00,  49.90),
    ('Máscara de Cílios Volume',            'maquiagem',             25.00,  59.90),
    ('Desodorante Aerosol Musk 150ml',      'higiene_pessoal',       11.00,  24.90),
    ('Colônia Cítrica Fresh 50ml',          'perfumaria_masculina',  32.00,  69.90),
    ('Desodorante Colônia Oceano 100ml',    'perfumaria_masculina',  36.00,  79.90),
    ('Perfume Floral Doce 50ml',            'perfumaria_feminina',   46.00,  99.90),
    ('Body Splash Coco 200ml',              'perfumaria_feminina',   25.00,  54.90),
    ('Hidratante Facial Hialurônico 50ml',  'cuidados_pele',         41.00,  89.90),
    ('Sabonete Líquido Aveia 250ml',        'cuidados_pele',         13.00,  29.90),
    ('Óleo Capilar Finalizador 60ml',       'cuidados_cabelo',       22.00,  49.90),
    ('Máscara Capilar Nutritiva 250g',      'cuidados_cabelo',       25.00,  54.90),
    ('Pó Compacto Translúcido',             'maquiagem',             25.00,  54.90),
    ('Delineador Líquido Preto',            'maquiagem',             15.00,  34.90),
    ('Desodorante Roll-on Sem Perfume 50ml','higiene_pessoal',        9.00,  19.90),
    ('Água de Perfume Especiarias 100ml',   'perfumaria_masculina', 105.00, 219.90),
    ('Colônia Infantil Suave 100ml',        'perfumaria_infantil',   18.00,  39.90),
    ('Óleo Corporal Seco 100ml',            'cuidados_pele',         32.00,  69.90),
    ('Máscara Facial Argila 100g',          'cuidados_pele',         15.00,  34.90),
    ('Leave-in Anticrespo 150ml',           'cuidados_cabelo',       20.00,  44.90),
    ('Paleta de Sombras Nude',              'maquiagem',             46.00,  99.90),
    ('Loção Pós-Barba Menthol 100ml',       'higiene_pessoal',       16.00,  34.90)
ON CONFLICT DO NOTHING;
