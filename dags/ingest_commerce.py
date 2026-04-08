from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

DATA_DIR = Path("/opt/airflow/data")
POSTGRES_CONN_ID = "postgres_commerce"

default_args = {
"owner": "airflow",
"depends_on_past": False,
"retries": 0,
}

ddl_sql = """
    -- Create tables in FK-safe order
    CREATE TABLE IF NOT EXISTS categorias_produto (
    categoria_id SERIAL PRIMARY KEY,
    nome_categoria VARCHAR(255) NOT NULL,
    status_categoria VARCHAR(50) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lojas (
    loja_id SERIAL PRIMARY KEY,
    nome_loja VARCHAR(255) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    regiao VARCHAR(50) NOT NULL,
    status_loja VARCHAR(20) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS vendedores (
    vendedor_id SERIAL PRIMARY KEY,
    nome_vendedor VARCHAR(255) NOT NULL,
    loja_id INT NOT NULL,
    data_admissao DATE NOT NULL,
    nivel VARCHAR(2) NOT NULL,
    status_vendedor VARCHAR(20) NOT NULL,
    FOREIGN KEY (loja_id) REFERENCES lojas(loja_id)
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
    data_cadastro DATE NOT NULL,
    data_nascimento DATE,
    status_cliente VARCHAR(20) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS produtos (
    produto_id SERIAL PRIMARY KEY,
    nome_produto VARCHAR(255) NOT NULL,
    categoria_id INT NOT NULL,
    marca VARCHAR(100) NOT NULL,
    custo_unitario DECIMAL(10, 2),
    preco_unitario DECIMAL(10, 2) NOT NULL,
    status_produto VARCHAR(20) NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias_produto(categoria_id)
    );

    CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id SERIAL PRIMARY KEY,
    pedido_codigo VARCHAR(20) NOT NULL,
    cliente_id INT NOT NULL,
    vendedor_id INT NOT NULL,
    loja_id INT NOT NULL,
    data_pedido TIMESTAMP NOT NULL,
    canal_venda VARCHAR(50) NOT NULL,
    status_pedido VARCHAR(50) NOT NULL,
    valor_frete DECIMAL(10, 2) NOT NULL,
    valor_desconto DECIMAL(10, 2),
    forma_pagamento_principal VARCHAR(50) NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id),
    FOREIGN KEY (loja_id) REFERENCES lojas(loja_id)
    );

    CREATE TABLE IF NOT EXISTS itens_pedido (
    item_pedido_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    sequencia_item INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    desconto_item DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id),
    FOREIGN KEY (produto_id) REFERENCES produtos(produto_id)
    );

    CREATE TABLE IF NOT EXISTS pagamentos (
    pagamento_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    metodo_pagamento VARCHAR(50) NOT NULL,
    status_pagamento VARCHAR(50) NOT NULL,
    data_pagamento TIMESTAMP NOT NULL,
    valor_pagamento DECIMAL(10, 2) NOT NULL,
    adquirente VARCHAR(50) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id)
    );

    CREATE TABLE IF NOT EXISTS entregas (
    entrega_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    transportadora VARCHAR(100) NOT NULL,
    data_postagem TIMESTAMP NOT NULL,
    data_prevista DATE NOT NULL,
    data_entrega_real DATE,
    status_entrega VARCHAR(50) NOT NULL,
    modalidade_frete VARCHAR(50) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id)
    );

    CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
    movimento_id SERIAL PRIMARY KEY,
    produto_id INT NOT NULL,
    loja_id INT NOT NULL,
    data_movimento TIMESTAMP NOT NULL,
    tipo_movimento VARCHAR(50),
    quantidade_movimentada INT NOT NULL,
    origem_movimento VARCHAR(50) NOT NULL,
    sistema_origem VARCHAR(50) NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos(produto_id),
    FOREIGN KEY (loja_id) REFERENCES lojas(loja_id)
    );
    """
    
def copy_csv_to_table(table: str, filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    # Treat empty strings as NULL to avoid type errors on numeric/date columns
    copy_sql = f"""
    COPY {table}
    FROM STDIN
    WITH (
        FORMAT csv,
        HEADER true,
        DELIMITER ',',
        QUOTE '"',
        NULL ''
    )
    """ 
    with hook.get_conn() as conn:
        with conn.cursor() as cur, open(path, "r", encoding="utf-8") as f:
            cur.copy_expert(copy_sql, f)
            conn.commit()

reset_sequences_sql = """
SELECT setval(pg_get_serial_sequence('categorias_produto','categoria_id'), COALESCE(MAX(categoria_id), 1), true) FROM categorias_produto;
SELECT setval(pg_get_serial_sequence('lojas','loja_id'), COALESCE(MAX(loja_id), 1), true) FROM lojas;
SELECT setval(pg_get_serial_sequence('vendedores','vendedor_id'), COALESCE(MAX(vendedor_id), 1), true) FROM vendedores;
SELECT setval(pg_get_serial_sequence('clientes','cliente_id'), COALESCE(MAX(cliente_id), 1), true) FROM clientes;
SELECT setval(pg_get_serial_sequence('produtos','produto_id'), COALESCE(MAX(produto_id), 1), true) FROM produtos;
SELECT setval(pg_get_serial_sequence('pedidos','pedido_id'), COALESCE(MAX(pedido_id), 1), true) FROM pedidos;
SELECT setval(pg_get_serial_sequence('itens_pedido','item_pedido_id'), COALESCE(MAX(item_pedido_id), 1), true) FROM itens_pedido;
SELECT setval(pg_get_serial_sequence('pagamentos','pagamento_id'), COALESCE(MAX(pagamento_id), 1), true) FROM pagamentos;
SELECT setval(pg_get_serial_sequence('entregas','entrega_id'), COALESCE(MAX(entrega_id), 1), true) FROM entregas;
SELECT setval(pg_get_serial_sequence('estoque_movimentacoes','movimento_id'), COALESCE(MAX(movimento_id), 1), true) FROM estoque_movimentacoes;
"""

with DAG(
    dag_id="ingest_commerce_csvs",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None, # trigger manually
    catchup=False,
    tags=["commerce", "ingest"],) as dag:
    create_schema = PostgresOperator(
    task_id="create_schema",
    postgres_conn_id=POSTGRES_CONN_ID,
    sql=ddl_sql,
)

# Load order must respect FKs
load_categorias = PythonOperator(
    task_id="load_categorias_produto",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "categorias_produto", "filename": "categorias_produto.csv"},
)

load_lojas = PythonOperator(
    task_id="load_lojas",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "lojas", "filename": "lojas.csv"},
)

load_vendedores = PythonOperator(
    task_id="load_vendedores",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "vendedores", "filename": "vendedores.csv"},
)

load_clientes = PythonOperator(
    task_id="load_clientes",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "clientes", "filename": "clientes.csv"},
)

load_produtos = PythonOperator(
    task_id="load_produtos",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "produtos", "filename": "produtos.csv"},
)

load_pedidos = PythonOperator(
    task_id="load_pedidos",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "pedidos", "filename": "pedidos.csv"},
)

load_itens = PythonOperator(
    task_id="load_itens_pedido",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "itens_pedido", "filename": "itens_pedido.csv"},
)

load_pagamentos = PythonOperator(
    task_id="load_pagamentos",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "pagamentos", "filename": "pagamentos.csv"},
)

load_entregas = PythonOperator(
    task_id="load_entregas",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "entregas", "filename": "entregas.csv"},
)

load_estoque = PythonOperator(
    task_id="load_estoque_movimentacoes",
    python_callable=copy_csv_to_table,
    op_kwargs={"table": "estoque_movimentacoes", "filename": "estoque_movimentacoes.csv"},
)

reset_sequences = PostgresOperator(
    task_id="reset_sequences",
    postgres_conn_id=POSTGRES_CONN_ID,
    sql=reset_sequences_sql,
)

# Dependencies
create_schema >> [load_categorias, load_lojas, load_clientes]
load_categorias >> load_produtos
load_lojas >> load_vendedores
[load_clientes, load_vendedores, load_lojas] >> load_pedidos
[load_produtos, load_pedidos] >> load_itens
load_pedidos >> [load_pagamentos, load_entregas]
[load_produtos, load_lojas] >> load_estoque

[load_itens, load_pagamentos, load_entregas, load_estoque] >> reset_sequences