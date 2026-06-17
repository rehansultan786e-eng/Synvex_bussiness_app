# app/services/attendance.py
#
# Attendance service (SRS 6.3).
#
# Attendance Rules (SRS 6.3.2, configurable via schedule):
# - Office Start Time: e.g. 9:00 AM
# - Grace Period: e.g. 15 minutes (arrival before start+grace = On Time)
# - Half Day: check-in after 12:00 PM OR check-out before 1:00 PM
# - Absent: no check-in recorded by end of day
#
# On failed face match (3 attempts), the frontend should call the
# manual-override endpoint instead of retrying indefinitely.

from app.database.connection import get_db
from app.deepface_service.face_recognition import verify_face_from_base64
from app.services.schedule import get_schedule_by_department
from datetime import datetime, date, timedelta
from bson import ObjectId

# SRS 6.3.2 defaults — used when a schedule doesn't define explicit half-day cutoffs
DEFAULT_HALF_DAY_CHECKIN_CUTOFF = "12:00:00"   # check-in after this time -> half day
DEFAULT_HALF_DAY_CHECKOUT_CUTOFF = "13:00:00"  # check-out before this time -> half day


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
        "work_hours": attendance.get("work_hours"),
        "ip_address": attendance.get("ip_address"),
        "device_info": attendance.get("device_info"),
        "manual_override": attendance.get("manual_override", False),
        "override_reason": attendance.get("override_reason"),
        "corrected": attendance.get("corrected", False)
    }


def calculate_checkin_status(check_in_time: str, schedule) -> str:
    """
    Determines initial status at check-in time:
    - 'half_day' if check-in is after the half-day cutoff (default 12:00 PM)
    - 'late' if check-in is after grace period but before half-day cutoff
    - 'present' if check-in is within grace period
    """
    try:
        check_in = datetime.strptime(check_in_time, "%H:%M:%S")
        half_day_cutoff = datetime.strptime(DEFAULT_HALF_DAY_CHECKIN_CUTOFF, "%H:%M:%S")

        if check_in > half_day_cutoff:
            return "half_day"

        if not schedule:
            return "present"

        schedule_start = datetime.strptime(schedule["start_time"], "%H:%M")
        grace = schedule["grace_time"]
        late_threshold = schedule_start + timedelta(minutes=grace)

        if check_in.time() <= late_threshold.time():
            return "present"
        return "late"
    except Exception:
        return "present"


def apply_checkout_half_day_rule(check_out_time: str, current_status: str) -> str:
    """
    SRS 6.3.2: if check-out is before 1:00 PM, status becomes half_day,
    regardless of the check-in status (unless already half_day or absent).
    """
    try:
        check_out = datetime.strptime(check_out_time, "%H:%M:%S")
        checkout_cutoff = datetime.strptime(DEFAULT_HALF_DAY_CHECKOUT_CUTOFF, "%H:%M:%S")
        if check_out < checkout_cutoff:
            return "half_day"
        return current_status
    except Exception:
        return current_status


def calculate_work_hours(check_in: str, check_out: str) -> float:
    try:
        fmt = "%H:%M:%S"
        ci = datetime.strptime(check_in, fmt)
        co = datetime.strptime(check_out, fmt)
        diff = (co - ci).total_seconds() / 3600
        return round(diff, 2)
    except Exception:
        return 0.0


async def mark_attendance(
    image_base64: str,
    mode: str = "checkin",
    ip_address: str = None,
    device_info: str = None
):
    """
    SRS 6.3.2: On successful face match, attendance is marked with
    timestamp, IP address, and device info.
    """
    db = get_db()
    employee, error = await verify_face_from_base64(image_base64)

    if error:
        # Track failed attempts for this employee today (face not recognized case
        # doesn't know which employee, so this only applies when employee context
        # is available; the route layer tracks attempts per-session/IP instead).
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
            status = calculate_checkin_status(now, schedule)
            attendance = {
                "employee_id": employee["employee_id"],
                "employee_name": employee["full_name"],
                "department": employee["department"],
                "date": today,
                "check_in": now,
                "check_out": None,
                "status": status,
                "work_hours": None,
                "ip_address": ip_address,
                "device_info": device_info,
                "manual_override": False,
                "override_reason": None,
                "corrected": False,
                "created_at": datetime.utcnow()
            }
            result = await db.attendance.insert_one(attendance)
            new_att = await db.attendance.find_one({"_id": result.inserted_id})
            return attendance_helper(new_att), None
        else:
            status = calculate_checkin_status(now, schedule)
            await db.attendance.update_one(
                {"_id": existing["_id"]},
                {"$set": {"check_in": now, "status": status, "ip_address": ip_address, "device_info": device_info}}
            )
            updated = await db.attendance.find_one({"_id": existing["_id"]})
            return attendance_helper(updated), None

    elif mode == "checkout":
        if not existing or not existing.get("check_in"):
            return None, "Please check in first"
        if existing.get("check_out"):
            return None, "Already checked out today"

        work_hours = calculate_work_hours(existing["check_in"], now)
        status = apply_checkout_half_day_rule(now, existing["status"])

        await db.attendance.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "check_out": now,
                "work_hours": work_hours,
                "status": status,
                "ip_address": ip_address or existing.get("ip_address"),
                "device_info": device_info or existing.get("device_info")
            }}
        )
        updated = await db.attendance.find_one({"_id": existing["_id"]})
        return attendance_helper(updated), None

    return None, "Invalid mode"


async def manual_override_attendance(employee_id: str, mode: str, reason: str, marked_by: str):
    """
    SRS 6.3.2: After 3 failed face-match attempts, HR Manager can manually
    mark check-in/check-out with a reason.
    """
    db = get_db()
    employee = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if not employee:
        return None, "Employee not found"

    today = str(date.today())
    now = datetime.now().strftime("%H:%M:%S")

    existing = await db.attendance.find_one({"employee_id": employee_id, "date": today})
    schedule = await get_schedule_by_department(employee["department"])

    if mode == "checkin":
        if existing and existing.get("check_in"):
            return None, "Already checked in today"
        status = calculate_checkin_status(now, schedule)
        record = {
            "employee_id": employee_id,
            "employee_name": employee["full_name"],
            "department": employee["department"],
            "date": today,
            "check_in": now,
            "check_out": None,
            "status": status,
            "work_hours": None,
            "ip_address": None,
            "device_info": None,
            "manual_override": True,
            "override_reason": reason,
            "corrected": False,
            "created_at": datetime.utcnow()
        }
        if existing:
            await db.attendance.update_one({"_id": existing["_id"]}, {"$set": record})
            result_id = existing["_id"]
        else:
            result = await db.attendance.insert_one(record)
            result_id = result.inserted_id
        updated = await db.attendance.find_one({"_id": result_id})
        return attendance_helper(updated), None

    elif mode == "checkout":
        if not existing or not existing.get("check_in"):
            return None, "Employee has not checked in today"
        if existing.get("check_out"):
            return None, "Already checked out today"
        work_hours = calculate_work_hours(existing["check_in"], now)
        status = apply_checkout_half_day_rule(now, existing["status"])
        await db.attendance.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "check_out": now,
                "work_hours": work_hours,
                "status": status,
                "manual_override": True,
                "override_reason": reason
            }}
        )
        updated = await db.attendance.find_one({"_id": existing["_id"]})
        return attendance_helper(updated), None

    return None, "Invalid mode"


async def auto_mark_absentees():
    """
    SRS 6.3.2: Absent = no check-in recorded by end of day.
    Intended to run once daily (e.g. via a scheduled job at end-of-day)
    to create 'absent' records for active employees with no attendance
    and no approved leave for today.
    """
    db = get_db()
    today = str(date.today())

    active_employees = await db.employees.find({"is_deleted": False, "status": "active"}).to_list(10000)
    marked_count = 0

    for emp in active_employees:
        existing = await db.attendance.find_one({"employee_id": emp["employee_id"], "date": today})
        if existing:
            continue  # already has a check-in, on_leave, or other record for today

        await db.attendance.insert_one({
            "employee_id": emp["employee_id"],
            "employee_name": emp["full_name"],
            "department": emp["department"],
            "date": today,
            "check_in": None,
            "check_out": None,
            "status": "absent",
            "work_hours": None,
            "ip_address": None,
            "device_info": None,
            "manual_override": False,
            "override_reason": None,
            "corrected": False,
            "created_at": datetime.utcnow()
        })
        marked_count += 1

    return marked_count


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


async def get_monthly_attendance_summary(employee_id: str, month: int, year: int):
    """SRS 6.3.3: Monthly attendance summary per employee."""
    records = await get_employee_attendance_history(employee_id, month, year)
    summary = {"present": 0, "late": 0, "half_day": 0, "absent": 0, "on_leave": 0}
    for r in records:
        status = r["status"]
        if status in summary:
            summary[status] += 1
    summary["total_days_recorded"] = len(records)
    return summary


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