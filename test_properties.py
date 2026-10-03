from datetime import date
from models import Property

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    

def test_list_properties_empty(client):
    response = client.get("/properties")
    assert response.status_code == 200
    assert response.json() == []

def test_list_properties_with_basic_data(client, db_session):
    from models import Property
    # no id required, primary key auto generates to True
    db_session.add(Property(
        address="road",
        suburb="suburb",
        postcode="1234",
        price=1000.10,
        bedrooms=1,
        sale_date=date(2026, 10, 3)
    ))
    db_session.commit()

    response = client.get("/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["suburb"] == "suburb"

def test_get_properties_by_id_not_found(client):
    response = client.get("/properties/9999")
    assert response.status_code == 404

def test_get_property_by_id_found(client, db_session):
    new_property = Property(
        address="road",
        suburb="suburb",
        postcode="1234",
        price=1000.11,
        bedrooms=2,
        sale_date=date(2026, 1, 1),
    )
    db_session.add(new_property)
    db_session.commit()
    db_session.refresh(new_property)

    response = client.get(f"/properties/{new_property.id}")
    assert response.status_code == 200
    assert response.json()["suburb"] == "suburb"