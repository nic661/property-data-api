from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import ilike_op
from sqlalchemy import func, extract
from database import Base, engine, get_db
import models
from schemas import PropertyOut, SuburbStatsOut, PriceTrendOut

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

@app.get("/stats/suburbs", response_model=list[SuburbStatsOut])
def suburb_stats(
    db: Session = Depends(get_db),
):  
   results = (
       db.query(
            models.Property.suburb,
            func.count(models.Property.id),
            func.round(func.avg(models.Property.price), 2),
            func.min(models.Property.price),
            func.max(models.Property.price)
        ).group_by(models.Property.suburb).all()
   )
   return [
        {"suburb": row[0], "count": row[1], "avg_price": row[2], "min_price": row[3], "max_price": row[4]}
        for row in results
    ]

@app.get("/properties/trend", response_model=list[PriceTrendOut])
def properties_id(
    db: Session = Depends(get_db),
):  
   results = db.query(
       extract('year', models.Property.sale_date), 
       extract('month', models.Property.sale_date),
       func.round(func.avg(models.Property.price), 2),
       func.count(models.Property.id)
    ).group_by(
        extract('year', models.Property.sale_date), 
        extract('month', models.Property.sale_date)
    ).order_by(
        extract('year', models.Property.sale_date), 
        extract('month', models.Property.sale_date)
    ).all()
   return [
       {"year_month": "-".join([str(row[0]), str(row[1])]), "avg_price": row[2], "count": row[3]}
       for row in results
   ]