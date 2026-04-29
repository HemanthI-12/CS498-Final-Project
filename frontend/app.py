"""
AirBnB Frontend Application - Flask Backend
Connects to MongoDB and provides API endpoints for all 6 queries
"""
import certifi
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv('MONGO_URI')

try:
    client = MongoClient(MONGO_URI, tls = True, tlsCAFile = certifi.where())
    db = client['airbnb_min']
    listings = db['listings']
    calendar = db['calendar']
    reviews = db['reviews']
    neighborhoods = db['neighborhoods']
    print("✓ Connected to MongoDB successfully")
except Exception as e:
    print(f"✗ Failed to connect to MongoDB: {e}")



# QUERY 1: AirBnB Search - Listings for a date range with details
@app.route('/api/query1/listings', methods=['GET'])
def query1_listings():
    """
    Display listings available for a two-day period in Portland, OR
    with details sorted by average rating (descending)
    """
    try:
        city = request.args.get('city', 'Portland')
        start_date = request.args.get('start_date')  # Format: YYYY-MM-DD
        end_date = request.args.get('end_date')      # Format: YYYY-MM-DD
        
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date required"}), 400
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Find listings in the city
        city_listings = list(listings.find({"city": city}))
        
        result = []
        for listing in city_listings:
            # Check availability for all dates in range
            available_dates = calendar.find({
                "listing_id": str(listing.get('_id')),
                "date": {"$gte": start, "$lte": end},
                "available": True
            })
            
            available_count = len(list(available_dates))
            
            # Only include if available for the entire period
            if available_count == (end - start).days + 1:
                result.append({
                    "_id": str(listing.get('_id')),
                    "name": listing.get('name'),
                    "neighborhood": listing.get('neighborhood'),
                    "room_type": listing.get('room_type'),
                    "accommodates": listing.get('accommodates'),
                    "property_type": listing.get('property_type'),
                    "amenities": listing.get('amenities', []),
                    "price": listing.get('price'),
                    "rating": listing.get('rating'),
                    "listing_url": listing.get('listing_url'),
                    "description": listing.get('description')
                })
        
        # Sort by rating descending
        result.sort(key=lambda x: x['rating'] if x['rating'] else 0, reverse=True)
        
        return jsonify({
            "city": city,
            "dates": {"start": start_date, "end": end_date},
            "count": len(result),
            "listings": result
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 2: Neighborhoods with no listings for a given month
# =====================================================================
@app.route('/api/query2/neighborhoods', methods=['GET'])
def query2_neighborhoods():
    """
    Find neighborhoods in any city with no listings for a given month
    """
    try:
        month = request.args.get('month')  # Format: YYYY-MM
        
        if not month:
            return jsonify({"error": "month parameter required (format: YYYY-MM)"}), 400
        
        # Parse month
        month_start = datetime.strptime(month, '%Y-%m')
        month_end = datetime(month_start.year, month_start.month if month_start.month < 12 else 1,
                            1) + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(seconds=1)
        
        # Get all neighborhoods and cities
        all_neighborhoods = list(neighborhoods.find({}))
        
        result = []
        for neighborhood_doc in all_neighborhoods:
            city = neighborhood_doc['city']
            neighborhood_name = neighborhood_doc['neighborhood']
            
            # Check if there are listings in this neighborhood
            listing_count = listings.count_documents({
                "city": city,
                "neighborhood": neighborhood_name
            })
            
            if listing_count == 0:
                result.append({
                    "city": city,
                    "neighborhood": neighborhood_name
                })
        
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
        
        if not month:
            return jsonify({"error": "month parameter required (format: YYYY-MM)"}), 400
        
        month_start = datetime.strptime(month, '%Y-%m')
        month_end = datetime(month_start.year, month_start.month if month_start.month < 12 else 1, 1)
        if month_end.month == 1:
            month_end = month_end.replace(year=month_end.year + 1)
        month_end = month_end - timedelta(seconds=1)
        
        # Get all Entire home/apt listings in Salem
        salem_listings = list(listings.find({
            "city": "Salem",
            "room_type": "Entire home/apt"
        }))
        
        result = []
        
        for listing in salem_listings:
            listing_id = str(listing.get('_id'))
            min_nights = listing.get('min_nights', 1)
            max_nights = listing.get('max_nights', 365)
            
            # Get availability for the month
            cal_data = list(calendar.find({
                "listing_id": listing_id,
                "date": {"$gte": month_start, "$lte": month_end},
                "available": True
            }).sort("date", 1))
            
            # Find consecutive availability periods
            availability_periods = []
            if cal_data:
                current_period_start = cal_data[0]['date']
                current_period_end = cal_data[0]['date']
                
                for i in range(1, len(cal_data)):
                    if (cal_data[i]['date'] - current_period_end).days == 1:
                        current_period_end = cal_data[i]['date']
                    else:
                        # End of period
                        period_length = (current_period_end - current_period_start).days + 1
                        if period_length >= min_nights:
                            availability_periods.append({
                                "from": current_period_start.strftime('%Y-%m-%d'),
                                "to": current_period_end.strftime('%Y-%m-%d'),
                                "nights": period_length,
                                "can_book": True
                            })
                        current_period_start = cal_data[i]['date']
                        current_period_end = cal_data[i]['date']
                
                # Don't forget the last period
                period_length = (current_period_end - current_period_start).days + 1
                if period_length >= min_nights:
                    availability_periods.append({
                        "from": current_period_start.strftime('%Y-%m-%d'),
                        "to": current_period_end.strftime('%Y-%m-%d'),
                        "nights": period_length,
                        "can_book": True
                    })
            
            result.append({
                "listing_id": listing_id,
                "name": listing.get('name'),
                "month": month,
                "min_nights": min_nights,
                "max_nights": max_nights,
                "availability_periods": availability_periods
            })
        
        return jsonify({
            "month": month,
            "city": "Salem",
            "room_type": "Entire home/apt",
            "count": len(result),
            "listings": result
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 4: Booking trend by month - Portland listings
# =====================================================================
@app.route('/api/query4/booking-trend', methods=['GET'])
def query4_booking_trend():
    """
    For Entire home/apt listings in Portland, provide total available
    nights for each month (March - August)
    """
    try:
        year = request.args.get('year', default=datetime.now().year, type=int)
        
        # Get all Entire home/apt listings in Portland
        portland_listings = list(listings.find({
            "city": "Portland",
            "room_type": "Entire home/apt"
        }))
        
        listing_ids = [str(l.get('_id')) for l in portland_listings]
        
        months_data = []
        
        # Check March through August
        for month_num in range(3, 9):
            month_start = datetime(year, month_num, 1)
            if month_num == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month_num + 1, 1) - timedelta(seconds=1)
            
            total_available_nights = 0
            
            for listing_id in listing_ids:
                min_nights = listings.find_one({"_id": ObjectId(listing_id)}).get('min_nights', 1)
                
                # Get availability for this listing in this month
                cal_data = list(calendar.find({
                    "listing_id": listing_id,
                    "date": {"$gte": month_start, "$lte": month_end},
                    "available": True
                }).sort("date", 1))
                
                if cal_data:
                    current_period_start = cal_data[0]['date']
                    current_period_end = cal_data[0]['date']
                    
                    for i in range(1, len(cal_data)):
                        if (cal_data[i]['date'] - current_period_end).days == 1:
                            current_period_end = cal_data[i]['date']
                        else:
                            period_length = (current_period_end - current_period_start).days + 1
                            if period_length >= min_nights:
                                total_available_nights += period_length
                            current_period_start = cal_data[i]['date']
                            current_period_end = cal_data[i]['date']
                    
                    period_length = (current_period_end - current_period_start).days + 1
                    if period_length >= min_nights:
                        total_available_nights += period_length
            
            month_name = datetime(year, month_num, 1).strftime('%B')
            months_data.append({
                "month": month_name,
                "month_num": month_num,
                "available_nights": total_available_nights
            })
        
        return jsonify({
            "city": "Portland",
            "year": year,
            "room_type": "Entire home/apt",
            "trend": months_data
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 5: Booking trend by city - Reviews in December
# =====================================================================
@app.route('/api/query5/review-trend', methods=['GET'])
def query5_review_trend():
    """
    For each city, count the reviews received in December of each year
    """
    try:
        # Get all distinct cities
        cities_list = listings.distinct("city")
        
        result = {}
        
        for city in cities_list:
            # Get listings in this city
            city_listing_ids = [str(l.get('_id')) for l in listings.find({"city": city})]
            
            review_counts_by_year = {}
            
            for listing_id in city_listing_ids:
                # Find all reviews for December across all years
                dec_reviews = list(reviews.find({
                    "listing_id": listing_id,
                    "date": {
                        "$gte": datetime(2000, 12, 1),
                        "$lte": datetime(2099, 12, 31)
                    }
                }))
                
                for review in dec_reviews:
                    year = review['date'].year
                    review_counts_by_year[year] = review_counts_by_year.get(year, 0) + 1
            
            result[city] = {
                "city": city,
                "december_reviews": review_counts_by_year
            }
        
        return jsonify({
            "trend": result
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# QUERY 6: Reminder to book again
# =====================================================================
@app.route('/api/query6/repeat-bookings', methods=['GET'])
def query6_repeat_bookings():
    """
    Find listings that a reviewer has reviewed more than once that are
    also available in the same month as they posted a review previously
    """
    try:
        result = []
        
        # Get all reviews
        all_reviews = list(reviews.find({}))
        
        # Group reviews by reviewer and listing
        reviewer_listing_map = {}
        
        for review in all_reviews:
            reviewer_id = review['reviewer_id']
            listing_id = review['listing_id']
            key = f"{reviewer_id}_{listing_id}"
            
            if key not in reviewer_listing_map:
                reviewer_listing_map[key] = []
            
            reviewer_listing_map[key].append(review)
        
        # Find reviewers who reviewed the same listing more than once
        for key, review_list in reviewer_listing_map.items():
            if len(review_list) > 1:
                reviewer_id = review_list[0]['reviewer_id']
                listing_id = review_list[0]['listing_id']
                reviewer_name = review_list[0]['reviewer_name']
                
                # Get listing details
                listing_doc = listings.find_one({"_id": ObjectId(listing_id)})
                if not listing_doc:
                    continue
                
                city = listing_doc['city']
                host_id = listing_doc['host']['host_id']
                
                # Find other listings by same host in same city
                other_listings = list(listings.find({
                    "host.host_id": host_id,
                    "city": city,
                    "_id": {"$ne": ObjectId(listing_id)}
                }))
                
                for review in review_list:
                    review_month = datetime(review['date'].year, review['date'].month, 1)
                    review_month_end = datetime(review['date'].year, review['date'].month if review['date'].month < 12 else 1, 1)
                    if review_month_end.month == 1:
                        review_month_end = review_month_end.replace(year=review_month_end.year + 1)
                    
                    # Check if listing is available in same month
                    available_in_month = calendar.find_one({
                        "listing_id": listing_id,
                        "date": {"$gte": review_month, "$lt": review_month_end},
                        "available": True
                    })
                    
                    if available_in_month:
                        result.append({
                            "listing_name": listing_doc.get('name'),
                            "listing_url": listing_doc.get('listing_url'),
                            "description": listing_doc.get('description'),
                            "host_name": listing_doc['host'].get('host_name'),
                            "reviewer_name": reviewer_name,
                            "previously_booked": True,
                            "month": review['date'].strftime('%Y-%m'),
                            "min_nights": listing_doc.get('min_nights'),
                            "max_nights": listing_doc.get('max_nights'),
                            "other_host_listings": len(other_listings),
                            "other_listings": [
                                {
                                    "name": l.get('name'),
                                    "listing_url": l.get('listing_url')
                                } for l in other_listings[:3]  # Show first 3
                            ]
                        })
        
        return jsonify({
            "count": len(result),
            "repeat_bookings": result
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    app.run(debug=True, port=5000)
