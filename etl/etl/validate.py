import os
import pandas as pd
from typing import List
from pydantic import ValidationError
from airflow.decorators import task
from etl.etl.config import LOGS_DIR
from etl.etl.commerce_models import MODEL_BY_DATASET


def _log_path(dataset: str, suffix: str) -> str:
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"{dataset}_{suffix}.csv")


@task
def validate(dataset: str, cleaned_path: str) -> int:
    df = pd.read_csv(cleaned_path, sep=";")
    model = MODEL_BY_DATASET[dataset]
    errors = []

    for idx, row in df.iterrows():
        try:
            row_dict = row.to_dict()
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            model(**row_dict)
        except ValidationError as e:
            errors.append({"row": idx, "errors": str(e)})

    if errors:
        error_df = pd.DataFrame(errors)
        error_df.to_csv(_log_path(dataset, "validation_errors"), index=False, sep=";")

    return len(errors)
