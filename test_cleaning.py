from datetime import date
from cleaning import parse_date, parse_price, parse_area, extract_suburb, clean_row, build_sale_key

ROW = {
    "property_id": "1305430", "download_date": "2024-02-19",
    "council_name": "INNER WEST", "purchase_price": "780208",
    "address": "11 ST DAVIDS RD, HABERFIELD", "post_code": "2045",
    "property_type": "house", "strata_lot_number": "", "property_name": "",
    "area": "916.8", "area_type": "M", "contract_date": "2023-06-27",
    "settlement_date": "2024-02-09", "zoning": "R2",
    "nature_of_property": "V", "primary_purpose": "VACANT LAND",
    "legal_description": "A/318470 1/320780 State Heritage  Register 933",
}


# ---------- parse_date ----------

def test_parse_date_valid():
    assert parse_date("2024-01-19") == date(2024, 1, 19)

def test_parse_date_rejects_typo():
    assert parse_date("1024-01-05") is None

def test_parse_date_empty_and_none():
    assert parse_date("") is None
    assert parse_date("   ") is None
    assert parse_date(None) is None

def test_parse_date_wrong_format():
    assert parse_date("19/01/2024") is None

def test_parse_date_strips_spaces():
    assert parse_date("  2024-01-19 ") == date(2024, 1, 19)


# ---------- parse_price ----------

def test_parse_price_valid():
    assert parse_price("100000") == 100000

def test_parse_price_reject_letters():
    assert parse_price("1000a00") is None

def test_parse_price_empty_and_none():
    assert parse_price("") is None
    assert parse_price(None) is None

def test_parse_price_zero_and_negative():
    assert parse_price("0") is None
    assert parse_price("-500") is None

def test_parse_price_tiny_price_is_still_valid():
    # Suspicious but possible; stats decide what to do with these, not cleaning.
    assert parse_price("700") == 700


# ---------- parse_area ----------

def test_parse_area_valid():
    assert parse_area("1000", "M") == (1000.0, "M", 1000.0)

def test_parse_area_hectares_converted_to_sqm():
    assert parse_area("3.419", "H") == (3.419, "H", 34190.0)

def test_parse_area_empty():
    assert parse_area("", "") == (None, None, None)

def test_parse_area_invalid_unit():
    assert parse_area("500", "X") == (None, None, None)

def test_parse_area_missing_unit():
    assert parse_area("500", "") == (None, None, None)

def test_parse_area_not_a_number():
    assert parse_area("abc", "M") == (None, None, None)
    assert parse_area("nan", "M") == (None, None, None)

def test_parse_area_zero_or_negative():
    assert parse_area("-5", "M") == (None, None, None)
    assert parse_area("0", "H") == (None, None, None)


# ---------- extract_suburb ----------

def test_extract_suburb_normal():
    assert extract_suburb("301/6 DUMARESQ ST, GORDON") == "GORDON"

def test_extract_suburb_no_street_number():
    assert extract_suburb(" NEWELL HWY, NARRABRI") == "NARRABRI"

def test_extract_suburb_no_comma():
    assert extract_suburb("NO COMMA HERE") is None
    assert extract_suburb(None) is None


# ---------- clean_row ----------

def test_clean_row_valid():
    record, reason = clean_row(ROW)
    assert reason is None
    assert record["suburb"] == "HABERFIELD"
    assert record["purchase_price"] == 780208
    assert record["contract_date"] == date(2023, 6, 27)
    assert record["area_sqm"] == 916.8
    assert record["strata_lot_number"] is None  # empty text becomes None

def test_clean_row_rejects_bad_date():
    record, reason = clean_row({**ROW, "contract_date": "1024-01-05"})
    assert record is None
    assert reason == "invalid contract_date"

def test_clean_row_rejects_bad_price():
    record, reason = clean_row({**ROW, "purchase_price": "0"})
    assert record is None
    assert reason == "invalid purchase_price"

def test_clean_row_rejects_missing_address():
    record, reason = clean_row({**ROW, "address": ""})
    assert record is None
    assert reason == "missing address"

def test_clean_row_rejects_no_suburb():
    record, reason = clean_row({**ROW, "address": "NO COMMA HERE"})
    assert record is None
    assert reason == "no suburb in address"

def test_clean_row_bad_post_code_becomes_none():
    record, reason = clean_row({**ROW, "post_code": "20456"})
    assert reason is None  # row is kept, only the bad field is blanked
    assert record["post_code"] is None


# ---------- build_sale_key (decides what counts as a duplicate) ----------

def test_sale_key_same_sale_different_formatting():
    a = build_sale_key("11 ST DAVIDS RD, HABERFIELD", date(2023, 6, 27), 780208,
                       "State Heritage  Register 933")
    b = build_sale_key("11  st davids rd, haberfield", date(2023, 6, 27), 780208,
                       "state heritage register 933")
    assert a == b

def test_sale_key_different_lots_are_different_sales():
    # Real rows: same address and price, different lots sold together.
    a = build_sale_key("SADOWA RD, ROCKY CREEK", date(2023, 9, 1), 9273, "1/1297132")
    b = build_sale_key("SADOWA RD, ROCKY CREEK", date(2023, 9, 1), 9273, "2/1297132")
    assert a != b

def test_sale_key_is_32_characters():
    key = build_sale_key("A, B", date(2023, 1, 1), 1, None)
    assert len(key) == 32

def test_sale_key_ignores_download_date():
    # The same sale republished in a later weekly download must still be a duplicate.
    a, _ = clean_row(ROW)
    b, _ = clean_row({**ROW, "download_date": "2024-03-01"})
    assert a["sale_key"] == b["sale_key"]

def test_sale_key_ignores_property_id():
    # A later copy may fill in a property_id that was empty at first.
    a, _ = clean_row({**ROW, "property_id": ""})
    b, _ = clean_row(ROW)
    assert a["sale_key"] == b["sale_key"]