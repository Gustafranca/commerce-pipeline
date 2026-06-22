"""Shared Pydantic models for commerce datasets (ETL CSV validation + staged promote)."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


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
    data_cadastro: Optional[date] = None
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
    categoria_id: int
    marca: str
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
    data_postagem: datetime
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
