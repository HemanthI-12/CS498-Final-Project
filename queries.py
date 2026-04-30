"""
AirBnB MongoDB Queries

Six queries against the 'airbnb' database (collections: listings, calendar,
reviews, neighborhoods).
"""

from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME    = "airbnb_min"

# MONGO_URI  = "mongodb://localhost:27017"
# DB_NAME    = "airbnb"

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

# Query 1: AirBnB Search

# Find available listings in Portland for a 2-night stay, sorted by rating descending.
# Params: city, check_in (datetime), check_out (datetime)
# Returns: List of JSON objects structured as 
# {
# 	"_id":   str,
# 	"name":  str,
# 	"neighborhood":  str,
# 	"room_type":  str,
# 	"property_type": str,
# 	"accommodates": int,
# 	"amenities":  list[str],
# 	"price":  int or None,
# 	"rating":  float,
# }


def q1_airbnb_search(check_in: datetime, check_out: datetime, city: str = "Portland"):
    pipeline = [
        # Step 1: filter calendar with {listing_id, date, available} index
        {"$match": {
            "date":           {"$gte": check_in, "$lte": check_out},
            "available":      True,
            "minimum_nights": {"$lte": 2},
            "maximum_nights": {"$gte": 2},
        }},
        # Step 2: group by listing_id, count matching available nights
        {"$group": {
            "_id":   "$listing_id",
            "count": {"$sum": 1},
        }},
        # Keep only listings where BOTH nights are available
        {"$match": {"count": 2}},
        # Step 3: join with listings collection on listing _id, filter by city
        {"$lookup": {
            "from":         "listings",
            "localField":   "_id",
            "foreignField": "_id",
            "as":           "listing",
        }},
        {"$unwind": "$listing"},
        {"$match": {"listing.city": city}},
        # Step 4: exclude listings with no rating (technical Step 5 in design doc, but is more efficient to get rid of them here)
        {"$match": {"listing.rating": {"$ne": None, "$exists": True}}},
        # Step 5: project only the fields we care about (design doc Step 4)
        {"$project": {
            "_id":           "$listing._id",
            "name":          "$listing.name",
            "neighborhood":  "$listing.neighborhood",
            "room_type":     "$listing.room_type",
            "property_type": "$listing.property_type",
            "accommodates":  "$listing.accommodates",
            "amenities":     "$listing.amenities",
            "price":         "$listing.price",
            "rating":        "$listing.rating",
        }},
        # Sort by rating descending
        {"$sort": {"rating": -1}}
    ]
    return list(db.calendar.aggregate(pipeline))

# Query 2: Neighborhoods with No Available Listings

# Find neighborhoods in a city that have no listings with availability in a given month.
# Params: city, year (int), month (int)
# Returns: list[str] with each entry being the name of a neighborhood

def q2_neighborhoods_no_listings(city: str, year: int, month: int):
    month_start = datetime(year, month, 1)
    
    # goes from month/01/year to (month+1)/01/year if month != 12 else to 01/01/(year + 1)
    
    # last day of the month
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    # Step 1: listing_ids with at least one available day in the month (date, available) index
    available_listing_ids = db.calendar.distinct(
        "listing_id",
        {
            "date":      {"$gte": month_start, "$lt": month_end},
            "available": True,
        }
    )

    # Step 2: neighborhoods of those listings (filtered by city)
    occupied_neighborhoods = set(
        doc["neighborhood"]
        for doc in db.listings.find(
            {"_id": {"$in": available_listing_ids}, "city": city, "neighborhood": {"$ne": None}},
            {"neighborhood": 1}
        )
    )

    # Step 3: full neighborhood list for this city
    all_neighborhoods = set(
        doc["neighborhood"]
        for doc in db.neighborhoods.find(
            {"city": city, "neighborhood": {"$ne": None}},
            {"neighborhood": 1}
        )
    )

    # Step 4: neighborhoods with no available listings
    empty = sorted(all_neighborhoods - occupied_neighborhoods)
    return empty


# Shared helper: find valid booking-start days for a set of listing IDs in a month.
# Returns {listing_id: [(date, min_nights), ...]} of valid start days.

def _valid_starts_for_month(listing_ids: list, year: int, month: int) -> dict:
    month_start = datetime(year, month, 1)
    month_end   = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    # Fetch up to 30 days past month_end so min_nights checks near month boundaries work
    buffer_end = month_end + timedelta(days=30)

    cursor = db.calendar.find(
        {
            "listing_id": {"$in": listing_ids},
            "date":       {"$gte": month_start, "$lt": buffer_end},
        },
        {"listing_id": 1, "date": 1, "available": 1, "minimum_nights": 1}
    ).sort([("listing_id", 1), ("date", 1)])

    by_listing: dict = {}
    for doc in cursor:
        by_listing.setdefault(doc["listing_id"], []).append(doc)

    result: dict = {}
    for listing_id, docs in by_listing.items():
        date_map = {doc["date"]: doc for doc in docs}
        valid = []
        for doc in docs:
            if doc["date"] >= month_end:
                continue  # buffer zone — only used for look-ahead, not valid starts
            if not doc.get("available"):
                continue
            min_n = doc.get("minimum_nights") or 1
            if all(
                date_map.get(doc["date"] + timedelta(days=i), {}).get("available")
                for i in range(min_n)
            ):
                valid.append((doc["date"], min_n))
        if valid:
            result[listing_id] = valid
    return result


# Query 3: Availability for Booking (Salem)
#
# For each "Entire home/apt" listing in Salem, find bookable availability periods in a given month.
#
# Params: year (int), month (int), room_type (str)
# Returns: list of {name, month, from, to, minimum_nights}

def q3_availability_periods(year: int, month: int, room_type: str = "Entire home/apt"):

    # Step 1: get all matching listings in Salem
    listings = {
        doc["_id"]: doc.get("name")
        for doc in db.listings.find(
            {"city": "Salem", "room_type": room_type},
            {"name": 1}
        )
    }

    # Step 2: find valid booking-start days per listing
    valid_by_listing = _valid_starts_for_month(list(listings.keys()), year, month)

    results = []
    for listing_id, valid_starts in valid_by_listing.items():
        name = listings.get(listing_id)

        # Step 3: group consecutive valid-start days into periods
        period_start, period_min_n = valid_starts[0]
        prev_date = period_start

        for date, min_n in valid_starts[1:]:
            if (date - prev_date).days == 1:
                prev_date = date
            else:
                results.append({
                    "name":           name,
                    "month":          f"{year}-{month:02d}",
                    "from":           period_start,
                    "to":             prev_date,
                    "minimum_nights": period_min_n,
                })
                period_start, period_min_n = date, min_n
                prev_date = date

        results.append({
            "name":           name,
            "month":          f"{year}-{month:02d}",
            "from":           period_start,
            "to":             prev_date,
            "minimum_nights": period_min_n,
        })

    return results


# Query 5: Reviews by City per December
#
# Count how many reviews were written in December of a given year, grouped by city.
# Params: year (int)
# Returns: list of json objects containing {city: str, review_count: int}

def q5_reviews_by_city_december(year: int):
    dec_start = datetime(year, 12, 1)
    dec_end   = datetime(year + 1, 1, 1)

    pipeline = [
        # Step 1: reviews in December of the target year
        {"$match": {
            "date": {"$gte": dec_start, "$lt": dec_end},
        }},
        # Step 2: join with listings to get city
        {"$lookup": {
            "from":         "listings",
            "localField":   "listing_id",
            "foreignField": "_id",
            "as":           "listing",
        }},
        {"$unwind": "$listing"},
        # Step 3: group by city, count reviews
        {"$group": {
            "_id":          "$listing.city",
            "review_count": {"$sum": 1},
        }},
        {"$sort": {"review_count": -1}},
        {"$project": {
            "city":         "$_id",
            "review_count": 1,
            "_id":          0,
        }},
    ]
    return list(db.reviews.aggregate(pipeline))