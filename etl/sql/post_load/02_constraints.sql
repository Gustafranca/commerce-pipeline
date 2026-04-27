ALTER TABLE pedidos
ADD CONSTRAINT fk_pedidos_cliente
FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id);

ALTER TABLE pedidos
ADD CONSTRAINT fk_pedidos_vendedor
FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id);

ALTER TABLE pedidos
ADD CONSTRAINT fk_pedidos_loja
FOREIGN KEY (loja_id) REFERENCES lojas(loja_id);

ALTER TABLE entregas
ADD CONSTRAINT fk_entregas_pedido
FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id);

ALTER TABLE itens_pedido
ADD CONSTRAINT fk_itens_pedido_pedido
FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id);

ALTER TABLE itens_pedido
ADD CONSTRAINT fk_itens_pedido_produto
FOREIGN KEY (produto_id) REFERENCES produtos(produto_id);

ALTER TABLE pagamentos
ADD CONSTRAINT fk_pagamentos_pedido
FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id);

ALTER TABLE estoque_movimentacoes
ADD CONSTRAINT fk_estoque_produto
FOREIGN KEY (produto_id) REFERENCES produtos(produto_id);

ALTER TABLE estoque_movimentacoes
ADD CONSTRAINT fk_estoque_loja
FOREIGN KEY (loja_id) REFERENCES lojas(loja_id);
