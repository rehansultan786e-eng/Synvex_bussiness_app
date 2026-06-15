from app.database.connection import get_db
from datetime import date, datetime

async def get_dashboard_stats():
    db = get_db()
    today = str(date.today())

    total_employees = await db.employees.count_documents({"is_deleted": False, "status": "active"})
    total_departments = await db.departments.count_documents({"is_deleted": False})
    present_today = await db.attendance.count_documents({"date": today, "status": "present"})
    late_today = await db.attendance.count_documents({"date": today, "status": "late"})
    on_leave_today = await db.attendance.count_documents({"date": today, "status": "on_leave"})
    absent_today = total_employees - present_today - late_today - on_leave_today
    pending_leaves = await db.leave_requests.count_documents({"status": "pending"})
    unread_notifications = await db.notifications.count_documents({"is_read": False})

    return {
        "total_employees": total_employees,
        "total_departments": total_departments,
        "present_today": present_today,
        "late_today": late_today,
        "absent_today": max(absent_today, 0),
        "on_leave_today": on_leave_today,
        "pending_leaves": pending_leaves,
        "unread_notifications": unread_notifications
    }

async def get_monthly_attendance_trend(year: int, month: int):
    db = get_db()
    prefix = f"{year}-{month:02d}"
    pipeline = [
        {"$match": {"date": {"$regex": f"^{prefix}"}}},
        {"$group": {
            "_id": "$date",
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
            "late": {"$sum": {"$cond": [{"$eq": ["$status", "late"]}, 1, 0]}},
            "absent": {"$sum": {"$cond": [{"$eq": ["$status", "absent"]}, 1, 0]}},
            "on_leave": {"$sum": {"$cond": [{"$eq": ["$status", "on_leave"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    result = await db.attendance.aggregate(pipeline).to_list(31)
    return result

async def get_department_attendance_stats():
    db = get_db()
    today = str(date.today())
    departments = await db.departments.find({"is_deleted": False}).to_list(100)
    result = []
    for dept in departments:
        total = await db.employees.count_documents({
            "department": dept["department_name"],
            "is_deleted": False
        })
        present = await db.attendance.count_documents({
            "department": dept["department_name"],
            "date": today,
            "status": {"$in": ["present", "late"]}
        })
        result.append({
            "department": dept["department_name"],
            "total_employees": total,
            "present_today": present,
            "attendance_rate": round((present / total * 100), 1) if total > 0 else 0
        })
    return result