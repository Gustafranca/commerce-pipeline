import os
import psycopg2
from typing import List
from airflow.decorators import task
from etl.etl.config import (
    PG_DBNAME, PG_USER, PG_PASSWORD, PG_HOST, PG_PORT,
    SQL_INIT_DB, SQL_CONSTRAINTS
)

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
                with open(SQL_INIT_DB, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
    finally:
        conn.close()
        
@task
def load(dataset: str, cleaned_path: str):
    conn = psycopg2.connect(dbname=PG_DBNAME, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    try:
        with conn:
            with conn.cursor() as cur:
                # Limpa a tabela antes de carregar para evitar erros de chave duplicada
                cur.execute(f"TRUNCATE TABLE {dataset} CASCADE;")
                with open(cleaned_path, "r", encoding="utf-8") as f:
                    cur.copy_expert(f"COPY {dataset} FROM STDIN WITH CSV HEADER DELIMITER ';'", f)
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
                        try:
                            cur.execute(cmd)
                        except psycopg2.errors.DuplicateObject:
                            conn.rollback() # Ignora se o constraint ja existe
                        except Exception as e:
                            print(f"Erro ao aplicar constraint: {e}")
                            conn.rollback()
    finally:
        conn.close()
