from app.database.connection import get_db
from app.deepface_service.face_recognition import verify_face_from_base64
from app.services.schedule import get_schedule_by_department
from datetime import datetime, date
from bson import ObjectId

def attendance_helper(attendance) -> dict:
    return {
        "id": str(attendance["_id"]),
        "employee_id": attendance["employee_id"],
        "employee_name": attendance["employee_name"],
        "department": attendance["department"],
        "date": attendance["date"],
        "check_in": attendance.get("check_in"),
        "check_out": attendance.get("check_out"),
        "status": attendance["status"],
        "work_hours": attendance.get("work_hours")
    }

def calculate_status(check_in_time: str, schedule) -> str:
    if not schedule:
        return "present"
    try:
        check_in = datetime.strptime(check_in_time, "%H:%M:%S")
        schedule_start = datetime.strptime(schedule["start_time"], "%H:%M")
        grace = schedule["grace_time"]
        from datetime import timedelta
        late_threshold = schedule_start + timedelta(minutes=grace)
        if check_in <= late_threshold:
            return "present"
        else:
            return "late"
    except Exception:
        return "present"

def calculate_work_hours(check_in: str, check_out: str) -> float:
    try:
        fmt = "%H:%M:%S"
        ci = datetime.strptime(check_in, fmt)
        co = datetime.strptime(check_out, fmt)
        diff = (co - ci).total_seconds() / 3600
        return round(diff, 2)
    except Exception:
        return 0.0

async def mark_attendance(image_base64: str, mode: str = "checkin"):
    db = get_db()
    employee, error = await verify_face_from_base64(image_base64)
    if error:
        return None, error

    today = str(date.today())
    now = datetime.now().strftime("%H:%M:%S")

    existing = await db.attendance.find_one({
        "employee_id": employee["employee_id"],
        "date": today
    })

    schedule = await get_schedule_by_department(employee["department"])

    if mode == "checkin":
        if existing and existing.get("check_in"):
            return None, "Already checked in today"
        if not existing:
            status = calculate_status(now, schedule)
            attendance = {
                "employee_id": employee["employee_id"],
                "employee_name": employee["full_name"],
                "department": employee["department"],
                "date": today,
                "check_in": now,
                "check_out": None,
                "status": status,
                "work_hours": None,
                "created_at": datetime.utcnow()
            }
            result = await db.attendance.insert_one(attendance)
            new_att = await db.attendance.find_one({"_id": result.inserted_id})
            return attendance_helper(new_att), None
        else:
            await db.attendance.update_one(
                {"_id": existing["_id"]},
                {"$set": {"check_in": now}}
            )
            updated = await db.attendance.find_one({"_id": existing["_id"]})
            return attendance_helper(updated), None

    elif mode == "checkout":
        if not existing or not existing.get("check_in"):
            return None, "Please check in first"
        if existing.get("check_out"):
            return None, "Already checked out today"
        work_hours = calculate_work_hours(existing["check_in"], now)
        status = existing["status"]
        if schedule and work_hours < schedule["required_hours"] / 2:
            status = "half_day"
        await db.attendance.update_one(
            {"_id": existing["_id"]},
            {"$set": {"check_out": now, "work_hours": work_hours, "status": status}}
        )
        updated = await db.attendance.find_one({"_id": existing["_id"]})
        return attendance_helper(updated), None

    return None, "Invalid mode"

async def get_attendance_by_date(date_str: str, department: str = None):
    db = get_db()
    query = {"date": date_str}
    if department:
        query["department"] = department
    records = await db.attendance.find(query).to_list(1000)
    return [attendance_helper(r) for r in records]

async def get_employee_attendance_history(employee_id: str, month: int = None, year: int = None):
    db = get_db()
    query = {"employee_id": employee_id}
    if month and year:
        prefix = f"{year}-{month:02d}"
        query["date"] = {"$regex": f"^{prefix}"}
    records = await db.attendance.find(query).to_list(1000)
    return [attendance_helper(r) for r in records]

async def correct_attendance(correction_data):
    db = get_db()
    update_data = {
        "status": correction_data.status,
        "corrected": True,
        "correction_reason": correction_data.reason,
        "updated_at": datetime.utcnow()
    }
    if correction_data.check_in:
        update_data["check_in"] = correction_data.check_in
    if correction_data.check_out:
        update_data["check_out"] = correction_data.check_out
        if correction_data.check_in:
            update_data["work_hours"] = calculate_work_hours(
                correction_data.check_in, correction_data.check_out
            )
    await db.attendance.update_one(
        {"employee_id": correction_data.employee_id, "date": correction_data.date},
        {"$set": update_data},
        upsert=True
    )
    return True