import argparse
import csv

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from cleaning import clean_row
from database import SessionLocal
from models import Property

BATCH_SIZE = 1000


def insert_batch(db, batch):
    """Insert cleaned rows, silently skipping any whose sale_key already exists."""
    stmt = insert(Property).on_conflict_do_nothing(index_elements=["sale_key"])
    db.execute(stmt, batch)
    db.commit()


def run(csv_path, limit):
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
            rejects.writerow(["line", "reason", "address"])

            for row in reader:
                if limit and rows_read >= limit:
                    break
                rows_read += 1

                record, reason = clean_row(row)
                if record is None:
                    rejected += 1
                    rejects.writerow([reader.line_num, reason, row.get("address")])
                    continue

                batch.append(record)
                if len(batch) >= BATCH_SIZE:
                    insert_batch(db, batch)
                    batch = []
                    print(f"  read {rows_read:,} rows...")

            if batch:
                insert_batch(db, batch)

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