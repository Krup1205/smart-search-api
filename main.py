from fastapi import FastAPI
import requests
from parser import parse_query
from pydantic import BaseModel
from rapidfuzz import fuzz

app = FastAPI()

DATA_API_URL = "https://getallproperties-kdezv7i5fa-uc.a.run.app/"

class SearchRequest(BaseModel):
    query: str

# ✅ Extract dynamic areas & cities
def extract_locations(data):
    areas = set()
    cities = set()

    for item in data:
        if item.get("area"):
            areas.add(item["area"].lower())

        if item.get("city"):
            cities.add(item["city"].lower())

    return list(areas), list(cities)


@app.get("/")
def home():
    return {"message": "Smart Search API running 🚀"}


@app.get("/get-data")
def get_data():
    try:
        response = requests.get(DATA_API_URL, timeout=5)

        if response.status_code != 200:
            return {"error": "Failed to fetch data"}

        data = response.json()

        return {
            "count": len(data),
            "data": data[:3]
        }

    except Exception as e:
        return {"error": str(e)}


#  MAIN SMART SEARCH API
@app.post("/smart-search")
def smart_search(request: SearchRequest):
    try:
        query = request.query

        # Fetch data
        response = requests.get(DATA_API_URL, timeout=5)

        if response.status_code != 200:
            return {"error": "Failed to fetch data"}

        data = response.json()

        # Extract locations
        areas, cities = extract_locations(data)

        # Parse query
        filters = parse_query(query, areas, cities)

        # 🔥 Smart ranking logic
        results = []

        for item in data:
            score = 0

            # Property Type
            if filters.get("propertyType"):
                if item.get("propertyType", "").lower() == filters["propertyType"].lower():
                    score += 2

            # Gender
            if filters.get("GenderType"):
                if item.get("GenderType", "").lower() == filters["GenderType"].lower():
                    score += 2

            # Tenant Type
            if filters.get("TenantType"):
                if item.get("TenantType", "").lower() == filters["TenantType"].lower():
                    score += 1

            # Area
            if filters.get("area"):
                item_area = item.get("area", "").lower()
                similarity = fuzz.partial_ratio(filters["area"], item_area)

                if similarity > 70:
                    score += 3

            # City
            if filters.get("city"):
                item_city = item.get("city", "").lower()
                similarity = fuzz.partial_ratio(filters["city"], item_city)

                if similarity > 70:
                    score += 2

            # Price
            if filters.get("max_price"):
                if item.get("price", 0) <= filters["max_price"]:
                    score += 2

            # Facilities
            if filters.get("facilities"):
                item_facilities = [f.lower() for f in item.get("facilities", [])]
                matches = sum(
                    1 for f in filters["facilities"] if f.lower() in item_facilities
                )
                score += matches

            # Add if relevant
            if score > 0:
                item["score"] = score
                results.append(item)

        # Sort results
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "filters": filters,
            "count": len(results),
            "results": results[:20]  # limit results
        }

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/suggestions")
def get_suggestions(q: str):
    try:
        # Fetch data
        response = requests.get(DATA_API_URL, timeout=5)

        if response.status_code != 200:
            return {"error": "Failed to fetch data"}

        data = response.json()

        # Extract areas & cities
        areas, cities = extract_locations(data)

        query = q.lower()

        suggestions = set()

        # Match areas
        for area in areas:
            similarity = fuzz.partial_ratio(query, area)
            if similarity > 70:
                suggestions.add(area.title())

        # Match cities
        for city in cities:
            similarity = fuzz.partial_ratio(query, city)
            if similarity > 70:
                suggestions.add(city.title())

        return {
            "query": q,
            "suggestions": list(suggestions)[:10]
        }

    except Exception as e:
        return {"error": str(e)}