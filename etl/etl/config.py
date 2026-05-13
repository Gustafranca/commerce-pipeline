import os
from airflow.models import Variable

RAW_DIR = Variable.get("COMMERCE_RAW_DIR", "/opt/airflow/data/raw")
INTERIM_DIR = Variable.get("COMMERCE_INTERIM_DIR", "/opt/airflow/data/interim")
LOGS_DIR = Variable.get("COMMERCE_LOGS_DIR", "/opt/airflow/data/logs")
POSTGRES_CONN_ID = Variable.get("COMMERCE_PG_CONN_ID", "etl_warehouse")
PG_HOST = Variable.get("COMMERCE_PG_HOST", "postgres")
PG_PORT = int(Variable.get("COMMERCE_PG_PORT", "5432"))
PG_DBNAME = Variable.get("COMMERCE_PG_DBNAME", "etl_warehouse")
PG_USER = Variable.get("COMMERCE_PG_USER", "etl_user")
PG_PASSWORD = Variable.get("COMMERCE_PG_PASSWORD", "etl_password")
SQL_INIT_DB = Variable.get("COMMERCE_SQL_INIT_DB", "/opt/airflow/sql/01_init_db.sql")
SQL_STAGING_TABLES = Variable.get("COMMERCE_SQL_STAGING_TABLES", "/opt/airflow/sql/02_tables.sql")
SQL_CONSTRAINTS = Variable.get("COMMERCE_SQL_CONSTRAINTS", "/opt/airflow/sql/post_load/02_constraints.sql")
