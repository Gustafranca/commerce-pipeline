from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import List, Optional

import pandas as pd
import psycopg2
from psycopg2 import sql
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook
from pydantic import BaseModel, EmailStr, ValidationError

RAW_DIR = Variable.get("COMMERCE_RAW_DIR", "/opt/airflow/data/raw")
INTERIM_DIR = Variable.get("COMMERCE_INTERIM_DIR", "/opt/airflow/data/interim")
LOGS_DIR = Variable.get("COMMERCE_LOGS_DIR", "/opt/airflow/data/logs")
POSTGRES_CONN_ID = Variable.get("COMMERCE_PG_CONN_ID", "postgres_commerce")
PG_HOST = Variable.get("COMMERCE_PG_HOST", "host.docker.internal")
PG_PORT = int(Variable.get("COMMERCE_PG_PORT", "5432"))
PG_DBNAME = Variable.get("COMMERCE_PG_DBNAME", "commerce")
PG_USER = Variable.get("COMMERCE_PG_USER", "postgres")
PG_PASSWORD = Variable.get("COMMERCE_PG_PASSWORD", "1234")

DATASETS = [
    "categorias_produto",
    "clientes",
    "entregas",
    "estoque_movimentacoes",
    "itens_pedido",
    "lojas",
    "pagamentos",
    "pedidos",
    "produtos",
    "vendedores",
]

## LISTANDO AS CLASSES Pydantic para cada dataset
class CategoriaProduto(BaseModel):
    categoria_id: Optional[int]
    nome_categoria: str
    status_categoria: str


class Cliente(BaseModel):
    cliente_id: Optional[int]
    tipo_cliente: str
    nome_razao_social: str
    documento: str
    email: Optional[EmailStr]
    telefone: str
    cidade: str
    uf: str
    data_cadastro: date
    data_nascimento: Optional[date]
    status_cliente: str


class Loja(BaseModel):
    loja_id: Optional[int]
    nome_loja: str
    cidade: str
    uf: str
    regiao: str
    status_loja: str


class Produto(BaseModel):
    produto_id: Optional[int]
    nome_produto: str
    custo_unitario: Optional[float]
    preco_unitario: float
    status_produto: str


class Vendedor(BaseModel):
    vendedor_id: Optional[int]
    nome_vendedor: str
    loja_id: int
    data_admissao: date
    nivel: str
    status_vendedor: str


class Pedido(BaseModel):
    pedido_id: Optional[int]
    pedido_codigo: str
    cliente_id: int
    vendedor_id: int
    loja_id: int
    data_pedido: datetime
    canal_venda: str
    status_pedido: str
    valor_frete: float
    valor_desconto: Optional[float]
    forma_pagamento_principal: str


class Entrega(BaseModel):
    entrega_id: Optional[int]
    pedido_id: int
    transportadora: str
    data_postagem: Optional[date]
    data_prevista: Optional[date]
    data_entrega_real: Optional[date]
    status_entrega: str
    modalidade_frete: str


class ItemPedido(BaseModel):
    item_pedido_id: Optional[int]
    pedido_id: int
    sequencia_item: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    desconto_item: float


class EstoqueMovimentacao(BaseModel):
    movimento_id: Optional[int]
    produto_id: int
    loja_id: int
    data_movimento: datetime
    tipo_movimento: Optional[str]
    quantidade_movimentada: int
    origem_movimento: str
    sistema_origem: str


class Pagamento(BaseModel):
    pagamento_id: Optional[int]
    pedido_id: int
    metodo_pagamento: str
    status_pagamento: str
    data_pagamento: datetime
    valor_pagamento: float
    adquirente: str


## DICTONARY PARA MAPEAR O NOME DO DATASET COM A CLASSE Pydantic
MODEL_BY_DATASET = {
    "categorias_produto": CategoriaProduto,
    "clientes": Cliente,
    "entregas": Entrega,
    "estoque_movimentacoes": EstoqueMovimentacao,
    "itens_pedido": ItemPedido,
    "lojas": Loja,
    "pagamentos": Pagamento,
    "pedidos": Pedido,
    "produtos": Produto,
    "vendedores": Vendedor,
}
    

def _raw_path(dataset: str) -> str:
    return os.path.join(RAW_DIR, f"{dataset}.csv")


def _interim_path(dataset: str) -> str:
    return os.path.join(INTERIM_DIR, f"{dataset}.csv")


def _log_path(dataset: str, suffix: str) -> str:
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"{dataset}_{suffix}.csv")

## FUNÇÃO PARA TRANSFORMAR OS DADOS DO DATASET EM UM DATAFRAME
def _transform(dataset: str, df: pd.DataFrame) -> pd.DataFrame:
    if dataset == "itens_pedido":
        df["desconto_item"] = (
            df["desconto_item"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")
    elif dataset == "clientes":
        df["data_nascimento"] = pd.to_datetime(
            df["data_nascimento"], format="%d/%m/%Y", errors="coerce"
        )
        df["data_cadastro"] = pd.to_datetime(df["data_cadastro"], errors="coerce")
    elif dataset == "pedidos":
        df["valor_frete"] = (
            df["valor_frete"].astype(str).str.replace(",", ".", regex=False).astype(float)
        )
        df["data_pedido"] = df["data_pedido"].astype(str).apply(
            lambda x: x + ":00" if len(x.split(":")) == 2 else x
        )
        df["data_pedido"] = df["data_pedido"].str.replace("/", "-", regex=False)
        df["data_pedido"] = pd.to_datetime(df["data_pedido"], dayfirst=True, errors="coerce")
    elif dataset == "estoque_movimentacoes":
        df["quantidade_movimentada"] = df["quantidade_movimentada"].replace("dez", "10")
        df["quantidade_movimentada"] = pd.to_numeric(
            df["quantidade_movimentada"], errors="coerce"
        ).astype("Int64")
        df["data_movimento"] = df["data_movimento"].astype(str).apply(
            lambda x: x + ":00" if len(x.split(":")) == 2 else x
        )
        df["data_movimento"] = df["data_movimento"].str.replace("/", "-", regex=False)
        df["data_movimento"] = pd.to_datetime(
            df["data_movimento"], dayfirst=True, errors="coerce"
        )
    elif dataset == "entregas":
        df["data_prevista"] = pd.to_datetime(df["data_prevista"], errors="coerce")
        if "data_postagem" in df.columns:
            df["data_postagem"] = pd.to_datetime(df["data_postagem"], errors="coerce")
        if "data_entrega_real" in df.columns:
            df["data_entrega_real"] = pd.to_datetime(
                df["data_entrega_real"], errors="coerce"
            )
    elif dataset == "produtos":
        df["preco_unitario"] = (
            df["preco_unitario"]
            .astype(str)
            .str.replace("R$ ", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")
        if "custo_unitario" in df.columns:
            df["custo_unitario"] = pd.to_numeric(
                df["custo_unitario"].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )
    elif dataset == "vendedores":
        df["data_admissao"] = pd.to_datetime(df["data_admissao"], errors="coerce")

    null_rows = df[df.isnull().any(axis=1)]
    if not null_rows.empty:
        null_rows.to_csv(_log_path(dataset, "null"), index=False, sep=";")
        df = df.dropna()
    return df

## FUNÇÃO PARA VALIDAR OS DADOS DO DATASET COM A CLASSE Pydantic
def _validate_with_pydantic(dataset: str, df: pd.DataFrame) -> List[str]:
    model = MODEL_BY_DATASET[dataset]
    errors = []
    for idx, row in df.iterrows():
        try:
            model(**row.to_dict())
        except ValidationError as e:
            errors.append(f"row={idx} errors={e}")
    return errors

## DAG PARA ETL DO COMERCE
@dag(
    schedule=None,  # defina "0 2 * * *" se quiser diario as 02:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=3)},
    tags=["etl", "commerce", "csv", "postgres"],
)
def commerce_etl():
    ## TASK PARA LISTAR OS DATASETS
    @task
    def list_datasets() -> List[str]:
        return DATASETS

    ## TASK PARA LIMPAR OS DADOS DO DATASET
    @task
    def clean(dataset: str) -> str:
        raw_path = _raw_path(dataset)
        if not os.path.exists(raw_path):
            raise AirflowException(f"Arquivo bruto nao encontrado: {raw_path}")
        os.makedirs(INTERIM_DIR, exist_ok=True)
        df = pd.read_csv(raw_path, sep=";")
        df = _transform(dataset, df)
        out = _interim_path(dataset)
        df.to_csv(out, index=False, sep=";")
        return out

    ## TASK PARA VALIDAR OS DADOS DO DATASET
    @task
    def validate(dataset: str, cleaned_path: str) -> int:
        df = pd.read_csv(cleaned_path, sep=";")
        model = MODEL_BY_DATASET[dataset]
        errors = []
        error_by_column = {}

        for idx, row in df.iterrows():
            try:
                model(**row.to_dict())
            except ValidationError as exc:
                parsed_errors = exc.errors()
                # Para clientes, ignora email invalido e valida o restante da linha.
                if dataset == "clientes":
                    parsed_errors = [
                        err
                        for err in parsed_errors
                        if not (err.get("loc") and err.get("loc")[0] == "email")
                    ]

                if not parsed_errors:
                    continue

                errors.append(f"row={idx} errors={parsed_errors}")
                for err in parsed_errors:
                    loc = err.get("loc", ())
                    column = str(loc[0]) if loc else "unknown"
                    error_by_column[column] = error_by_column.get(column, 0) + 1

        if errors:
            with open(_log_path(dataset, "validation_errors"), "w", encoding="utf-8") as f:
                f.write("dataset,total_errors,error_by_column\n")
                f.write(
                    f"{dataset},{len(errors)},{error_by_column}\n\n"
                )
                f.write("error\n")
                for err in errors:
                    f.write(f"{err}\n")
            raise AirflowException(
                f"Validacao falhou para {dataset} com {len(errors)} erros. "
                f"Colunas com erro: {error_by_column}"
            )
        return len(df)

    ## TASK PARA CARREGAR OS DADOS DO DATASET NO BANCO DE DADOS
    @task
    def load(dataset: str, cleaned_path: str) -> int:
        try:
            hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
            conn = hook.get_conn()
        except Exception:
            # Fallback para credenciais diretas quando a conexao do Airflow nao existe.
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DBNAME,
                user=PG_USER,
                password=PG_PASSWORD,
            )
        conn.autocommit = True
        table = dataset
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1
                  FROM information_schema.tables
                  WHERE table_schema='public' AND table_name=%s
                )
                """,
                (table,),
            )
            exists = cur.fetchone()[0]
            if not exists:
                raise AirflowException(
                    f"Tabela '{table}' nao existe. Crie-a antes do load."
                )

            # Descobre colunas da tabela alvo para montar INSERT dinamico.
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
                ORDER BY ordinal_position
                """,
                (table,),
            )
            columns = [row[0] for row in cur.fetchall()]
            if not columns:
                raise AirflowException(f"Tabela '{table}' sem colunas.")

            # Descobre PK para aplicar ON CONFLICT e permitir reruns idempotentes.
            cur.execute(
                """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a
                  ON a.attrelid = i.indrelid
                 AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                  AND i.indisprimary
                ORDER BY array_position(i.indkey, a.attnum)
                """,
                (f"public.{table}",),
            )
            pk_columns = [row[0] for row in cur.fetchall()]

            temp_table = f"tmp_{table}_load"
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(temp_table))
            )
            cur.execute(
                sql.SQL(
                    "CREATE TEMP TABLE {} AS SELECT * FROM {} WHERE 1=0"
                ).format(sql.Identifier(temp_table), sql.Identifier(table))
            )

            with open(cleaned_path, "r", encoding="utf-8") as f:
                cur.copy_expert(
                    sql.SQL("COPY {} FROM STDIN WITH CSV HEADER DELIMITER ';'")
                    .format(sql.Identifier(temp_table))
                    .as_string(conn),
                    f,
                )

            cols_sql = sql.SQL(", ").join([sql.Identifier(col) for col in columns])
            if pk_columns:
                conflict_sql = sql.SQL(", ").join(
                    [sql.Identifier(col) for col in pk_columns]
                )
                insert_sql = sql.SQL(
                    "INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) DO NOTHING"
                ).format(
                    sql.Identifier(table),
                    cols_sql,
                    cols_sql,
                    sql.Identifier(temp_table),
                    conflict_sql,
                )
            else:
                insert_sql = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {}").format(
                    sql.Identifier(table),
                    cols_sql,
                    cols_sql,
                    sql.Identifier(temp_table),
                )

            cur.execute(insert_sql)
        return 1

    @task
    def build_mapping_payloads(
        datasets: List[str], cleaned_paths: List[str]
    ) -> List[dict]:
        # Faz pareamento 1-para-1 (dataset[i] -> cleaned_paths[i]).
        return [
            {"dataset": dataset, "cleaned_path": cleaned_path}
            for dataset, cleaned_path in zip(datasets, cleaned_paths)
        ]

    ## TASK PARA EXECUTAR O ETL
    datasets = list_datasets()
    cleaned_paths = clean.expand(dataset=datasets)
    mapping_payloads = build_mapping_payloads(datasets, cleaned_paths)
    validated_counts = validate.expand_kwargs(mapping_payloads)
    loaded = load.expand_kwargs(mapping_payloads)
    validated_counts >> loaded


commerce_etl()

if __name__ == "__main__":
    dag.test()