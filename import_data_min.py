"""
Minimal AirBnB import
Loads into database: airbnb_min

listings:    { _id, city, name, neighborhood, room_type, property_type,
               accommodates, amenities, price, rating, min_nights, max_nights,
               listing_url, description, host: { host_id, host_name } }

calendar:    { _id (ObjectId), listing_id, date, available, price,
               minimum_nights, maximum_nights }

reviews:     { _id (ObjectId), listing_id, reviewer_id, reviewer_name,
               date, comments }

neighborhoods: { _id (ObjectId), city, neighborhood }
"""

import gzip
import zipfile
import csv
import json
import re
import os
import io
from datetime import datetime
from dotenv import load_dotenv

from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError

load_dotenv()

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME    = "airbnb_min"
DATA_ROOT  = os.path.dirname(os.path.abspath(__file__))
BATCH_SIZE = 5000

CITIES = {
    "Los Angeles": "Los Angeles",
    "Portland":    "Portland",
    "Salem":       "Salem",
    "San Diego":   "San Diego",
}


# parsers

def parse_price(val):
    if not val:
        return None
    try:
        return float(re.sub(r"[$,]", "", val.strip()))
    except ValueError:
        return None

def parse_bool(val):
    if not val:
        return None
    v = val.strip().lower()
    if v in ("t", "true"):
        return True
    if v in ("f", "false"):
        return False
    return None

def parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val.strip(), "%Y-%m-%d")
    except ValueError:
        return None

def parse_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def parse_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def parse_amenities(val):
    if not val:
        return []
    try:
        result = json.loads(val)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

# bulk insert

def bulk_insert(collection, docs, ordered=False):
    if not docs:
        return 0
    try:
        return len(collection.insert_many(docs, ordered=ordered).inserted_ids)
    except BulkWriteError as e:
        inserted = e.details.get("nInserted", 0)
        dupes    = len(e.details.get("writeErrors", []))
        print(f"    {inserted} inserted, {dupes} duplicates skipped")
        return inserted


# collections

def build_listing(row, city):
    neighborhood = row.get("neighbourhood_cleansed") or None
    room_type    = row.get("room_type") or None
    host_id      = row.get("host_id") or None
    host_name    = row.get("host_name") or None
    if not all([neighborhood, room_type, host_id, host_name]):
        return None
    return {
        "_id":          row["id"],
        "city":         city,
        "name":         row.get("name") or None,
        "neighborhood": neighborhood,
        "room_type":    room_type,
        "property_type":row.get("property_type") or None,
        "accommodates": parse_int(row.get("accommodates")),
        "amenities":    parse_amenities(row.get("amenities")),
        "price":        parse_price(row.get("price")),
        "rating":       parse_float(row.get("review_scores_rating")),
        "min_nights":   parse_int(row.get("minimum_nights")),
        "max_nights":   parse_int(row.get("maximum_nights")),
        "listing_url":  row.get("listing_url") or None,
        "description":  row.get("description") or None,
        "host": {
            "host_id":   host_id,
            "host_name": host_name,
        },
    }

def build_calendar_doc(row, city):
    date      = parse_date(row["date"])
    available = parse_bool(row["available"])
    min_n     = parse_int(row.get("minimum_nights"))
    max_n     = parse_int(row.get("maximum_nights"))
    if not all([date, available is not None, min_n is not None, max_n is not None]):
        return None
    return {
        "listing_id":     row["listing_id"],
        "date":           date,
        "available":      available,
        "price":          parse_price(row.get("price")),
        "minimum_nights": min_n,
        "maximum_nights": max_n,
    }

def build_review_doc(row, city):
    listing_id  = row.get("listing_id") or None
    reviewer_id = row.get("reviewer_id") or None
    date        = parse_date(row["date"])
    if not all([listing_id, reviewer_id, date]):
        return None
    return {
        "listing_id":    listing_id,
        "reviewer_id":   reviewer_id,
        "reviewer_name": row.get("reviewer_name") or None,
        "date":          date,
        "comments":      row.get("comments") or None,
    }

def build_neighborhood_doc(row, city):
    neighborhood = row.get("neighbourhood") or row.get("neighborhood")
    if not neighborhood:
        return None
    return {
        "city":         city,
        "neighborhood": neighborhood,
    }


# import fn

def open_file(path, compressed):
    """Open a file for reading, handling gzip, zip, or plain text."""
    if not compressed:
        return open(path, "r", encoding="utf-8"), None
    with open(path, "rb") as probe:
        magic = probe.read(2)
    if magic == b"PK":
        zf = zipfile.ZipFile(path, "r")
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        return io.TextIOWrapper(zf.open(name), encoding="utf-8"), zf
    return gzip.open(path, "rt", encoding="utf-8"), None

def import_collection(col, city, path, builder, compressed=True):
    batch, total = [], 0
    f, handle = open_file(path, compressed)
    try:
        for row in csv.DictReader(f):
            doc = builder(row, city)
            if doc:
                batch.append(doc)
            if len(batch) >= BATCH_SIZE:
                total += bulk_insert(col, batch)
                batch = []
        if batch:
            total += bulk_insert(col, batch)
    finally:
        f.close()
        if handle:
            handle.close()
    print(f"    → {total:,} docs")


# indices based on data model

def create_indexes(db):
    print("\nCreating indexes...")

    db.listings.create_index([("city", ASCENDING), ("neighborhood", ASCENDING)])
    db.listings.create_index([("city", ASCENDING), ("room_type", ASCENDING)])
    db.listings.create_index([("host.host_id", ASCENDING), ("city", ASCENDING)])

    db.calendar.create_index([("listing_id", ASCENDING), ("date", ASCENDING), ("available", ASCENDING)])
    db.calendar.create_index([("date", ASCENDING), ("available", ASCENDING)])

    db.reviews.create_index([("date", ASCENDING), ("listing_id", ASCENDING)])
    db.reviews.create_index([("reviewer_id", ASCENDING), ("listing_id", ASCENDING), ("date", ASCENDING)])

    db.neighborhoods.create_index([("city", ASCENDING), ("neighborhood", ASCENDING)])

    print("  Done.")


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except Exception:
        print("ERROR: Could not connect to MongoDB at", MONGO_URI)
        return

    db = client[DB_NAME]
    print(f"Connected. Using database: '{DB_NAME}'\n")

    for folder, city in CITIES.items():
        city_path = os.path.join(DATA_ROOT, folder)
        print(f"=== {city} ===")

        paths = {
            "listings":      (os.path.join(city_path, "listings.csv.gz"),      True,  build_listing),
            "calendar":      (os.path.join(city_path, "calendar.csv.gz"),      True,  build_calendar_doc),
            "reviews":       (os.path.join(city_path, "reviews.csv.gz"),       True,  build_review_doc),
            "neighborhoods": (os.path.join(city_path, "neighbourhoods.csv"),   False, build_neighborhood_doc),
        }

        for col_name, (path, compressed, builder) in paths.items():
            if os.path.exists(path):
                print(f" {col_name} ({city}) ")
                import_collection(db[col_name], city, path, builder, compressed)

    create_indexes(db)

    print("\nImport complete. Collection counts:")
    for col in ["listings", "calendar", "reviews", "neighborhoods"]:
        print(f"  {col}: {db[col].count_documents({}):,}")


if __name__ == "__main__":
    main()
