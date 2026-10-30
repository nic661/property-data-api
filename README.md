# NSW Property Sales Analytics API

A FastAPI + PostgreSQL API serving 4.6M cleaned, deduplicated NSW property sales (1990 to 2024), with suburb stats and monthly trends that exclude bundled sales and report medians.

**Docs:** http://localhost:8000/docs (when running locally) · **Repo:** https://github.com/nic661/property-data-api

![Swagger UI](docs/swagger.png)

## Data

Sales records from the [NSW Valuer General](https://valuation.property.nsw.gov.au/embed/propertySalesInformation), via the Kaggle dataset [NSW Australia Property Data](https://www.kaggle.com/datasets/josephcheng123456/nsw-australia-property-data) by Joseph Cheng ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). I cleaned and deduplicated it.

4,854,814 source rows became **4,623,974 stored sales**: 17,892 rejected (0.37%: price of 0 or blank, contract date before 1990, no usable suburb) and 212,948 collapsed as republished duplicates. Another 348,467 stored rows belong to bundled sales (one contract, price repeated on every lot). They are flagged, kept, and excluded from statistics.

## Architecture

                  NSW PROPERTY SALES DATA
                       4.85M rows
                           |
                           v
              +-------------------------+
              |   PYTHON INGESTION      |
              |-------------------------|
              |  CSV batch processing   |
              |  Data validation        |
              |  Cleaning & deduplication|
              |  Bundled sale detection |
              +-------------------------+
                    |           |
             Valid records   Rejected rows
                    |           |
                    v           v
          +----------------+  rejects.csv
          |   POSTGRESQL   |
          |----------------|
          |  4.62M sales   |
          |  Indexed data  |
          +----------------+
                    |
                    v
              +-------------------------+
              |       FASTAPI           |
              |-------------------------|
              |  Property search        |
              |  Property details       |
              |  Suburb statistics      |
              |  Monthly price trends   |
              |  Health check           |
              +-------------------------+
                    |
                    v
          +--------------------------+
          |       API ACCESS         |
          |--------------------------|
          |  Swagger UI (/docs)      |
          |  REST API clients        |
          +--------------------------+

## Endpoints

| Endpoint | Notes |
|---|---|
| `GET /properties` | Newest first. Filters: `suburb`, `property_type` (house/unit), `min_price`, `max_price`; `limit`, `offset` |
| `GET /properties/{id}` | 404 if missing |
| `GET /stats/suburbs` | Count, average, median, min, max per suburb. Params: `suburb`, `residential_only` (default true), `min_price` (default 10000), `limit` |
| `GET /properties/trend` | Monthly average, median, count. Params: `suburb`, `residential_only`, `min_price` |
| `GET /health` | Liveness check |

## Data decisions

- **Unique Sale key.** With no sale ID, `property_id` being inconsistent: sometimes identifies a property, sometimes blank, and duplicated. The unique key is an MD5 fingerprint of address + contract date + price + legal description. With legal description being a key differentiator, because different lots sold together share an address and price: in a 5,000-row sample, adding it cut collisions from 70 to 57.
- **Contract date, not settlement date.** Settlement can lag by years.
- **Bundled sales** are flagged where council, contract date, settlement date and price all match (142,230 groups). The cost is occasional false positives.
- **Residential only, $10,000 price floor** Sales under $10k are mostly transfers and partial interests (0.15% of residential rows) and were omitted.
- **Reject instead of repairing columns** During injesting, bad rows go to `rejects.csv` with a text reason. No repairing was done as it would assume data.

## Performance

Local Docker, 4.6M rows, warm cache, end to end:

| Call | Time |
|---|---|
| Stats for one suburb | ~0.27 s |
| Trend, all suburbs | ~2.3 s |
| Stats, all suburbs | ~6 s |

- **Ingest:** profiling showed about 99% of the time was database round trips. One multi-row `INSERT` per batch cut 5,000 rows from 36.8 s to 2.8 s.
- **All-suburb stats are slow because the median needs sorting:** about 6.5 s with it and 0.8 s without, inside the query.

## Trade-offs

- **Python ingestion over `COPY`:** keeps validation and the reject log.
- **Live aggregation over a materialized view:** simpler and always current, but the all-suburb median is slow.
- **Exact-match suburb over `ILIKE`:** `ILIKE` can't use the B-tree index, so there are no partial matches.
- **Hash key and bundling heuristic:** both can occasionally merge or flag distinct sales.
- **No migrations:** `create_all` never alters an existing table.

## Getting started

```bash
git clone https://github.com/nic661/property-data-api.git
cd property-data-api
docker compose up -d --build
python -m venv venv && venv\Scripts\activate    # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (local development credentials only):

```env
DATABASE_URL=postgresql://postgres:devpass@localhost:5432/postgres
```

```bash
python ingest.py sample_properties.csv      # 50 real rows
python ingest.py nsw_property_data.csv      # full Kaggle file, ~4.85M rows, long run
```

Ingestion is safe to stop and re-run; `--limit N` loads only the first N rows, and `rejects.csv` is overwritten each run.

## Tests

43 tests cover the cleaning rules, the API, and the statistics exclusions, against an isolated test database:

```bash
docker compose up -d db
docker compose exec db psql -U postgres -c "CREATE DATABASE test_db;"
pytest -v
```

## Limitations

- `property_type` has nuance, some early records use numeric council codes, recent months are incomplete (January 2024 has 16 sales against roughly 60 typical), and all-time stats mix 34 years of prices.
- No authentication, logging or deployment yet.