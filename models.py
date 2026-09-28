# python class -> table

from sqlalchemy import Column, Integer, String, Numeric, Date
from database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    suburb = Column(String, nullable=False, index=True)
    postcode = Column(String(4), nullable=False)
    price = Column(Numeric(12, 2))
    bedrooms = Column(Integer)
    sale_date = Column(Date)