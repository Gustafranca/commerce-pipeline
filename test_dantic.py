from pydantic import BaseModel, EmailStr, ValidationError
from typing import Optional
from datetime import date, datetime
import pandas as pd


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
    categoria_id: int
    marca: str
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
    data_postagem: datetime
    data_prevista: date
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
    
    
def validate_and_convert(df, model):
    instances = []
    for _, row in df.iterrows():
        try:
            instance = model(**row.to_dict())
            instances.append(instance)
        except ValidationError as e:
            print(f"Validation error: {e}")
    return instances

# Load CSV files into DataFrames
folder_raw = '/home/gflameida2/repositorios/pipeline-commerce/data/interim/'

categorias_produto_df = pd.read_csv(folder_raw + 'categorias_produto.csv', sep=';')
clientes_df = pd.read_csv(folder_raw + 'clientes.csv', sep=';')
entregas_df = pd.read_csv(folder_raw + 'entregas.csv', sep=';')
estoque_movimentacoes_df = pd.read_csv(folder_raw + 'estoque_movimentacoes.csv', sep=';')
itens_pedido_df = pd.read_csv(folder_raw + 'itens_pedido.csv', sep=';')
lojas_df = pd.read_csv(folder_raw + 'lojas.csv', sep=';')
pagamentos_df = pd.read_csv(folder_raw + 'pagamentos.csv', sep=';')
pedidos_df = pd.read_csv(folder_raw + 'pedidos.csv', sep=';')
produtos_df = pd.read_csv(folder_raw + 'produtos.csv', sep=';')
vendedores_df = pd.read_csv(folder_raw + 'vendedores.csv', sep=';')

# Validate and convert DataFrames to Pydantic model instances
categorias_produto_instances = validate_and_convert(categorias_produto_df, CategoriaProduto)
clientes_instances = validate_and_convert(clientes_df, Cliente)
entregas_instances = validate_and_convert(entregas_df, Entrega)
estoque_movimentacoes_instances = validate_and_convert(estoque_movimentacoes_df, EstoqueMovimentacao)
itens_pedido_instances = validate_and_convert(itens_pedido_df, ItemPedido)
lojas_instances = validate_and_convert(lojas_df, Loja)
pagamentos_instances = validate_and_convert(pagamentos_df, Pagamento)
pedidos_instances = validate_and_convert(pedidos_df, Pedido)
produtos_instances = validate_and_convert(produtos_df, Produto)
vendedores_instances = validate_and_convert(vendedores_df, Vendedor)