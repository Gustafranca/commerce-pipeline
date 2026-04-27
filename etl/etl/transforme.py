import os
import pandas as pd
from airflow.decorators import task
from airflow.exceptions import AirflowException
from etl.etl.config import RAW_DIR, INTERIM_DIR, LOGS_DIR

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
    return df

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
