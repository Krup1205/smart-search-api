from fastapi import FastAPI
import requests
from parser import parse_query
from pydantic import BaseModel
from rapidfuzz import fuzz
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

DATA_API_URL = "https://getallproperties-kdezv7i5fa-uc.a.run.app/"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

        results = []

        for item in data:
            score = 0
            strict_fail = False

            # Property Type (STRICT)
            if filters.get("propertyType"):
                item_type = item.get("propertyType", "")

                # Normalize to lowercase for safe comparison
                item_type = item_type.lower()
                filter_types = [t.lower() for t in filters["propertyType"]]

                if item_type not in filter_types:
                    strict_fail = True
                else:
                    score += 2

            # Gender (STRICT)
            if filters.get("GenderType"):
                if item.get("GenderType", "").lower() != filters["GenderType"].lower():
                    strict_fail = True
                else:
                    score += 2

            # Tenant Type (STRICT)
            if filters.get("TenantType"):
                if item.get("TenantType", "").lower() != filters["TenantType"].lower():
                    strict_fail = True
                else:
                    score += 1

            # Area (STRICT + FUZZY)
            if filters.get("area"):
                item_area = item.get("area", "").lower()
                similarity = fuzz.partial_ratio(filters["area"], item_area)

                if similarity < 70:
                    strict_fail = True
                else:
                    score += 3

            # City (STRICT + FUZZY)
            if filters.get("city"):
                item_city = item.get("city", "").lower()
                similarity = fuzz.partial_ratio(filters["city"], item_city)

                if similarity < 70:
                    strict_fail = True
                else:
                    score += 2

            # If strict condition fails → skip item
            if strict_fail:
                continue

            # Price (SOFT)
            if filters.get("max_price"):
                if item.get("price", 0) <= filters["max_price"]:
                    score += 2

            # Facilities (SOFT)
            if filters.get("facilities"):
                item_facilities = [f.lower() for f in item.get("facilities", [])]
                matches = sum(
                    1 for f in filters["facilities"] if f.lower() in item_facilities
                )
                score += matches

            results.append({**item, "score": score})

        # Sort best results
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "filters": filters,
            "count": len(results),
            "results": results[:20]
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