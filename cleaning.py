import hashlib
import math
from datetime import date, datetime

MIN_DATE = date(1990, 1, 1)
MAX_DATE = date(2026, 12, 31)

def parse_date(value):
    """Return a date for 'YYYY-MM-DD' text, or None if empty, malformed or implausible."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    if parsed_date < MIN_DATE or parsed_date > MAX_DATE:
        return None
    return parsed_date

def parse_price(value):
    """Return the price as a positive int, or None if empty, not a number, or <= 0."""
    if value is None:
        return None
    try:
        parsed_price = int(value)
    except ValueError:
        return None
    if parsed_price <= 0:
        return None
    return parsed_price

def clean_text(value):
    """Strip whitespace; return None if the result is empty."""
    if value is None:
        return None
    value = value.strip()
    return value or None

def parse_int(value):
    """Return an int, or None if empty or not a whole number."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None

def parse_area(area, area_type):
    """Return (area_raw, area_type, area_sqm), or (None, None, None) if unusable."""
    if area is None or area_type is None:
        return None, None, None
    area = area.strip()
    area_type = area_type.strip().upper()
    if area == "" or area_type not in ("M", "H"):
        return None, None, None
    try:
        area_raw = float(area)
    except ValueError:
        return None, None, None
    if area_raw <= 0 or not math.isfinite(area_raw):
        return None, None, None
    area_sqm = area_raw if area_type == "M" else area_raw * 10_000
    return area_raw, area_type, round(area_sqm, 2)

def extract_suburb(address):
    """'301/6 DUMARESQ ST, GORDON' -> 'GORDON'. None if there is no comma."""
    if address is None or "," not in address:
        return None
    suburb = address.rsplit(",", 1)[1].strip().upper()
    return suburb or None

def _normalise(text):
    """Collapse repeated spaces and uppercase, so trivial differences don't change the key."""
    return " ".join((text or "").split()).upper()

def build_sale_key(address, contract_date, purchase_price, legal_description):
    """32-character fingerprint of the four columns that identify a sale."""
    parts = [
        _normalise(address),
        contract_date.isoformat(),
        str(purchase_price),
        _normalise(legal_description),
    ]
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()

def clean_row(row):
    """Take one raw CSV row (a dict of strings).
    Return (record, None) if usable, or (None, reason) if the row must be rejected."""
    contract_date = parse_date(row.get("contract_date"))
    if contract_date is None:
        return None, "invalid contract_date"

    purchase_price = parse_price(row.get("purchase_price"))
    if purchase_price is None:
        return None, "invalid purchase_price"

    address = clean_text(row.get("address"))
    if address is None:
        return None, "missing address"

    suburb = extract_suburb(address)
    if suburb is None:
        return None, "no suburb in address"

    legal_description = clean_text(row.get("legal_description"))
    area_raw, area_type, area_sqm = parse_area(row.get("area"), row.get("area_type"))

    post_code = clean_text(row.get("post_code"))
    if post_code is not None and not (len(post_code) == 4 and post_code.isdigit()):
        post_code = None

    record = {
        "property_id": parse_int(row.get("property_id")),
        "council_name": clean_text(row.get("council_name")),
        "address": address,
        "suburb": suburb,
        "post_code": post_code,
        "purchase_price": purchase_price,
        "contract_date": contract_date,
        "settlement_date": parse_date(row.get("settlement_date")),
        "property_type": clean_text(row.get("property_type")),
        "nature_of_property": clean_text(row.get("nature_of_property")),
        "primary_purpose": clean_text(row.get("primary_purpose")),
        "zoning": clean_text(row.get("zoning")),
        "strata_lot_number": clean_text(row.get("strata_lot_number")),
        "property_name": clean_text(row.get("property_name")),
        "legal_description": legal_description,
        "area_raw": area_raw,
        "area_type": area_type,
        "area_sqm": area_sqm,
        "download_date": parse_date(row.get("download_date")),
        "sale_key": build_sale_key(address, contract_date, purchase_price, legal_description),
    }
    return record, None