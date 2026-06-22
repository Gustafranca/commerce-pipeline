"""Unit tests: `validate_payload` for every warehouse entity (same gate as ingest and promote)."""

from __future__ import annotations

import pytest

from commerce_models import MODEL_BY_DATASET
from staged_promote import validate_payload

# Minimal valid payloads after `normalize_staged_payload` + Pydantic (string forms as from manual ingest).
_VALID_BY_DATASET: dict[str, dict] = {
    "categorias_produto": {
        "nome_categoria": "Eletrônicos",
        "status_categoria": "ativo",
    },
    "clientes": {
        "tipo_cliente": "PF",
        "nome_razao_social": "Maria Silva",
        "documento": "12345678901",
        "telefone": "11999999999",
        "cidade": "São Paulo",
        "uf": "SP",
        "status_cliente": "ativo",
    },
    "lojas": {
        "nome_loja": "Loja Centro",
        "cidade": "São Paulo",
        "uf": "SP",
        "regiao": "Sudeste",
        "status_loja": "ativa",
    },
    "produtos": {
        "nome_produto": "Caneta",
        "categoria_id": "1",
        "marca": "MarcaX",
        "preco_unitario": "10,50",
        "status_produto": "ativo",
    },
    "vendedores": {
        "nome_vendedor": "João",
        "loja_id": "1",
        "data_admissao": "01/01/2020",
        "nivel": "1",
        "status_vendedor": "ativo",
    },
    "pedidos": {
        "pedido_codigo": "PED-1",
        "cliente_id": "1",
        "vendedor_id": "1",
        "loja_id": "1",
        "data_pedido": "15/03/2024 14:30:00",
        "canal_venda": "online",
        "status_pedido": "aberto",
        "valor_frete": "0",
        "forma_pagamento_principal": "pix",
    },
    "entregas": {
        "pedido_id": "1",
        "transportadora": "Correios",
        "data_postagem": "2024-01-15 10:00:00",
        "status_entrega": "postado",
        "modalidade_frete": "PAC",
    },
    "itens_pedido": {
        "pedido_id": "1",
        "sequencia_item": "1",
        "produto_id": "1",
        "quantidade": "2",
        "preco_unitario": "25,00",
        "desconto_item": "0",
    },
    "estoque_movimentacoes": {
        "produto_id": "1",
        "loja_id": "1",
        "data_movimento": "2024-01-15 10:00:00",
        "quantidade_movimentada": "5",
        "origem_movimento": "ajuste",
        "sistema_origem": "erp",
    },
    "pagamentos": {
        "pedido_id": "1",
        "metodo_pagamento": "pix",
        "status_pagamento": "aprovado",
        "data_pagamento": "2024-01-15T10:00:00",
        "valor_pagamento": "100,00",
        "adquirente": "Stone",
    },
}


def test_valid_payloads_cover_all_model_datasets() -> None:
    assert set(_VALID_BY_DATASET.keys()) == set(MODEL_BY_DATASET.keys())


@pytest.mark.parametrize("dataset", sorted(MODEL_BY_DATASET.keys()))
def test_validate_payload_accepts_valid_manual_payload(dataset: str) -> None:
    payload = _VALID_BY_DATASET[dataset]
    inst, errs = validate_payload(dataset, payload)
    assert errs == []
    assert inst is not None


@pytest.mark.parametrize("dataset", sorted(MODEL_BY_DATASET.keys()))
def test_validate_payload_rejects_empty_payload(dataset: str) -> None:
    _, errs = validate_payload(dataset, {})
    assert errs


@pytest.mark.parametrize("dataset", sorted(MODEL_BY_DATASET.keys()))
def test_validate_payload_rejects_unknown_entity(dataset: str) -> None:
    """Wrong path segment / entity_name must not match another model."""
    _, errs = validate_payload("not_a_real_table_" + dataset, _VALID_BY_DATASET[dataset])
    assert errs
    assert any("Unsupported entity_name" in e for e in errs)


def test_validate_payload_clientes_rejects_invalid_tipo_cliente() -> None:
    p = {**_VALID_BY_DATASET["clientes"], "tipo_cliente": "XX"}
    _, errs = validate_payload("clientes", p)
    assert errs
    assert any("varchar(2)" in e or "PF" in e for e in errs)
