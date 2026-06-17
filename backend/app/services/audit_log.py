# app/services/audit_log.py
#
# Audit Log service (SRS 9.4 / FIN-10).
# log_action() is the single entry point other services/routes call to
# record a CRUD action. Logs are read-only and retained for 2+ years.

from app.database.connection import get_db
from datetime import datetime


def audit_log_helper(log) -> dict:
    return {
        "id": str(log["_id"]),
        "log_id": log["log_id"],
        "user_id": log["user_id"],
        "user_name": log["user_name"],
        "user_role": log["user_role"],
        "action": log["action"],
        "entity": log["entity"],
        "entity_id": log["entity_id"],
        "old_value": log.get("old_value"),
        "new_value": log.get("new_value"),
        "description": log.get("description"),
        "timestamp": log["timestamp"]
    }


async def generate_log_id():
    db = get_db()
    count = await db.audit_logs.count_documents({})
    return f"LOG-{count + 1:08d}"


def _make_json_safe(value):
    if value is None:
        return None
    if isinstance(value, dict):
        safe = {}
        for k, v in value.items():
            if k in ("password", "pdf_base64", "photo_base64", "face_images"):
                continue
            safe[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
        return safe
    return str(value)


async def log_action(
    user_id: str,
    user_name: str,
    user_role: str,
    action: str,
    entity: str,
    entity_id: str,
    old_value: dict = None,
    new_value: dict = None,
    description: str = None
):
    db = get_db()
    log_id = await generate_log_id()

    entry = {
        "log_id": log_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "old_value": _make_json_safe(old_value),
        "new_value": _make_json_safe(new_value),
        "description": description,
        "timestamp": datetime.utcnow()
    }
    await db.audit_logs.insert_one(entry)
    return True


async def get_all_audit_logs(
    entity: str = None,
    action: str = None,
    user_id: str = None,
    page: int = 1,
    page_size: int = 50
):
    db = get_db()
    query = {}
    if entity:
        query["entity"] = entity
    if action:
        query["action"] = action
    if user_id:
        query["user_id"] = user_id

    skip = (page - 1) * page_size
    total = await db.audit_logs.count_documents(query)
    logs = await db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(page_size).to_list(page_size)

    return {
        "logs": [audit_log_helper(l) for l in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


async def get_entity_history(entity: str, entity_id: str):
    db = get_db()
    logs = await db.audit_logs.find(
        {"entity": entity, "entity_id": entity_id}
    ).sort("timestamp", 1).to_list(1000)
    return [audit_log_helper(l) for l in logs]