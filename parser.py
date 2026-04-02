import re

def parse_query(query, areas_list, cities_list):
    query = query.lower()

    result = {}

    # 🏠 Property Type
    if "pg" in query:
        result["propertyType"] = "PG"
    elif "flat" in query or "apartment" in query:
        result["propertyType"] = "Flat"

    # 👩 Gender
    if any(word in query for word in ["girls", "female", "ladies"]):
        result["GenderType"] = "Female"
    elif any(word in query for word in ["boys", "male", "gents"]):
        result["GenderType"] = "Male"

    # 👨‍🎓 Tenant Type
    if "student" in query:
        result["TenantType"] = "Students"
    elif "working" in query or "job" in query:
        result["TenantType"] = "Working"

    # 💰 Price (handles "under 8000", "below 10k", etc.)
    price = re.findall(r'\d+', query)
    if price:
        result["max_price"] = int(price[0])

    # 💸 Cheap / Budget logic
    if any(word in query for word in ["cheap", "low", "budget"]):
        result["max_price"] = result.get("max_price", 5000)

    # 🛠 Facilities
    facilities_map = ["wifi", "ac", "food", "parking", "laundry", "cleaning"]
    result["facilities"] = [f.upper() for f in facilities_map if f in query]

    # 📍 Dynamic Area Match (improved)
    for area in areas_list:
        if area in query:
            result["area"] = area
            break

    # 🌆 Dynamic City Match (improved)
    for city in cities_list:
        if city in query:
            result["city"] = city
            break

    return result