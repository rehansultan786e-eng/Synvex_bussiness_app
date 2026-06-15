from app.database.connection import get_db
from app.models.schedule import ScheduleCreate, ScheduleUpdate
from bson import ObjectId
from datetime import datetime

def schedule_helper(schedule) -> dict:
    return {
        "id": str(schedule["_id"]),
        "schedule_name": schedule["schedule_name"],
        "department": schedule["department"],
        "shift_type": schedule["shift_type"],
        "start_time": schedule["start_time"],
        "end_time": schedule["end_time"],
        "grace_time": schedule["grace_time"],
        "required_hours": schedule["required_hours"],
        "created_at": schedule["created_at"]
    }

async def create_schedule(schedule_data: ScheduleCreate):
    db = get_db()
    existing = await db.schedules.find_one({
        "department": schedule_data.department,
        "shift_type": schedule_data.shift_type,
        "is_deleted": False
    })
    if existing:
        return None, "Schedule already exists for this department and shift"

    schedule = {
        **schedule_data.model_dump(),
        "is_deleted": False,
        "created_at": datetime.utcnow()
    }
    result = await db.schedules.insert_one(schedule)
    new_schedule = await db.schedules.find_one({"_id": result.inserted_id})
    return schedule_helper(new_schedule), None

async def get_all_schedules(department: str = None, shift_type: str = None):
    db = get_db()
    query = {"is_deleted": False}
    if department:
        query["department"] = department
    if shift_type:
        query["shift_type"] = shift_type
    schedules = await db.schedules.find(query).to_list(1000)
    return [schedule_helper(s) for s in schedules]

async def get_schedule_by_id(schedule_id: str):
    db = get_db()
    schedule = await db.schedules.find_one({"_id": ObjectId(schedule_id), "is_deleted": False})
    if schedule:
        return schedule_helper(schedule)
    return None

async def get_schedule_by_department(department: str):
    db = get_db()
    schedule = await db.schedules.find_one({"department": department, "is_deleted": False})
    if schedule:
        return schedule_helper(schedule)
    return None

async def update_schedule(schedule_id: str, schedule_data: ScheduleUpdate):
    db = get_db()
    update_data = {k: v for k, v in schedule_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    await db.schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": update_data})
    return await get_schedule_by_id(schedule_id)

async def delete_schedule(schedule_id: str):
    db = get_db()
    await db.schedules.update_one(
        {"_id": ObjectId(schedule_id)},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )
    return True