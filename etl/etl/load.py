import os
import psycopg2
from psycopg2 import sql
from typing import List
from airflow.decorators import task
from etl.etl.config import (
    PG_DBNAME, PG_USER, PG_PASSWORD, PG_HOST, PG_PORT,
    SQL_INIT_DB, SQL_STAGING_TABLES, SQL_CONSTRAINTS
)

DATASET_PRIMARY_KEY = {
    "categorias_produto": "categoria_id",
    "clientes": "cliente_id",
    "lojas": "loja_id",
    "produtos": "produto_id",
    "vendedores": "vendedor_id",
    "pedidos": "pedido_id",
    "entregas": "entrega_id",
    "itens_pedido": "item_pedido_id",
    "estoque_movimentacoes": "movimento_id",
    "pagamentos": "pagamento_id",
}


@task
def list_datasets() -> List[str]:
    return [
        "categorias_produto", "clientes", "lojas", "produtos", 
        "vendedores", "pedidos", "entregas", "itens_pedido", 
        "estoque_movimentacoes", "pagamentos"
    ]

@task
def build_mapping_payloads(datasets: List[str], cleaned_paths: List[str]) -> List[dict]:
    return [{"dataset": dataset, "cleaned_path": cleaned_path} for dataset, cleaned_path in zip(datasets, cleaned_paths)]

@task
def create_tables():
    conn = psycopg2.connect(dbname=PG_DBNAME, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    try:
        with conn:
            with conn.cursor() as cur:
                # Initialize core tables
                with open(SQL_INIT_DB, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
                # Initialize staging tables
                if os.path.exists(SQL_STAGING_TABLES):
                    with open(SQL_STAGING_TABLES, "r", encoding="utf-8") as f:
                        cur.execute(f.read())
    finally:
        conn.close()
        
@task
def load(dataset: str, cleaned_path: str):
    if dataset not in DATASET_PRIMARY_KEY:
        raise ValueError(f"Unsupported dataset for load: {dataset}")
    conn = psycopg2.connect(dbname=PG_DBNAME, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    try:
        with conn:
            with conn.cursor() as cur:
                pk_column = DATASET_PRIMARY_KEY[dataset]
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (dataset,),
                )
                columns = [row[0] for row in cur.fetchall()]
                if not columns:
                    raise ValueError(f"No columns found for dataset: {dataset}")

                temp_table = f"{dataset}_load_tmp"
                cur.execute(
                    sql.SQL("CREATE TEMP TABLE {} (LIKE {} INCLUDING DEFAULTS) ON COMMIT DROP").format(
                        sql.Identifier(temp_table),
                        sql.Identifier(dataset),
                    )
                )
                with open(cleaned_path, "r", encoding="utf-8") as f:
                    cur.copy_expert(f"COPY {temp_table} FROM STDIN WITH CSV HEADER DELIMITER ';'", f)

                quoted_columns = sql.SQL(", ").join(sql.Identifier(col) for col in columns)
                update_columns = [col for col in columns if col != pk_column]
                if update_columns:
                    set_clause = sql.SQL(", ").join(
                        sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
                        for col in update_columns
                    )
                    upsert = sql.SQL(
                        "INSERT INTO {dataset} ({columns}) "
                        "SELECT {columns} FROM {temp_table} "
                        "ON CONFLICT ({pk}) DO UPDATE SET {set_clause}"
                    ).format(
                        dataset=sql.Identifier(dataset),
                        columns=quoted_columns,
                        temp_table=sql.Identifier(temp_table),
                        pk=sql.Identifier(pk_column),
                        set_clause=set_clause,
                    )
                else:
                    upsert = sql.SQL(
                        "INSERT INTO {dataset} ({columns}) "
                        "SELECT {columns} FROM {temp_table} "
                        "ON CONFLICT ({pk}) DO NOTHING"
                    ).format(
                        dataset=sql.Identifier(dataset),
                        columns=quoted_columns,
                        temp_table=sql.Identifier(temp_table),
                        pk=sql.Identifier(pk_column),
                    )
                cur.execute(upsert)
    finally:
        conn.close()

@task
def add_constraints():
    conn = psycopg2.connect(dbname=PG_DBNAME, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    try:
        with conn:
            with conn.cursor() as cur:
                with open(SQL_CONSTRAINTS, "r", encoding="utf-8") as f:
                    commands = f.read().split(';')
                    for cmd in commands:
                        if not cmd.strip(): continue
                        cur.execute("SAVEPOINT constraint_apply")
                        try:
                            cur.execute(cmd)
                        except psycopg2.errors.DuplicateObject:
                            cur.execute("ROLLBACK TO SAVEPOINT constraint_apply")
                        except Exception as e:
                            cur.execute("ROLLBACK TO SAVEPOINT constraint_apply")
                            raise RuntimeError(f"Error applying constraint command: {e}") from e
                        finally:
                            cur.execute("RELEASE SAVEPOINT constraint_apply")
    finally:
        conn.close()
