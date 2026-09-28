from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from schemas import PropertyOut

Base.metadata.create_all(engine)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/properties", response_model=list[PropertyOut])
def list_properties(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Property)
        .order_by(models.Property.id)
        .offset(offset)
        .limit(limit)
        .all()
    )