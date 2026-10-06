from datetime import date
from models import Property

def create_property(db_session, **kwargs):
    """Helper factory: creates a valid Property with sensible defaults for tests."""
    # Use a unique sale_key per instance to respect the unique constraint
    count = db_session.query(Property).count()
    defaults = {
        "address": "123 TEST ST",
        "suburb": "PARRAMATTA",
        "post_code": "2150",
        "purchase_price": 750000,
        "contract_date": date(2024, 1, 15),
        "property_type": "Residence",
        "is_multi_property_sale": False,
        "sale_key": f"test_key_{count + 1}",
    }
    defaults.update(kwargs)
    prop = Property(**defaults)
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_properties_empty(client):
    response = client.get("/properties")
    assert response.status_code == 200
    assert response.json() == []


def test_list_properties_with_data(client, db_session):
    create_property(db_session, suburb="PARRAMATTA", purchase_price=800000)
    create_property(db_session, suburb="ST MARYS", purchase_price=600000)

    response = client.get("/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_filter_properties_by_suburb(client, db_session):
    create_property(db_session, suburb="PARRAMATTA")
    create_property(db_session, suburb="ST MARYS")

    response = client.get("/properties?suburb=PARRAMATTA")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["suburb"] == "PARRAMATTA"


def test_get_property_by_id_found(client, db_session):
    prop = create_property(db_session, address="45 HUNTER ST", suburb="PARRAMATTA")

    response = client.get(f"/properties/{prop.id}")
    assert response.status_code == 200
    assert response.json()["address"] == "45 HUNTER ST"
    assert response.json()["id"] == prop.id


def test_get_property_by_id_not_found(client):
    response = client.get("/properties/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "not found"


def test_suburb_stats(client, db_session):
    create_property(db_session, suburb="PARRAMATTA", purchase_price=500000)
    create_property(db_session, suburb="PARRAMATTA", purchase_price=1000000)

    response = client.get("/stats/suburbs?suburb=PARRAMATTA")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["suburb"] == "PARRAMATTA"
    assert data[0]["count"] == 2
    assert data[0]["avg_price"] == 750000.0
    assert data[0]["min_price"] == 500000
    assert data[0]["max_price"] == 1000000


def test_price_trends(client, db_session):
    create_property(
        db_session,
        suburb="ST MARYS",
        contract_date=date(2023, 5, 10),
        purchase_price=600000,
    )
    create_property(
        db_session,
        suburb="ST MARYS",
        contract_date=date(2023, 5, 20),
        purchase_price=800000,
    )

    response = client.get("/properties/trend?suburb=ST MARYS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["year_month"] == "2023-05"
    assert data[0]["avg_price"] == 700000.0
    assert data[0]["count"] == 2