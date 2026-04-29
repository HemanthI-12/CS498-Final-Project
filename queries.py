"""
AirBnB MongoDB Queries

Six queries against the 'airbnb' database (collections: listings, calendar,
reviews, neighborhoods).
"""

from datetime import datetime
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



# Q2: Neighborhoods with No Available Listings

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
