import os
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, TIMESTAMP, JSON, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="Commerce Data Ingestion API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://etl_user:etl_password@localhost:5432/etl_warehouse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.post("/ingest/{entity_name}")
async def ingest_data(entity_name: str, payload: Dict[str, Any]):
    run_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    
    try:
        with engine.connect() as conn:
            # Insert into staging.common_records as defined in 02_tables.sql
            query = text("""
                INSERT INTO staging.common_records (entity_name, run_id, staged_at, payload)
                VALUES (:entity, :run_id, :staged_at, :payload)
            """)
            conn.execute(query, {
                "entity": entity_name,
                "run_id": run_id,
                "staged_at": datetime.now(),
                "payload": payload
            })
            conn.commit()
        
        return {"status": "success", "run_id": run_id, "entity": entity_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
