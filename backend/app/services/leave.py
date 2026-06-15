from app.database.connection import get_db
from app.models.leave import LeaveRequest, LeaveUpdate
from bson import ObjectId
from datetime import datetime, date

def leave_helper(leave) -> dict:
    return {
        "id": str(leave["_id"]),
        "employee_id": leave["employee_id"],
        "employee_name": leave["employee_name"],
        "leave_date": leave["leave_date"],
        "leave_type": leave["leave_type"],
        "reason": leave["reason"],
        "status": leave["status"],
        "admin_comment": leave.get("admin_comment"),
        "created_at": leave["created_at"]
    }

async def create_leave_request(leave_data: LeaveRequest):
    db = get_db()
    employee = await db.employees.find_one({
        "employee_id": leave_data.employee_id,
        "is_deleted": False
    })
    if not employee:
        return None, "Employee not found"

    existing = await db.leave_requests.find_one({
        "employee_id": leave_data.employee_id,
        "leave_date": leave_data.leave_date,
        "status": {"$in": ["pending", "approved"]}
    })
    if existing:
        return None, "Leave request already exists for this date"

    leave = {
        "employee_id": leave_data.employee_id,
        "employee_name": employee["full_name"],
        "leave_date": leave_data.leave_date,
        "leave_type": leave_data.leave_type,
        "reason": leave_data.reason,
        "status": "pending",
        "admin_comment": None,
        "created_at": datetime.utcnow()
    }
    result = await db.leave_requests.insert_one(leave)

    # Create notification for admin
    notification = {
        "type": "leave_request",
        "title": "New Leave Request",
        "message": f"{employee['full_name']} requested {leave_data.leave_type} on {leave_data.leave_date}",
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    await db.notifications.insert_one(notification)

    new_leave = await db.leave_requests.find_one({"_id": result.inserted_id})
    return leave_helper(new_leave), None

async def get_all_leave_requests(status: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    leaves = await db.leave_requests.find(query).sort("created_at", -1).to_list(1000)
    return [leave_helper(l) for l in leaves]

async def get_employee_leave_requests(employee_id: str):
    db = get_db()
    today = str(date.today())
    leaves = await db.leave_requests.find({
        "employee_id": employee_id
    }).sort("created_at", -1).to_list(100)
    return [leave_helper(l) for l in leaves]

async def update_leave_status(leave_id: str, leave_update: LeaveUpdate):
    db = get_db()
    leave = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        return None, "Leave request not found"

    await db.leave_requests.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {
            "status": leave_update.status,
            "admin_comment": leave_update.admin_comment,
            "updated_at": datetime.utcnow()
        }}
    )

    # If approved, mark attendance as on_leave
    if leave_update.status == "approved":
        existing_att = await db.attendance.find_one({
            "employee_id": leave["employee_id"],
            "date": leave["leave_date"]
        })
        if not existing_att:
            await db.attendance.insert_one({
                "employee_id": leave["employee_id"],
                "employee_name": leave["employee_name"],
                "department": "",
                "date": leave["leave_date"],
                "check_in": None,
                "check_out": None,
                "status": "on_leave",
                "work_hours": None,
                "created_at": datetime.utcnow()
            })
        else:
            await db.attendance.update_one(
                {"_id": existing_att["_id"]},
                {"$set": {"status": "on_leave"}}
            )

    updated = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    return leave_helper(updated), None