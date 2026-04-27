CREATE TABLE IF NOT EXISTS categorias_produto (
    categoria_id SERIAL PRIMARY KEY,
    nome_categoria VARCHAR(255) NOT NULL,
    status_categoria VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS clientes (
    cliente_id SERIAL PRIMARY KEY,
    tipo_cliente VARCHAR(2) NOT NULL,
    nome_razao_social VARCHAR(255) NOT NULL,
    documento VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    telefone VARCHAR(20) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    data_cadastro DATE,
    data_nascimento DATE,
    status_cliente VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS lojas (
    loja_id SERIAL PRIMARY KEY,
    nome_loja VARCHAR(255) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    regiao VARCHAR(50) NOT NULL,
    status_loja VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    produto_id SERIAL PRIMARY KEY,
    nome_produto VARCHAR(255) NOT NULL,
    categoria_id INT NOT NULL,
    marca VARCHAR(100) NOT NULL,
    custo_unitario DECIMAL(10, 2),
    preco_unitario DECIMAL(10, 2),
    status_produto VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS vendedores (
    vendedor_id SERIAL PRIMARY KEY,
    nome_vendedor VARCHAR(255) NOT NULL,
    loja_id INT NOT NULL,
    data_admissao DATE NOT NULL,
    nivel VARCHAR(2) NOT NULL,
    status_vendedor VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id SERIAL PRIMARY KEY,
    pedido_codigo VARCHAR(20) NOT NULL,
    cliente_id INT NOT NULL,
    vendedor_id INT NOT NULL,
    loja_id INT NOT NULL,
    data_pedido TIMESTAMP,
    canal_venda VARCHAR(50) NOT NULL,
    status_pedido VARCHAR(50) NOT NULL,
    valor_frete DECIMAL(10, 2) NOT NULL,
    valor_desconto DECIMAL(10, 2),
    forma_pagamento_principal VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS entregas (
    entrega_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    transportadora VARCHAR(100) NOT NULL,
    data_postagem TIMESTAMP NOT NULL,
    data_prevista DATE,
    data_entrega_real DATE,
    status_entrega VARCHAR(50) NOT NULL,
    modalidade_frete VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    item_pedido_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    sequencia_item INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10, 2),
    desconto_item DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
    movimento_id SERIAL PRIMARY KEY,
    produto_id INT NOT NULL,
    loja_id INT NOT NULL,
    data_movimento TIMESTAMP,
    tipo_movimento VARCHAR(50),
    quantidade_movimentada INT NOT NULL,
    origem_movimento VARCHAR(50) NOT NULL,
    sistema_origem VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS pagamentos (
    pagamento_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    metodo_pagamento VARCHAR(50) NOT NULL,
    status_pagamento VARCHAR(50) NOT NULL,
    data_pagamento TIMESTAMP NOT NULL,
    valor_pagamento DECIMAL(10, 2) NOT NULL,
    adquirente VARCHAR(50) NOT NULL
);
