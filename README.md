# Pipeline Commerce

E-commerce data platform: batch ETL into a PostgreSQL warehouse, a REST API for ingestion and curation, and a dashboard for operators. This document describes the **technologies implemented** in the repository.

---

## Stack at a glance

| Layer | Technologies |
|-------|----------------|
| **Languages** | Python 3.11, TypeScript 5.6 |
| **Data warehouse** | PostgreSQL 16 |
| **ETL orchestration** | Apache Airflow 2.10 (TaskFlow API, LocalExecutor) |
| **API** | FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2 |
| **Dashboard** | React 18, Vite 5, Tailwind CSS 3, Radix UI |
| **Containers** | Docker, Docker Compose, multi-stage image builds |
| **Kubernetes** | Kustomize, Helm, NGINX Ingress Controller |
| **Delivery** | GitHub Actions, Argo CD, Docker Hub |

---

## Data layer

### PostgreSQL 16

- Single warehouse database (`etl_warehouse`) with staging and production schemas.
- DDL and constraints live under `etl/sql/` and are applied on first container start (Compose) or via ConfigMap/init jobs (Kubernetes).
- Foreign keys are applied **after** bulk load to keep ingest fast and avoid ordering races.
- Bulk load uses PostgreSQL **`COPY`** via `psycopg2`.

### Shared validation models (Pydantic v2)

- Entity schemas are defined once in `etl/etl/commerce_models.py`.
- The same models drive ETL validation, API ingest (`POST /ingest/{entity}`), and staged-row promote flows.
- The backend image copies this module at build time so API and pipeline stay aligned.

---

## ETL pipeline

### Apache Airflow 2.10

- Custom image based on `apache/airflow:2.10.0-python3.11`.
- **TaskFlow API** (`@dag`, `@task`) with **dynamic task mapping** (`.expand` / `.expand_kwargs`) to process many datasets in parallel.
- **LocalExecutor** in Docker Compose; Helm values under `k8s/helm/` for cluster deployments.
- DAG `commerce_etl`: extract CSV → transform → validate → load → add constraints.

### Python data tooling

| Package | Role |
|---------|------|
| **Pandas** | CSV read, cleaning, type coercion, null handling |
| **Pydantic v2** | Row-level schema validation before load |
| **psycopg2** | Direct Postgres connections and `COPY` in load tasks |
| **SQLAlchemy** (&lt;2.0 in ETL image) | Available in the ETL environment per `etl/requirements.txt` |

### Testing

- **pytest** for ETL validation tests (`etl/tests/`).

---

## Backend API

### FastAPI + Uvicorn

- ASGI app in `backend/main.py`, served on port **8000**.
- OpenAPI docs at `/docs` and `/redoc`.

### Core libraries

| Package | Version (pinned) | Use |
|---------|------------------|-----|
| **FastAPI** | 0.111.0 | Routes, dependency injection, HTTP exceptions |
| **Uvicorn** | 0.30.1 | ASGI server |
| **SQLAlchemy** | 2.0.31 | Engine, sessions, raw SQL for warehouse browse/staging |
| **Pydantic** | 2.7.4 | Request/response models |
| **psycopg2-binary** | 2.9.9 | PostgreSQL driver |
| **python-dotenv** | 1.0.1 | Local configuration |
| **email-validator** | 2.1.1 | Email fields in shared models |

### Security and API behavior

- **HTTP Basic** authentication for dashboard routes (`DASHBOARD_USER` / `DASHBOARD_PASSWORD`), with constant-time password comparison.
- **CORS** restricted to configured frontend origins.
- Staging workflow: rows in `staging.common_records` — PATCH, promote, or DELETE; promote runs the same `validate_payload` rules as ingest.
- Table and column names for browse/delete use **fixed whitelists** only (no dynamic SQL identifiers from user input).

### Testing

- **pytest** + **FastAPI TestClient** (`backend/tests/`).

---

## Frontend dashboard

### React SPA (TypeScript)

| Technology | Role |
|------------|------|
| **React 18** | UI components and client state |
| **TypeScript ~5.6** | Typed sources and build-time checks |
| **Vite 5** | Dev server and production bundling |
| **React Router 6** | Client-side routes (`/`, `/staged`, `/browse`, `/explorer`) |
| **Tailwind CSS 3** | Utility-first styling (PostCSS + Autoprefixer) |
| **Radix UI** (`@radix-ui/react-dialog`) | Accessible modal dialogs |

### Production serving

- **Multi-stage Docker build**: Node 22 Alpine → compile static assets → **nginx:alpine** serves `dist/`.
- Nginx reverse-proxies `/api/`, `/ingest/`, `/health`, and OpenAPI paths to the backend service in Compose.
- Auth context stores Basic credentials for API calls; destructive actions re-prompt for password.

---

## Containers and local runtime

### Docker Compose

Services defined in `docker-compose.yml`:

| Service | Image / build | Port |
|---------|---------------|------|
| `postgres` | `postgres:16` | 5432 |
| `airflow-init` | `./etl` Dockerfile | — |
| `airflow-webserver` | `./etl` | 8080 |
| `airflow-scheduler` | `./etl` | — |
| `backend` | `backend/Dockerfile` | 8000 |
| `frontend` | `frontend/Dockerfile` | 30030 → 80 |

Named volumes: `postgres_data`, `airflow_logs`. ETL and DAG mounts are read-only where possible.

Quick start: [docs/local-dev.md](docs/local-dev.md).

---

## Kubernetes and GitOps

### Kustomize

- **Base** manifests: namespace, Postgres, backend, frontend, ingress, secrets — `k8s/base/`.
- **Overlays**: `k8s/overlays/staging` and `k8s/overlays/prod` for environment-specific image tags.

### Helm

- **Apache Airflow** chart (e.g. v1.16.0) installed separately from app manifests.
- Values files: `k8s/helm/airflow-values-staging.yaml`, `airflow-values-prod.yaml`.

### Ingress

- **NGINX Ingress Controller** (`ingressClassName: nginx`).
- Split routing: API paths → backend Service; static UI → frontend Service.

### Argo CD

- Example `Application` manifests in `gitops/argocd/` for Kustomize overlays and Helm-based Airflow.
- See [gitops/argocd/README.md](gitops/argocd/README.md).

Cluster access notes: [docs/staging-cluster-access.md](docs/staging-cluster-access.md).  
K8s layout details: [k8s/README.md](k8s/README.md).

---

## CI/CD

### GitHub Actions

Workflow [`.github/workflows/build-push.yaml`](.github/workflows/build-push.yaml):

- Triggers on push to `main` or manual `workflow_dispatch`.
- **Docker Buildx** builds and pushes three images to Docker Hub:
  - `pipeline-commerce-backend`
  - `pipeline-commerce-frontend`
  - `pipeline-commerce-etl` (Airflow)
- Tags: Git SHA (12 chars) and `latest`.
- Image tags for staging can be pinned with `scripts/set-image-tags.sh`.

---

## Repository map (by technology)

```text
pipeline-commerce/
├── etl/                    # Airflow DAGs, transform/validate/load, SQL DDL
├── backend/                # FastAPI app, staged promote, API tests
├── frontend/               # React + Vite + Tailwind SPA, nginx.conf
├── k8s/                    # Kustomize base/overlays, Helm values
├── gitops/argocd/          # Argo CD Application examples
├── .github/workflows/      # Container build and push
├── docker-compose.yml      # Local full stack
└── docs/                   # Local dev and cluster access guides
```

---

## Related documentation

| Topic | Location |
|-------|----------|
| Local development | [docs/local-dev.md](docs/local-dev.md) |
| Kubernetes manifests | [k8s/README.md](k8s/README.md) |
| Argo CD bootstrap | [gitops/argocd/README.md](gitops/argocd/README.md) |
| Staging cluster access | [docs/staging-cluster-access.md](docs/staging-cluster-access.md) |
