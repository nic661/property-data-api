from datetime import date
from pydantic import BaseModel, ConfigDict


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    suburb: str
    postcode: str
    price: float | None = None
    bedrooms: int | None = None
    sale_date: date | None = None