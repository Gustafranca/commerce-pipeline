-- Schema for staging manual data ingestion
CREATE SCHEMA IF NOT EXISTS staging;

-- Table to store raw JSON payloads from manual ingestion
CREATE TABLE IF NOT EXISTS staging.common_records (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    run_id VARCHAR(255) NOT NULL,
    staged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL
);
