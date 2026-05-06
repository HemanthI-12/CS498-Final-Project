"""
AirBnB Frontend Application - Flask Backend
Connects to MongoDB and provides API endpoints for all 6 queries
"""
import certifi
import sys
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Import implemented query functions from queries.py (project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from queries import (
    q1_airbnb_search,
    q2_neighborhoods_no_listings,
    q3_availability_periods,
    q5_reviews_by_city_december,
)

app = Flask(__name__, static_folder=os.path.dirname(__file__))
CORS(app)


FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

MONGO_URI = os.getenv('MONGO_URI')

try:
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    db = client['airbnb_min']
    listings = db['listings']
    calendar = db['calendar']
    reviews = db['reviews']
    neighborhoods = db['neighborhoods']
    print("✓ Connected to MongoDB successfully")
except Exception as e:
    print(f"✗ Failed to connect to MongoDB: {e}")


# =====================================================================
# QUERY 1: AirBnB Search - Listings for a date range with details
# =====================================================================
@app.route('/api/query1/listings', methods=['GET'])
def query1_listings():
    """
    Display listings available for a two-day period in Portland, OR
    with details sorted by average rating (descending)
    """
    try:
        city = request.args.get('city', 'Portland')
        start_date = request.args.get('start_date')  # Format: YYYY-MM-DD
        end_date = request.args.get('end_date')       # Format: YYYY-MM-DD

        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date required"}), 400

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        result = q1_airbnb_search(start, end, city)

        # Convert _id to string for JSON serialization
        for item in result:
            if '_id' in item:
                item['_id'] = str(item['_id'])

        return jsonify({
            "city": city,
            "dates": {"start": start_date, "end": end_date},
            "count": len(result),
            "listings": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 2: Neighborhoods with no available listings for a given month
# =====================================================================
@app.route('/api/query2/neighborhoods', methods=['GET'])
def query2_neighborhoods():
    """
    Find neighborhoods across all cities with no listings available for a given month
    """
    try:
        month = request.args.get('month')  # Format: YYYY-MM

        if not month:
            return jsonify({"error": "month parameter required (format: YYYY-MM)"}), 400

        month_dt = datetime.strptime(month, '%Y-%m')
        year = month_dt.year
        month_num = month_dt.month

        result = q2_neighborhoods_no_listings(year, month_num)

        return jsonify({
            "month": month,
            "count": len(result),
            "neighborhoods": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 3: Availability for booking - "Entire home/apt" in Salem
# =====================================================================
@app.route('/api/query3/availability', methods=['GET'])
def query3_availability():
    """
    For each "Entire home/apt" listing in Salem, provide availability
    periods for a particular month
    """
    try:
        month = request.args.get('month')  # Format: YYYY-MM
        room_type = request.args.get('room_type', 'Entire home/apt')

        if not month:
            return jsonify({"error": "month parameter required (format: YYYY-MM)"}), 400

        month_dt = datetime.strptime(month, '%Y-%m')
        year = month_dt.year
        month_num = month_dt.month

        flat = q3_availability_periods(year, month_num, room_type)

        # Group flat period list into per-listing structure expected by the frontend
        listings_map = {}
        for period in flat:
            name = period["name"]
            from_dt = period["from"]
            to_dt   = period["to"]
            min_n   = period["minimum_nights"]

            from_str = from_dt.strftime('%Y-%m-%d') if isinstance(from_dt, datetime) else str(from_dt)
            to_str   = to_dt.strftime('%Y-%m-%d')   if isinstance(to_dt, datetime)   else str(to_dt)
            nights   = (to_dt - from_dt).days + 1   if isinstance(from_dt, datetime) else 1

            if name not in listings_map:
                listings_map[name] = {
                    "name":                 name,
                    "month":                period["month"],
                    "min_nights":           min_n,
                    "max_nights":           None,
                    "availability_periods": [],
                }
            listings_map[name]["availability_periods"].append({
                "from":   from_str,
                "to":     to_str,
                "nights": nights,
            })

        listings_out = list(listings_map.values())

        return jsonify({
            "month": month,
            "city": "Salem",
            "room_type": room_type,
            "count": len(listings_out),
            "listings": listings_out,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 4: Booking trend by month - Portland listings (not yet implemented)
# =====================================================================
# @app.route('/api/query4/booking-trend', methods=['GET'])
# def query4_booking_trend():
#     """
#     For Entire home/apt listings in Portland, provide total available
#     nights for each month (March - August)
#     """
#     try:
#         year = request.args.get('year', default=datetime.now().year, type=int)
#
#         # Get all Entire home/apt listings in Portland
#         portland_listings = list(listings.find({
#             "city": "Portland",
#             "room_type": "Entire home/apt"
#         }))
#
#         listing_ids = [str(l.get('_id')) for l in portland_listings]
#
#         months_data = []
#
#         # Check March through August
#         for month_num in range(3, 9):
#             month_start = datetime(year, month_num, 1)
#             if month_num == 12:
#                 month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
#             else:
#                 month_end = datetime(year, month_num + 1, 1) - timedelta(seconds=1)
#
#             total_available_nights = 0
#
#             for listing_id in listing_ids:
#                 min_nights = listings.find_one({"_id": ObjectId(listing_id)}).get('min_nights', 1)
#
#                 cal_data = list(calendar.find({
#                     "listing_id": listing_id,
#                     "date": {"$gte": month_start, "$lte": month_end},
#                     "available": True
#                 }).sort("date", 1))
#
#                 if cal_data:
#                     current_period_start = cal_data[0]['date']
#                     current_period_end = cal_data[0]['date']
#
#                     for i in range(1, len(cal_data)):
#                         if (cal_data[i]['date'] - current_period_end).days == 1:
#                             current_period_end = cal_data[i]['date']
#                         else:
#                             period_length = (current_period_end - current_period_start).days + 1
#                             if period_length >= min_nights:
#                                 total_available_nights += period_length
#                             current_period_start = cal_data[i]['date']
#                             current_period_end = cal_data[i]['date']
#
#                     period_length = (current_period_end - current_period_start).days + 1
#                     if period_length >= min_nights:
#                         total_available_nights += period_length
#
#             month_name = datetime(year, month_num, 1).strftime('%B')
#             months_data.append({
#                 "month": month_name,
#                 "month_num": month_num,
#                 "available_nights": total_available_nights
#             })
#
#         return jsonify({
#             "city": "Portland",
#             "year": year,
#             "room_type": "Entire home/apt",
#             "trend": months_data
#         }), 200
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 5: Reviews by city in December
# =====================================================================
@app.route('/api/query5/review-trend', methods=['GET'])
def query5_review_trend():
    """
    For each city, count the reviews received in December of each year
    """
    try:
        rows = q5_reviews_by_city_december()

        # Reshape flat list into {city: {december_reviews: {year: count}}}
        trend = {}
        for row in rows:
            city = row["city"]
            year = str(row["year"])
            count = row["review_count"]
            if city not in trend:
                trend[city] = {"city": city, "december_reviews": {}}
            trend[city]["december_reviews"][year] = count

        return jsonify({"trend": trend}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 6: Reminder to book again (not yet implemented)
# =====================================================================
# @app.route('/api/query6/repeat-bookings', methods=['GET'])
# def query6_repeat_bookings():
#     """
#     Find listings that a reviewer has reviewed more than once that are
#     also available in the same month as they posted a review previously
#     """
#     try:
#         result = []
#
#         all_reviews = list(reviews.find({}))
#
#         reviewer_listing_map = {}
#
#         for review in all_reviews:
#             reviewer_id = review['reviewer_id']
#             listing_id = review['listing_id']
#             key = f"{reviewer_id}_{listing_id}"
#
#             if key not in reviewer_listing_map:
#                 reviewer_listing_map[key] = []
#
#             reviewer_listing_map[key].append(review)
#
#         for key, review_list in reviewer_listing_map.items():
#             if len(review_list) > 1:
#                 reviewer_id = review_list[0]['reviewer_id']
#                 listing_id = review_list[0]['listing_id']
#                 reviewer_name = review_list[0]['reviewer_name']
#
#                 listing_doc = listings.find_one({"_id": ObjectId(listing_id)})
#                 if not listing_doc:
#                     continue
#
#                 city = listing_doc['city']
#                 host_id = listing_doc['host']['host_id']
#
#                 other_listings = list(listings.find({
#                     "host.host_id": host_id,
#                     "city": city,
#                     "_id": {"$ne": ObjectId(listing_id)}
#                 }))
#
#                 for review in review_list:
#                     review_month = datetime(review['date'].year, review['date'].month, 1)
#                     review_month_end = datetime(review['date'].year, review['date'].month if review['date'].month < 12 else 1, 1)
#                     if review_month_end.month == 1:
#                         review_month_end = review_month_end.replace(year=review_month_end.year + 1)
#
#                     available_in_month = calendar.find_one({
#                         "listing_id": listing_id,
#                         "date": {"$gte": review_month, "$lt": review_month_end},
#                         "available": True
#                     })
#
#                     if available_in_month:
#                         result.append({
#                             "listing_name": listing_doc.get('name'),
#                             "listing_url": listing_doc.get('listing_url'),
#                             "description": listing_doc.get('description'),
#                             "host_name": listing_doc['host'].get('host_name'),
#                             "reviewer_name": reviewer_name,
#                             "previously_booked": True,
#                             "month": review['date'].strftime('%Y-%m'),
#                             "min_nights": listing_doc.get('min_nights'),
#                             "max_nights": listing_doc.get('max_nights'),
#                             "other_host_listings": len(other_listings),
#                             "other_listings": [
#                                 {
#                                     "name": l.get('name'),
#                                     "listing_url": l.get('listing_url')
#                                 } for l in other_listings[:3]
#                             ]
#                         })
#
#         return jsonify({
#             "count": len(result),
#             "repeat_bookings": result
#         }), 200
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# =====================================================================
# Health Check and Info Endpoints
# =====================================================================
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "AirBnB Frontend API is running"}), 200


@app.route('/api/info', methods=['GET'])
def info():
    """Get database info"""
    try:
        return jsonify({
            "database": "airbnb_min",
            "listings_count": listings.count_documents({}),
            "calendar_entries": calendar.count_documents({}),
            "reviews_count": reviews.count_documents({}),
            "neighborhoods_count": neighborhoods.count_documents({})
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
