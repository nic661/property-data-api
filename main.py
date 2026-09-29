from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import ilike_op

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
    suburb: str | None = None,
    bedrooms: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    db: Session = Depends(get_db),
):  
    query = db.query(models.Property)
    if suburb:
        query = query.filter(models.Property.suburb.ilike(suburb))
    if bedrooms is not None:
        query = query.filter(models.Property.bedrooms == bedrooms)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    return (
        query
        .order_by(models.Property.id)
        .offset(offset)
        .limit(limit)
        .all()
    )