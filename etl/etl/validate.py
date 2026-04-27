import os
import pandas as pd
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ValidationError
from airflow.decorators import task
from etl.etl.config import LOGS_DIR

class CategoriaProduto(BaseModel):
    categoria_id: Optional[int] = None
    nome_categoria: str
    status_categoria: str


class Cliente(BaseModel):
    cliente_id: Optional[int] = None
    tipo_cliente: str
    nome_razao_social: str
    documento: str
    email: Optional[EmailStr] = None
    telefone: str
    cidade: str
    uf: str
    data_cadastro: date
    data_nascimento: Optional[date] = None
    status_cliente: str


class Loja(BaseModel):
    loja_id: Optional[int] = None
    nome_loja: str
    cidade: str
    uf: str
    regiao: str
    status_loja: str


class Produto(BaseModel):
    produto_id: Optional[int] = None
    nome_produto: str
    custo_unitario: Optional[float] = None
    preco_unitario: float
    status_produto: str


class Vendedor(BaseModel):
    vendedor_id: Optional[int] = None
    nome_vendedor: str
    loja_id: int
    data_admissao: date
    nivel: str
    status_vendedor: str


class Pedido(BaseModel):
    pedido_id: Optional[int] = None
    pedido_codigo: str
    cliente_id: int
    vendedor_id: int
    loja_id: int
    data_pedido: datetime
    canal_venda: str
    status_pedido: str
    valor_frete: float
    valor_desconto: Optional[float] = None
    forma_pagamento_principal: str


class Entrega(BaseModel):
    entrega_id: Optional[int] = None
    pedido_id: int
    transportadora: str
    data_postagem: Optional[date] = None
    data_prevista: Optional[date] = None
    data_entrega_real: Optional[date] = None
    status_entrega: str
    modalidade_frete: str


class ItemPedido(BaseModel):
    item_pedido_id: Optional[int] = None
    pedido_id: int
    sequencia_item: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    desconto_item: float


class EstoqueMovimentacao(BaseModel):
    movimento_id: Optional[int] = None
    produto_id: int
    loja_id: int
    data_movimento: datetime
    tipo_movimento: Optional[str] = None
    quantidade_movimentada: int
    origem_movimento: str
    sistema_origem: str


class Pagamento(BaseModel):
    pagamento_id: Optional[int] = None
    pedido_id: int
    metodo_pagamento: str
    status_pagamento: str
    data_pagamento: datetime
    valor_pagamento: float
    adquirente: str


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

def _log_path(dataset: str, suffix: str) -> str:
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"{dataset}_{suffix}.csv")

@task
def validate(dataset: str, cleaned_path: str) -> int:
    df = pd.read_csv(cleaned_path, sep=";")
    model = MODEL_BY_DATASET[dataset]
    errors = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Convert row to dict, replace NaT/NaN with None for Pydantic
            row_dict = row.to_dict()
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            model(**row_dict)
            valid_rows.append(row)
        except ValidationError as e:
            errors.append({"row": idx, "errors": str(e)})
            
    if errors:
        error_df = pd.DataFrame(errors)
        error_df.to_csv(_log_path(dataset, "validation_errors"), index=False, sep=";")
        
    # Optional: overwrite cleaned_path with only valid rows? 
    # For now, just logging errors.
    return len(errors)
