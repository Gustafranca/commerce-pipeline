import os
import pandas as pd
from typing import List, Dict, Tuple
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
    return validate_dataframe(dataset=dataset, dataframe=df)[0]


def validate_dataframe(dataset: str, dataframe: pd.DataFrame) -> Tuple[int, List[Dict[str, str]]]:
    model = MODEL_BY_DATASET[dataset]
    errors: List[Dict[str, str]] = []

    for idx, row in dataframe.iterrows():
        try:
            row_dict = row.to_dict()
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            model(**row_dict)
        except ValidationError as e:
            errors.append({"row": str(idx), "errors": str(e)})

    if errors:
        error_df = pd.DataFrame(errors)
        error_df.to_csv(_log_path(dataset, "validation_errors"), index=False, sep=";")
        raise ValueError(f"Validation failed for dataset '{dataset}': {len(errors)} invalid rows.")
    return 0, errors
