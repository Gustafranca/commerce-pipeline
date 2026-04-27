from __future__ import annotations


from datetime import datetime, timedelta
from etl.etl.transforme import clean
from etl.etl.load import (
    create_tables, list_datasets, build_mapping_payloads, 
    load, add_constraints
    )

from etl.etl.validate import validate

from airflow.decorators import dag


## DAG PARA ETL DO COMERCE
@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=3)},
    tags=["etl", "commerce", "csv", "postgres"],
)

def commerce_etl():
    init_db = create_tables()
    datasets = list_datasets()
    cleaned_paths = clean.expand(dataset=datasets)
    mapping_payloads = build_mapping_payloads(datasets, cleaned_paths)
    validated_counts = validate.expand_kwargs(mapping_payloads)

    # Garantir que as tabelas existam antes do load
    loaded = load.expand_kwargs(mapping_payloads)

    init_db >> cleaned_paths
    validated_counts >> loaded
    loaded >> add_constraints()


commerce_etl_dag = commerce_etl()

if __name__ == "__main__":
    commerce_etl_dag.test()