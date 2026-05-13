import os
import json
import hmac
import hashlib
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any, List, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from commerce_models import MODEL_BY_DATASET
from staged_promote import (
    PromoteConflictError,
    StagedValidationError,
    promote_staged_record as promote_staged_to_warehouse,
    validate_payload,
)

app = FastAPI(title="Commerce Data Ingestion API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://etl_user:etl_password@localhost:5432/etl_warehouse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

http_basic = HTTPBasic(auto_error=False)


def _digest(s: str) -> bytes:
    return hashlib.sha256(s.encode("utf-8")).digest()


def _credentials_ok(given: str, expected: str) -> bool:
    return hmac.compare_digest(_digest(given), _digest(expected))


def verify_dashboard_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(http_basic),
) -> str:
    expected_user = os.getenv("DASHBOARD_USER")
    expected_password = os.getenv("DASHBOARD_PASSWORD")
    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=503,
            detail="Dashboard access is not configured (set DASHBOARD_USER and DASHBOARD_PASSWORD).",
        )
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not (
        _credentials_ok(credentials.username, expected_user)
        and _credentials_ok(credentials.password, expected_password)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def _json_value(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


def _mapping_to_dict(row: Any) -> Dict[str, Any]:
    d = dict(row)
    return {k: _json_value(v) for k, v in d.items()}


# Read-only table browse: API key -> (SQL table identifier, ORDER BY column).
# Identifiers are fixed literals only; user input never concatenated into SQL.
BROWSE_TABLES: Dict[str, Tuple[str, str]] = {
    "categorias_produto": ("categorias_produto", "categoria_id"),
    "clientes": ("clientes", "cliente_id"),
    "lojas": ("lojas", "loja_id"),
    "produtos": ("produtos", "produto_id"),
    "vendedores": ("vendedores", "vendedor_id"),
    "pedidos": ("pedidos", "pedido_id"),
    "entregas": ("entregas", "entrega_id"),
    "itens_pedido": ("itens_pedido", "item_pedido_id"),
    "estoque_movimentacoes": ("estoque_movimentacoes", "movimento_id"),
    "pagamentos": ("pagamentos", "pagamento_id"),
}


@app.get("/api/browse/{entity}")
def browse_table(
    entity: str,
    _username: str = Depends(verify_dashboard_user),
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    key = entity.strip()
    if key not in BROWSE_TABLES:
        raise HTTPException(status_code=404, detail="Unknown or unsupported entity.")
    table, order_col = BROWSE_TABLES[key]
    lim = min(max(limit, 1), 500)
    off = min(max(offset, 0), 50_000)
    stmt = text(
        f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT :lim OFFSET :off"
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"lim": lim, "off": off}).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "entity": key,
        "rows": [_mapping_to_dict(r) for r in rows],
        "limit": lim,
        "offset": off,
        "count": len(rows),
    }


@app.delete("/api/browse/{entity}/{row_id}")
def browse_delete_row(
    entity: str,
    row_id: int,
    _username: str = Depends(verify_dashboard_user),
) -> Dict[str, Any]:
    """Delete one warehouse row by primary key (same tables as GET /api/browse)."""
    key = entity.strip()
    if key not in BROWSE_TABLES:
        raise HTTPException(status_code=404, detail="Unknown or unsupported entity.")
    table, pk_col = BROWSE_TABLES[key]
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(f"DELETE FROM {table} WHERE {pk_col} = :id RETURNING {pk_col}"),
                {"id": row_id},
            ).mappings().first()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete: other rows still reference this record. " + str(e.orig),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Row not found.")
    return {"status": "deleted", "entity": key, "id": row[pk_col], "primary_key": pk_col}


@app.get("/api/explorer/order")
def explorer_order(
    _username: str = Depends(verify_dashboard_user),
    pedido_id: Optional[int] = None,
    pedido_codigo: Optional[str] = None,
) -> Dict[str, Any]:
    if (pedido_id is None) == (pedido_codigo is None or pedido_codigo.strip() == ""):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of: pedido_id or pedido_codigo.",
        )
    try:
        with engine.connect() as conn:
            if pedido_id is not None:
                ped = conn.execute(
                    text("SELECT * FROM pedidos WHERE pedido_id = :pid"),
                    {"pid": pedido_id},
                ).mappings().first()
            else:
                ped = conn.execute(
                    text("SELECT * FROM pedidos WHERE pedido_codigo = :cod LIMIT 1"),
                    {"cod": pedido_codigo.strip()},
                ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not ped:
        raise HTTPException(status_code=404, detail="Order not found.")

    p = dict(ped)
    pid = p["pedido_id"]
    cid = p["cliente_id"]
    lid = p["loja_id"]
    vid = p["vendedor_id"]

    try:
        with engine.connect() as conn:
            cliente = conn.execute(
                text("SELECT * FROM clientes WHERE cliente_id = :cid"),
                {"cid": cid},
            ).mappings().first()
            loja = conn.execute(
                text("SELECT * FROM lojas WHERE loja_id = :lid"),
                {"lid": lid},
            ).mappings().first()
            vendedor = conn.execute(
                text("SELECT * FROM vendedores WHERE vendedor_id = :vid"),
                {"vid": vid},
            ).mappings().first()
            itens = conn.execute(
                text(
                    """
                    SELECT ip.*, pr.nome_produto
                    FROM itens_pedido ip
                    JOIN produtos pr ON pr.produto_id = ip.produto_id
                    WHERE ip.pedido_id = :pid
                    ORDER BY ip.sequencia_item
                    """
                ),
                {"pid": pid},
            ).mappings().all()
            pagamentos = conn.execute(
                text("SELECT * FROM pagamentos WHERE pedido_id = :pid ORDER BY data_pagamento"),
                {"pid": pid},
            ).mappings().all()
            entregas = conn.execute(
                text("SELECT * FROM entregas WHERE pedido_id = :pid ORDER BY data_postagem"),
                {"pid": pid},
            ).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "pedido": _mapping_to_dict(ped),
        "cliente": _mapping_to_dict(cliente) if cliente else None,
        "loja": _mapping_to_dict(loja) if loja else None,
        "vendedor": _mapping_to_dict(vendedor) if vendedor else None,
        "relationship": {
            "pedido.cliente_id": cid,
            "matches_cliente.cliente_id": cliente["cliente_id"] if cliente else None,
            "related": bool(cliente and cliente["cliente_id"] == cid),
        },
        "itens_pedido": [_mapping_to_dict(r) for r in itens],
        "pagamentos": [_mapping_to_dict(r) for r in pagamentos],
        "entregas": [_mapping_to_dict(r) for r in entregas],
    }


@app.get("/api/explorer/pedidos-por-cliente")
def explorer_pedidos_por_cliente(
    cliente_id: int,
    _username: str = Depends(verify_dashboard_user),
    limit: int = 100,
) -> Dict[str, Any]:
    cap = min(max(limit, 1), 500)
    try:
        with engine.connect() as conn:
            cliente = conn.execute(
                text("SELECT * FROM clientes WHERE cliente_id = :cid"),
                {"cid": cliente_id},
            ).mappings().first()
            if not cliente:
                raise HTTPException(status_code=404, detail="Customer not found.")
            pedidos = conn.execute(
                text(
                    """
                    SELECT pedido_id, pedido_codigo, data_pedido, status_pedido, canal_venda
                    FROM pedidos
                    WHERE cliente_id = :cid
                    ORDER BY data_pedido DESC NULLS LAST, pedido_id DESC
                    LIMIT :lim
                    """
                ),
                {"cid": cliente_id, "lim": cap},
            ).mappings().all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "cliente": _mapping_to_dict(cliente),
        "pedidos": [_mapping_to_dict(r) for r in pedidos],
        "count": len(pedidos),
    }


def _staged_record_row_to_dict(r: Any) -> Dict[str, Any]:
    payload = r["payload"]
    if payload is not None and not isinstance(payload, (dict, list)):
        try:
            payload = json.loads(str(payload))
        except (json.JSONDecodeError, TypeError):
            payload = str(payload)
    return {
        "id": r["id"],
        "entity_name": r["entity_name"],
        "run_id": r["run_id"],
        "staged_at": r["staged_at"].isoformat() if r["staged_at"] else None,
        "payload": payload,
    }


class EditStagedRecordBody(BaseModel):
    payload: Dict[str, Any]
    entity_name: Optional[str] = None


@app.get("/api/records")
def list_staged_records(
    _username: str = Depends(verify_dashboard_user),
    limit: int = 500,
) -> List[Dict[str, Any]]:
    cap = min(max(limit, 1), 2000)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, entity_name, run_id, staged_at, payload
                    FROM staging.common_records
                    ORDER BY id DESC
                    LIMIT :lim
                    """
                ),
                {"lim": cap},
            ).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return [_staged_record_row_to_dict(r) for r in rows]


@app.patch("/api/records/{record_id}")
def patch_staged_record(
    record_id: int,
    body: EditStagedRecordBody,
    _username: str = Depends(verify_dashboard_user),
) -> Dict[str, Any]:
    new_entity = (body.entity_name or "").strip() or None
    if new_entity is not None and new_entity not in MODEL_BY_DATASET:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown entity_name: {new_entity}. Use one of the supported datasets.",
        )
    payload_json = json.dumps(body.payload)
    try:
        with engine.begin() as conn:
            if new_entity is not None:
                row = conn.execute(
                    text(
                        """
                        UPDATE staging.common_records
                        SET payload = CAST(:payload AS jsonb), entity_name = :entity_name
                        WHERE id = :id
                        RETURNING id, entity_name, run_id, staged_at, payload
                        """
                    ),
                    {
                        "payload": payload_json,
                        "entity_name": new_entity,
                        "id": record_id,
                    },
                ).mappings().first()
            else:
                row = conn.execute(
                    text(
                        """
                        UPDATE staging.common_records
                        SET payload = CAST(:payload AS jsonb)
                        WHERE id = :id
                        RETURNING id, entity_name, run_id, staged_at, payload
                        """
                    ),
                    {"payload": payload_json, "id": record_id},
                ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not row:
        raise HTTPException(status_code=404, detail="Staged record not found.")

    return _staged_record_row_to_dict(row)


@app.delete("/api/records/{record_id}")
def delete_staged_record(
    record_id: int,
    _username: str = Depends(verify_dashboard_user),
) -> Dict[str, Any]:
    """Remove one row from staging.common_records (password re-checked via Basic auth on this request)."""
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("DELETE FROM staging.common_records WHERE id = :id RETURNING id"),
                {"id": record_id},
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Staged record not found.")
    return {"status": "deleted", "id": row["id"]}


@app.post("/api/records/{record_id}/promote")
def promote_staged_record_endpoint(
    record_id: int,
    _username: str = Depends(verify_dashboard_user),
) -> Dict[str, Any]:
    """Normalize + Pydantic validate (same models as ETL), INSERT into warehouse, remove staging row."""
    try:
        return promote_staged_to_warehouse(engine, record_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Staged record not found.")
    except StagedValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={"validation_errors": e.errors},
        )
    except PromoteConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ingest/{entity_name}")
async def ingest_data(entity_name: str, payload: Dict[str, Any]):
    run_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    key = entity_name.strip()
    if key == "clientes":
        _, errs = validate_payload(key, payload)
        if errs:
            raise HTTPException(
                status_code=422,
                detail={"validation_errors": errs},
            )

    try:
        with engine.connect() as conn:
            # Insert into staging.common_records as defined in 02_tables.sql
            query = text("""
                INSERT INTO staging.common_records (entity_name, run_id, staged_at, payload)
                VALUES (:entity, :run_id, :staged_at, :payload)
            """)
            conn.execute(query, {
                "entity": entity_name,
                "run_id": run_id,
                "staged_at": datetime.now(),
                "payload": json.dumps(payload)
            })
            conn.commit()
        
        return {"status": "success", "run_id": run_id, "entity": entity_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
