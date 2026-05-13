# Pipeline Commerce ETL 🛒📦

A robust and scalable data engineering pipeline designed to ingest, transform, validate, and load e-commerce datasets into a PostgreSQL data warehouse using **Apache Airflow**.

## 🚀 Overview

This project implements a complete ETL (Extract, Transform, Load) workflow for a commerce system. It handles data from multiple sources (CSV files), applies business transformations, validates data integrity using **Pydantic**, and manages a PostgreSQL database with complex relational constraints.

### Key Features
- **Orchestration:** Apache Airflow with TaskFlow API for efficient DAG management.
- **Data Quality:** Strict schema validation with Pydantic models before database insertion.
- **Parallel Processing:** Dynamic task mapping to process multiple datasets simultaneously.
- **Idempotency:** Re-runnable tasks using a `Truncate and Reload` strategy.
- **Infrastructure:** Fully containerized environment with Docker Compose.
- **Observability:** Persistent logs for task execution and data quality monitoring.

---

## 🏗️ Architecture

1.  **Extract:** Reads raw CSV data from the `data/raw` directory.
2.  **Transform:** Standardizes dates, formats currency values, and handles null values using Pandas.
3.  **Validate:** Ensures every row matches the expected business schema using Pydantic.
4.  **Load:** Uses PostgreSQL `COPY` for high-performance data ingestion.
5.  **Constraints:** Applies Foreign Keys and relationships **after** data loading to optimize performance and prevent race conditions.

---

## 🛠️ Technologies

- **Language:** Python 3.11
- **Orchestration:** Apache Airflow 2.10.0
- **Data Processing:** Pandas
- **Validation:** Pydantic v2
- **Database:** PostgreSQL 16
- **Containerization:** Docker & Docker Compose

---

## 📂 Project Structure

```text
├── etl/
│   ├── dags/                # Airflow DAG definitions
│   ├── etl/                 # Core logic (Transform, Validate, Load)
│   ├── sql/                 # Database initialization and constraints
│   ├── tests/               # Unit and integration tests
│   └── Dockerfile           # Custom Airflow image
├── data/
│   ├── raw/                 # Source CSV files
│   ├── interim/             # Processed data ready for load
│   └── logs/                # Data quality and validation logs
├── backend/                 # API service
├── frontend/                # Web interface
└── docker-compose.yml       # System orchestration
```

---

## 🚦 Getting Started

### Prerequisites
- Docker and Docker Compose installed.

### Local development (recommended)

Use Docker Compose for UI/API/database iteration. See [docs/local-dev.md](docs/local-dev.md).

### Kubernetes / GitOps

- Kustomize layouts: [k8s/README.md](k8s/README.md)
- Cluster access notes (Minikube, tunnels, DNS): [docs/staging-cluster-access.md](docs/staging-cluster-access.md)
- Argo CD examples: [gitops/argocd/README.md](gitops/argocd/README.md)
- CI image build: [.github/workflows/build-push.yaml](.github/workflows/build-push.yaml) (requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets)

### Setup and Execution
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pipeline-commerce.git
    cd pipeline-commerce
    ```

2.  **Place your raw data:**
    Ensure your CSV files are located in `./data/raw/`.

3.  **Start the environment:**
    ```bash
    docker compose up --build -d
    ```

4.  **Access Airflow:**
    - URL: `http://localhost:8080`
    - Login: `admin` / `admin`

5.  **Access the ingestion UI:**
    - URL: `http://localhost:30030` (frontend; API paths are proxied to the backend)

6.  **Trigger the DAG:**
    Locate the `commerce_etl` DAG and trigger it manually.

---

## 📊 Monitoring and Logs

- **Task Logs:** Accessible via the Airflow UI or `docker compose logs airflow-webserver` (filesystem logs live in the Compose named volume `airflow_logs`, not `./logs`).
- **Data Quality Logs:** Check `./data/logs/` for CSV files containing specific rows that failed validation or contained null values.

---

## 🛡️ Security and Reliability

- **Volume Protection:** Source code volumes are mounted as `read-only` in Docker to prevent accidental modifications during container runtime.
- **Atomic Operations:** Uses database transactions and `CASCADE` truncates to ensure the database remains in a consistent state even if a task fails.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
