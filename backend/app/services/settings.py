from app.database.connection import get_db
from datetime import datetime

async def get_office_settings():
    db = get_db()
    settings = await db.office_settings.find_one({})
    if settings:
        return {
            "id": str(settings["_id"]),
            "latitude": settings["latitude"],
            "longitude": settings["longitude"],
            "radius": settings["radius"],
            "office_name": settings.get("office_name", "Main Office"),
            "updated_at": settings.get("updated_at")
        }
    return None

async def update_office_settings(latitude: float, longitude: float, radius: float, office_name: str = "Main Office"):
    db = get_db()
    existing = await db.office_settings.find_one({})
    data = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "office_name": office_name,
        "updated_at": datetime.utcnow()
    }
    if existing:
        await db.office_settings.update_one({}, {"$set": data})
    else:
        await db.office_settings.insert_one(data)
    return await get_office_settings()

async def verify_location(emp_lat: float, emp_lng: float):
    import math
    db = get_db()
    settings = await db.office_settings.find_one({})
    if not settings:
        return True, 0  # Agar settings nahi hain to allow karo

    office_lat = settings["latitude"]
    office_lng = settings["longitude"]
    radius = settings["radius"]

    # Haversine formula — accurate distance calculation
    R = 6371000  # Earth radius in meters
    lat1 = math.radians(emp_lat)
    lat2 = math.radians(office_lat)
    dlat = math.radians(office_lat - emp_lat)
    dlng = math.radians(office_lng - emp_lng)

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance <= radius, round(distance)