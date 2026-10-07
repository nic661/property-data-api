from datetime import date
from pydantic import BaseModel, ConfigDict


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int | None = None
    council_name: str | None = None
    address: str
    suburb: str
    post_code: str | None = None
    purchase_price: int
    contract_date: date
    settlement_date: date | None = None
    property_type: str | None = None
    nature_of_property: str | None = None
    primary_purpose: str | None = None
    zoning: str | None = None
    strata_lot_number: str | None = None
    area_sqm: float | None = None
    is_multi_property_sale: bool

class SuburbStatsOut(BaseModel):
    suburb: str
    count: int
    avg_price: float | None = None
    median_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None

class PriceTrendOut(BaseModel):
    year_month: str
    avg_price: float
    median_price: float
    count: int