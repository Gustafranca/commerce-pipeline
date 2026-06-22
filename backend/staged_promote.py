"""Normalize + Pydantic validate staged payloads, then INSERT into warehouse tables."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DataError, IntegrityError

from commerce_models import MODEL_BY_DATASET


class PromoteConflictError(Exception):
    """INSERT violated a database constraint (e.g. duplicate key, FK)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class StagedValidationError(Exception):
    """Payload failed Pydantic validation (same rules as ETL validate task)."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(("; ").join(errors))


TIPO_CLIENTE_VARCHAR2_MSG = "This field is varchar(2) (PF, PJ)."


def _cliente_tipo_cliente_errors(tipo: Any) -> List[str]:
    """Warehouse column clientes.tipo_cliente is VARCHAR(2); allowed codes PF / PJ."""
    if tipo is None:
        return []
    if not isinstance(tipo, str):
        return [TIPO_CLIENTE_VARCHAR2_MSG]
    s = tipo.strip()
    if not s:
        return []
    if s.upper() not in ("PF", "PJ"):
        return [TIPO_CLIENTE_VARCHAR2_MSG]
    return []


TABLE_PRIMARY_KEY: Dict[str, str] = {
    "categorias_produto": "categoria_id",
    "clientes": "cliente_id",
    "lojas": "loja_id",
    "produtos": "produto_id",
    "vendedores": "vendedor_id",
    "pedidos": "pedido_id",
    "entregas": "entrega_id",
    "itens_pedido": "item_pedido_id",
    "estoque_movimentacoes": "movimento_id",
    "pagamentos": "pagamento_id",
}


def _empty_to_none(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


def _br_float(v: Any) -> Any:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    s = re.sub(r"R\$\s*", "", s, flags=re.I).replace(" ", "")
    if re.search(r",\d{1,2}$", s) and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return v


def _int_val(v: Any) -> Any:
    if v is None or v == "":
        return None
    if isinstance(v, int):
        return v
    try:
        return int(str(v).strip())
    except ValueError:
        return v


def _parse_to_date(v: Any) -> Any:
    """Coerce BR/common date strings to datetime.date (mirrors ETL transforme.py / cleaning_data)."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        if "T" in s:
            s = s.split("T", 1)[0].strip()
        fmts = (
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d.%m.%Y",
        )
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return v


def _parse_to_datetime(v: Any) -> Any:
    """Coerce BR/common datetime strings to datetime.datetime."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        normalized = s.replace("/", "-")
        dt_formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
        )
        for fmt in dt_formats:
            try:
                parsed = datetime.strptime(normalized, fmt)
                if "%H:%M" in fmt and "%S" not in fmt:
                    return parsed.replace(second=0)
                return parsed
            except ValueError:
                continue
        date_formats = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y")
        for fmt in date_formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    return v


def normalize_staged_payload(dataset: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror key cleaning from ETL transforme.py for JSON/form payloads."""
    d: Dict[str, Any] = {}
    for k, v in (data or {}).items():
        d[k] = _empty_to_none(v)

    if dataset == "itens_pedido":
        for f in ("desconto_item", "preco_unitario"):
            if d.get(f) is not None:
                d[f] = _br_float(d[f])
        if d.get("quantidade") is not None:
            d["quantidade"] = _int_val(d["quantidade"])
        for f in ("pedido_id", "produto_id", "sequencia_item", "item_pedido_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
    elif dataset == "pedidos":
        if d.get("valor_frete") is not None:
            d["valor_frete"] = _br_float(d["valor_frete"])
        if d.get("valor_desconto") is not None:
            d["valor_desconto"] = _br_float(d["valor_desconto"])
        for f in ("cliente_id", "vendedor_id", "loja_id", "pedido_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("data_pedido") and isinstance(d["data_pedido"], str):
            raw = d["data_pedido"].strip()
            parsed = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S"):
                try:
                    parsed = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
            if parsed is None:
                s = raw.replace("/", "-")
                if len(s.split(":")) == 2:
                    s = s + ":00"
                try:
                    parsed = datetime.fromisoformat(s)
                except ValueError:
                    pass
            if parsed is not None:
                d["data_pedido"] = parsed
    elif dataset == "estoque_movimentacoes":
        if d.get("quantidade_movimentada") is not None and isinstance(d["quantidade_movimentada"], str):
            q = d["quantidade_movimentada"].strip().lower()
            if q == "dez":
                d["quantidade_movimentada"] = 10
            else:
                d["quantidade_movimentada"] = _int_val(d["quantidade_movimentada"])
        for f in ("produto_id", "loja_id", "movimento_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("data_movimento") and isinstance(d["data_movimento"], str):
            s = d["data_movimento"].strip().replace("/", "-")
            if len(s.split(":")) == 2:
                s = s + ":00"
            try:
                d["data_movimento"] = datetime.fromisoformat(s)
            except ValueError:
                try:
                    d["data_movimento"] = datetime.strptime(
                        d["data_movimento"].strip().replace("/", "-"), "%d-%m-%Y %H:%M:%S"
                    )
                except ValueError:
                    pass
    elif dataset == "entregas":
        for f in ("pedido_id", "entrega_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("data_postagem") is not None:
            d["data_postagem"] = _parse_to_datetime(d["data_postagem"])
        for f in ("data_prevista", "data_entrega_real"):
            if d.get(f) is not None:
                d[f] = _parse_to_date(d[f])
    elif dataset == "produtos":
        for f in ("produto_id", "categoria_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("preco_unitario") is not None:
            d["preco_unitario"] = _br_float(d["preco_unitario"])
        if d.get("custo_unitario") is not None:
            d["custo_unitario"] = _br_float(d["custo_unitario"])
    elif dataset == "vendedores":
        for f in ("vendedor_id", "loja_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("data_admissao") is not None:
            d["data_admissao"] = _parse_to_date(d["data_admissao"])
    elif dataset == "pagamentos":
        for f in ("pagamento_id", "pedido_id"):
            if d.get(f) is not None:
                d[f] = _int_val(d[f])
        if d.get("valor_pagamento") is not None:
            d["valor_pagamento"] = _br_float(d["valor_pagamento"])
    elif dataset == "clientes":
        if d.get("cliente_id") is not None:
            d["cliente_id"] = _int_val(d["cliente_id"])
        if isinstance(d.get("tipo_cliente"), str):
            d["tipo_cliente"] = d["tipo_cliente"].strip()
        for f in ("data_cadastro", "data_nascimento"):
            if d.get(f) is not None:
                d[f] = _parse_to_date(d[f])
    elif dataset == "lojas":
        if d.get("loja_id") is not None:
            d["loja_id"] = _int_val(d["loja_id"])
    elif dataset == "categorias_produto":
        if d.get("categoria_id") is not None:
            d["categoria_id"] = _int_val(d["categoria_id"])

    return d


def validate_payload(dataset: str, payload: Dict[str, Any]) -> Tuple[Any, List[str]]:
    """Returns (model_instance, []) on success or (None, error_messages)."""
    if dataset not in MODEL_BY_DATASET:
        return None, [f"Unsupported entity_name: {dataset}"]
    model_cls = MODEL_BY_DATASET[dataset]
    normalized = normalize_staged_payload(dataset, payload)
    if dataset == "clientes":
        tc_errs = _cliente_tipo_cliente_errors(normalized.get("tipo_cliente"))
        if tc_errs:
            return None, tc_errs
        if isinstance(normalized.get("tipo_cliente"), str):
            normalized["tipo_cliente"] = normalized["tipo_cliente"].strip().upper()
    try:
        inst = model_cls.model_validate(normalized)
        return inst, []
    except ValidationError as e:
        msgs = [f"{err.get('loc', ())}: {err.get('msg', '')}" for err in e.errors()]
        return None, msgs


def promote_staged_record(engine: Engine, record_id: int) -> Dict[str, Any]:
    """
    Load staging row, normalize + validate (same Pydantic models as ETL), INSERT, delete staging row.
    """
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT id, entity_name, run_id, payload FROM staging.common_records WHERE id = :id"
            ),
            {"id": record_id},
        ).mappings().first()
        if not row:
            raise LookupError("Staged record not found.")

        dataset = (row["entity_name"] or "").strip()
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object.")

        inst, errs = validate_payload(dataset, payload)
        if errs:
            raise StagedValidationError(errs)
        assert inst is not None

        if dataset not in TABLE_PRIMARY_KEY:
            raise ValueError(f"No primary key mapping for table {dataset}.")
        pk = TABLE_PRIMARY_KEY[dataset]

        dump = inst.model_dump(exclude_none=True, mode="python")
        if pk in dump and dump[pk] is None:
            dump.pop(pk, None)

        cols = list(dump.keys())
        if not cols:
            raise ValueError("Nothing to insert after validation.")

        placeholders = ", ".join(f":{c}" for c in cols)
        col_sql = ", ".join(cols)
        insert_sql = text(
            f"INSERT INTO {dataset} ({col_sql}) VALUES ({placeholders}) RETURNING {pk}"
        )
        try:
            out = conn.execute(insert_sql, dump).mappings().first()
        except IntegrityError as e:
            raise PromoteConflictError(str(e.orig)) from e
        except DataError as e:
            raise ValueError(f"Database rejected insert: {e.orig}") from e

        conn.execute(
            text("DELETE FROM staging.common_records WHERE id = :id"),
            {"id": record_id},
        )

        wid = out[pk] if out else None
        return {
            "status": "promoted",
            "staging_id": record_id,
            "entity_name": dataset,
            "warehouse_table": dataset,
            "warehouse_id": wid,
            "run_id": row["run_id"],
        }

