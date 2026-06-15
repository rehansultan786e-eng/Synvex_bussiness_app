from app.database.connection import get_db
from datetime import datetime

async def get_allowed_ips():
    db = get_db()
    settings = await db.ip_settings.find_one({})
    if settings:
        return {
            "id": str(settings["_id"]),
            "allowed_ips": settings.get("allowed_ips", []),
            "ip_check_enabled": settings.get("ip_check_enabled", False),
            "updated_at": settings.get("updated_at")
        }
    return {"allowed_ips": [], "ip_check_enabled": False}

async def update_allowed_ips(allowed_ips: list, ip_check_enabled: bool):
    db = get_db()
    data = {
        "allowed_ips": allowed_ips,
        "ip_check_enabled": ip_check_enabled,
        "updated_at": datetime.utcnow()
    }
    existing = await db.ip_settings.find_one({})
    if existing:
        await db.ip_settings.update_one({}, {"$set": data})
    else:
        await db.ip_settings.insert_one(data)
    return await get_allowed_ips()

async def verify_ip(client_ip: str):
    db = get_db()
    settings = await db.ip_settings.find_one({})
    if not settings or not settings.get("ip_check_enabled", False):
        return True, "IP check disabled"
    allowed_ips = settings.get("allowed_ips", [])
    if not allowed_ips:
        return True, "No IPs configured"
    if client_ip in allowed_ips:
        return True, "IP verified"
    return False, f"Access denied. Your IP ({client_ip}) is not whitelisted."