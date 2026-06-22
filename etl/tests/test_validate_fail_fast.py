from __future__ import annotations

import pandas as pd
import pytest

from etl.etl.validate import validate_dataframe


def test_validate_dataframe_raises_when_rows_are_invalid() -> None:
    bad_clientes = pd.DataFrame(
        [
            {
                "tipo_cliente": "PF",
                "nome_razao_social": "Cliente Teste",
                "documento": "12345678900",
                "telefone": "11999999999",
                "cidade": "Sao Paulo",
                "uf": "SP",
                "status_cliente": "ativo",
            },
            {
                "tipo_cliente": "PJ",
                "nome_razao_social": "Cliente Invalido",
                "documento": "00999999999999",
                "telefone": "11999999999",
                "cidade": "Sao Paulo",
                "uf": "SP",
            },
        ]
    )

    with pytest.raises(ValueError, match="Validation failed"):
        validate_dataframe(dataset="clientes", dataframe=bad_clientes)


def test_validate_dataframe_returns_zero_when_rows_are_valid() -> None:
    valid_clientes = pd.DataFrame(
        [
            {
                "tipo_cliente": "PF",
                "nome_razao_social": "Cliente Teste",
                "documento": "12345678900",
                "telefone": "11999999999",
                "cidade": "Sao Paulo",
                "uf": "SP",
                "status_cliente": "ativo",
            }
        ]
    )

    errors_count, errors = validate_dataframe(dataset="clientes", dataframe=valid_clientes)

    assert errors_count == 0
    assert errors == []
