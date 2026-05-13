FROM apache/airflow:2.10.0-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

ARG AIRFLOW_VERSION=2.10.0
ARG PYTHON_VERSION=3.11
ENV AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --constraint "${AIRFLOW_CONSTRAINTS_URL}" -r /requirements.txt

COPY ./dags /opt/airflow/dags
COPY ./etl /opt/airflow/etl
COPY ./sql /opt/airflow/sql