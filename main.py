from fastapi import FastAPI, Depends, Query, HTTPException
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
    property_type: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Property)

    if suburb:
        query = query.filter(models.Property.suburb.ilike(suburb))
    if property_type:
        query = query.filter(models.Property.property_type.ilike(property_type))
    if min_price is not None:
        query = query.filter(models.Property.purchase_price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.purchase_price <= max_price)

    return (
        query
        .order_by(models.Property.contract_date.desc(), models.Property.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

@app.get("/stats/suburbs", response_model=list[SuburbStatsOut])
def suburb_stats(
    suburb: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(
        models.Property.suburb,
        func.count(models.Property.id).label("count"),
        func.round(func.avg(models.Property.purchase_price), 2).label("avg_price"),
        func.min(models.Property.purchase_price).label("min_price"),
        func.max(models.Property.purchase_price).label("max_price"),
    )

    if suburb:
        query = query.filter(models.Property.suburb.ilike(suburb))

    results = (
        query
        .group_by(models.Property.suburb)
        .order_by(func.count(models.Property.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "suburb": row[0],
            "count": row[1],
            "avg_price": float(row[2]) if row[2] else None,
            "min_price": row[3],
            "max_price": row[4],
        }
        for row in results
    ]

@app.get("/properties/trend", response_model=list[PriceTrendOut])
def price_trends(
    suburb: str | None = None,
    db: Session = Depends(get_db),
):
    year_col = extract("year", models.Property.contract_date)
    month_col = extract("month", models.Property.contract_date)

    query = db.query(
        year_col,
        month_col,
        func.round(func.avg(models.Property.purchase_price), 2).label("avg_price"),
        func.count(models.Property.id).label("count"),
    )

    if suburb:
        query = query.filter(models.Property.suburb.ilike(suburb))

    results = (
        query
        .group_by(year_col, month_col)
        .order_by(year_col, month_col)
        .all()
    )

    return [
        {
            "year_month": f"{int(row[0])}-{int(row[1]):02d}",
            "avg_price": float(row[2]) if row[2] else 0.0,
            "count": row[3],
        }
        for row in results
    ]

@app.get("/properties/{id}", response_model=PropertyOut)
def read_id(
    id: int,
    db: Session = Depends(get_db),
):  
   property = db.get(models.Property, id)
   if not property:
       raise HTTPException(status_code=404, detail="not found")
   return ( property )