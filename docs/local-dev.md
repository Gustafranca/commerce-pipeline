# Local development (Docker Compose)

Use Compose for day-to-day work on the API, UI, and database. You do not need Minikube or Kubernetes for this loop.

## Start

From the repository root:

```bash
docker compose up --build -d
```

## URLs

| Service   | URL |
|-----------|-----|
| Frontend  | http://localhost:30030 |
| Backend   | http://localhost:8000 |
| Airflow   | http://localhost:8080 (admin / admin) |
| Postgres  | localhost:5432 |

The frontend nginx proxies `/ingest`, `/health`, `/docs`, `/openapi.json`, and `/redoc` to the backend, so opening only **http://localhost:30030** is enough for manual ingestion.

## Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f airflow-init airflow-webserver airflow-scheduler
```

Airflow writes its scheduler/web logs inside the **`airflow_logs` Docker volume** (not the `./logs` host folder). Inspect or clear it with:

```bash
docker volume ls | grep airflow_logs
# Example: copy logs out of the volume for debugging
docker compose run --rm --no-deps airflow-webserver ls -la /opt/airflow/logs
```

## Stop

```bash
docker compose down
```

To remove containers **and** named volumes (`postgres_data`, `airflow_logs`) — destructive reset:

```bash
docker compose down -v
```

## Kubernetes and GitOps

Staging and production manifests live under `k8s/`. See [k8s/README.md](../k8s/README.md) and [docs/staging-cluster-access.md](staging-cluster-access.md).
