from __future__ import annotations

import base64
import importlib

from fastapi.testclient import TestClient

import main as backend_main


def _basic_auth(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def test_ingest_requires_auth(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    module = importlib.reload(backend_main)
    client = TestClient(module.app)

    res = client.post("/ingest/clientes", json={"tipo_cliente": "PF"})

    assert res.status_code == 401


def test_internal_errors_are_sanitized(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    module = importlib.reload(backend_main)

    class BrokenEngine:
        def connect(self):
            raise RuntimeError("db password leaked")

    monkeypatch.setattr(module, "engine", BrokenEngine())
    client = TestClient(module.app)

    res = client.get(
        "/api/records",
        headers={"Authorization": _basic_auth("admin", "secret")},
    )

    assert res.status_code == 500
    assert res.json() == {"detail": "Internal server error."}
