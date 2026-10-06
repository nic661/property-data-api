# python class -> table

from sqlalchemy import Column, Integer, String, Date, BigInteger, Text, Float, Boolean, Index
from database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(BigInteger, nullable=True)
    council_name = Column(String, nullable=True)
    address = Column(String, nullable=False)
    suburb = Column(String, nullable=False, index=True)
    post_code = Column(String(4), nullable=True)
    purchase_price = Column(BigInteger, nullable=False)
    contract_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)
    property_type = Column(String, nullable=True)
    nature_of_property = Column(String, nullable=True)
    primary_purpose = Column(String, nullable=True)
    zoning = Column(String, nullable=True)
    strata_lot_number = Column(String, nullable=True)
    property_name = Column(String, nullable=True)
    legal_description = Column(Text, nullable=True)
    area_raw = Column(Float, nullable=True)
    area_type = Column(String(1), nullable=True)
    area_sqm = Column(Float, nullable=True)
    is_multi_property_sale = Column(Boolean, nullable=False, default=False)
    download_date = Column(Date, nullable=True)
    sale_key = Column(String(32), nullable=False, unique=True)

    __table_args__ = (
        Index("ix_properties_suburb_contract_date", "suburb", "contract_date"),
    )