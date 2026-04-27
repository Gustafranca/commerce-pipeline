"""
Dado os tipos estabelecidos no banco de dados, é necessário realizar uma
limpeza e transformação dos dados para garantir a consistência e integridade
dos mesmos antes de carregá-los no banco. O código abaixo realiza as
seguintes operações:

1. Lê os arquivos CSV brutos para DataFrames do pandas.
2. Realiza a limpeza e transformação dos dados, incluindo:
   - Conversão de tipos de dados (ex: string para float, string para datetime).
   - Tratamento de valores nulos (ex: remoção de linhas com valores nulos).
   - Correção de formatação (ex: substituição de vírgulas por pontos em valores numéricos, padronização de formatos de data).
3. Salva os DataFrames limpos em arquivos CSV na pasta interim, prontos
    para serem carregados no banco de dados.
"""

import pandas as pd

folder_raw = '/home/gflameida2/repositorios/pipeline-commerce/data/raw/'
folder_interim = '/home/gflameida2/repositorios/pipeline-commerce/data/interim/'
folder_logs = '/home/gflameida2/repositorios/pipeline-commerce/data/logs/'

categorias_produto = pd.read_csv(folder_raw + 'categorias_produto.csv', sep=';')
clientes = pd.read_csv(folder_raw + 'clientes.csv', sep=';')
entregas = pd.read_csv(folder_raw + 'entregas.csv', sep=';')
estoque_movimentacoes = pd.read_csv(folder_raw + 'estoque_movimentacoes.csv', sep=';')
itens_pedido = pd.read_csv(folder_raw + 'itens_pedido.csv', sep=';')
lojas = pd.read_csv(folder_raw + 'lojas.csv', sep=';')
pagamentos = pd.read_csv(folder_raw + 'pagamentos.csv', sep=';')
pedidos = pd.read_csv(folder_raw + 'pedidos.csv', sep=';')
produtos = pd.read_csv(folder_raw + 'produtos.csv', sep=';')
vendedores = pd.read_csv(folder_raw + 'vendedores.csv', sep=';')


lista_df = [categorias_produto, clientes, entregas,
            estoque_movimentacoes, itens_pedido, lojas,
            pagamentos, pedidos, produtos, vendedores]

lista_df_names = ['categorias_produto', 'clientes', 'entregas',
                  'estoque_movimentacoes', 'itens_pedido', 'lojas',
                  'pagamentos', 'pedidos', 'produtos', 'vendedores']

primary_key = ['categoria_id', 'cliente_id', 'entrega_id',
               'movimento_id', 'item_pedido_id', 'loja_id',
               'pagamento_id', 'pedido_id', 'produto_id', 'vendedor_id']

itens_pedido['desconto_item'] = itens_pedido['desconto_item'].str.replace(',', '.').astype(float)
itens_pedido['preco_unitario'] = itens_pedido['preco_unitario'].astype(float)

clientes['data_nascimento'] = pd.to_datetime(clientes['data_nascimento'], format='%d/%m/%Y')
clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'], errors='coerce')


# Handling formart issues in 'pedidos' DataFrame
pedidos['valor_frete'] = pedidos['valor_frete'].str.replace(',', '.').astype(float)
pedidos['data_pedido'] = pedidos['data_pedido'].apply(lambda x: x + ':00' if len(x.split(':')) == 2 else x)
pedidos['data_pedido'] = pedidos['data_pedido'].str.replace('/', '-', regex=False)
pedidos['data_pedido'] = pd.to_datetime(pedidos['data_pedido'], dayfirst=True, errors='coerce')

# Handling formart issues in 'estoque_movimentacoes' DataFrame
estoque_movimentacoes['quantidade_movimentada'] = estoque_movimentacoes['quantidade_movimentada'].replace('dez','10')
estoque_movimentacoes['quantidade_movimentada'] = estoque_movimentacoes['quantidade_movimentada'].astype(int)
estoque_movimentacoes['data_movimento'] = estoque_movimentacoes['data_movimento'].apply(lambda x: x + ':00' if len(x.split(':')) == 2 else x)
estoque_movimentacoes['data_movimento'] = estoque_movimentacoes['data_movimento'].str.replace('/', '-', regex=False)
estoque_movimentacoes['data_movimento'] = pd.to_datetime(estoque_movimentacoes['data_movimento'], dayfirst=True, errors='coerce')

# Handling formart issues in 'entregas' DataFrame
entregas['data_prevista'] = pd.to_datetime(entregas['data_prevista'], errors='coerce')

# Handling formart issues in 'produtos' DataFrame
produtos['preco_unitario'] = produtos['preco_unitario'].str.replace('R$ ', '').replace('.', '')
produtos['preco_unitario'] = produtos['preco_unitario'].str.replace(',', '.').astype(float)



for df, name in zip(lista_df, lista_df_names):
    print('---' * 20)
    print(f"DataFrame: {name}")
    
    # Identify rows with null values
    null_rows = df[df.isnull().any(axis=1)]
    if not null_rows.empty:
        null_rows.to_csv(folder_logs + f'{name}_null.csv', index=False, sep=';')
        
    # Drop rows with null values from the original DataFrame
    df_cleaned = df.dropna()
    
    print('Nulos after cleaning: ')
    print(df_cleaned.isnull().sum())
    
    df_cleaned.to_csv(folder_interim + f'{name}.csv', index=False, sep=';')
