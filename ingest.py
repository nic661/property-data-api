import argparse
import csv

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from cleaning import clean_row
from database import SessionLocal, Base, engine
from models import Property

BATCH_SIZE = 1000

FLAG_BUNDLED_SQL = text("""
    UPDATE properties SET is_multi_property_sale = TRUE
    WHERE is_multi_property_sale = FALSE
      AND id IN (
        SELECT id FROM (
            SELECT id, count(*) OVER (
                PARTITION BY council_name, contract_date, settlement_date, purchase_price
            ) AS n
            FROM properties
        ) t
        WHERE n > 1
    )
""")

def insert_batch(db, batch):
    """Insert cleaned rows in one statement, skipping any whose sale_key already exists."""
    stmt = insert(Property).values(batch).on_conflict_do_nothing(index_elements=["sale_key"])
    db.execute(stmt)
    db.commit()


def run(csv_path, limit):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    rows_read = 0
    rejected = 0
    batch = []
    try:
        before = db.scalar(select(func.count(Property.id)))

        with open(csv_path, newline="", encoding="utf-8-sig") as f, \
             open("rejects.csv", "w", newline="", encoding="utf-8") as rf:
            reader = csv.DictReader(f)
            rejects = csv.writer(rf)
            rejects.writerow(["line", "reason", "address", "contract_date"])

            for row in reader:
                if limit and rows_read >= limit:
                    break
                rows_read += 1

                record, reason = clean_row(row)
                if record is None:
                    rejected += 1
                    rejects.writerow([reader.line_num, reason, row.get("address"), row.get("contract_date")])
                    continue

                batch.append(record)
                if len(batch) >= BATCH_SIZE:
                    insert_batch(db, batch)
                    batch = []
                    print(f"  read {rows_read:,} rows...")

            if batch:
                insert_batch(db, batch)
        
        print("Flagging bundled sales...")
        db.execute(FLAG_BUNDLED_SQL)
        db.commit()

        after = db.scalar(select(func.count(Property.id)))
        inserted = after - before
        duplicates = rows_read - rejected - inserted
        print(f"Rows read:          {rows_read:,}")
        print(f"Rejected:           {rejected:,}  (see rejects.csv)")
        print(f"Duplicates skipped: {duplicates:,}")
        print(f"Inserted:           {inserted:,}")
        print(f"Total in table:     {after:,}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NSW sales CSV into Postgres")
    parser.add_argument("csv_path", nargs="?", default="nsw_property_data.csv")
    parser.add_argument("--limit", type=int, help="only process the first N rows")
    args = parser.parse_args()
    run(args.csv_path, args.limit)