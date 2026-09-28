import csv
from datetime import date
from decimal import Decimal

from database import SessionLocal, engine, Base
from models import Property

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        if db.query(Property).count() > 0:
            print("Table already has data, skipping seed.")
            return

        properties = []
        with open("sample_properties.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                properties.append(
                    Property(
                        address=row["address"],
                        suburb=row["suburb"],
                        postcode=row["postcode"],
                        price=Decimal(row["price"]) if row["price"] else None,
                        bedrooms=int(row["bedrooms"]) if row["bedrooms"] else None,
                        sale_date=date.fromisoformat(row["sale_date"]),
                    )
                )

        db.add_all(properties)
        db.commit()
        print(f"Inserted {len(properties)} properties.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()