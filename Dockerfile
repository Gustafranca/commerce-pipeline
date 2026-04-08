FROM apache/airflow:3.1.8

COPY requirements.txt .

RUN pip install -r requirements.txt