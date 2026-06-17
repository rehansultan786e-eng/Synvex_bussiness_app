# app/services/leave.py
#
# Leave service (SRS 6.4).
#
# Workflow (SRS 6.4.2):
# 1. Employee submits leave request: type, from_date, to_date, reason.
# 2. Reporting Manager receives notification and approves/rejects.
# 3. HR Manager is notified of the final decision.
# 4. Leave balance is deducted automatically on approval.
# 5. Approved leave appears in the attendance calendar (as 'on_leave').

from app.database.connection import get_db
from app.models.leave import LeaveRequestCreate, LeaveUpdate
from app.services.leave_balance import has_sufficient_balance, deduct_leave_balance, restore_leave_balance
from bson import ObjectId
from datetime import datetime, date, timedelta


def leave_helper(leave) -> dict:
    return {
        "id": str(leave["_id"]),
        "employee_id": leave["employee_id"],
        "employee_name": leave["employee_name"],
        "leave_type": leave["leave_type"],
        "from_date": leave["from_date"],
        "to_date": leave["to_date"],
        "total_days": leave["total_days"],
        "reason": leave["reason"],
        "status": leave["status"],
        "admin_comment": leave.get("admin_comment"),
        "approved_by": leave.get("approved_by"),
        "created_at": leave["created_at"],
        "updated_at": leave.get("updated_at")
    }


def _calculate_total_days(from_date: date, to_date: date) -> int:
    """Inclusive day count between from_date and to_date."""
    return (to_date - from_date).days + 1


def _date_range(from_date: date, to_date: date):
    """Yields each date in the inclusive range, used to mark attendance per day."""
    current = from_date
    while current <= to_date:
        yield current
        current += timedelta(days=1)


async def create_leave_request(leave_data: LeaveRequestCreate):
    """SRS 6.4.2 step 1: Employee submits a leave request."""
    db = get_db()

    employee = await db.employees.find_one({
        "employee_id": leave_data.employee_id,
        "is_deleted": False
    })
    if not employee:
        return None, "Employee not found"

    if leave_data.to_date < leave_data.from_date:
        return None, "to_date cannot be before from_date"

    total_days = _calculate_total_days(leave_data.from_date, leave_data.to_date)

    # Prevent overlapping leave requests
    overlapping = await db.leave_requests.find_one({
        "employee_id": leave_data.employee_id,
        "status": {"$in": ["pending", "approved"]},
        "from_date": {"$lte": str(leave_data.to_date)},
        "to_date": {"$gte": str(leave_data.from_date)}
    })
    if overlapping:
        return None, "An overlapping leave request already exists for this period"

    # Check balance before allowing submission
    has_balance, balance_error = await has_sufficient_balance(
        leave_data.employee_id, leave_data.leave_type, total_days
    )
    if not has_balance:
        return None, balance_error

    leave = {
        "employee_id": leave_data.employee_id,
        "employee_name": employee["full_name"],
        "leave_type": leave_data.leave_type,
        "from_date": str(leave_data.from_date),
        "to_date": str(leave_data.to_date),
        "total_days": total_days,
        "reason": leave_data.reason,
        "status": "pending",
        "admin_comment": None,
        "approved_by": None,
        "created_at": datetime.utcnow()
    }
    result = await db.leave_requests.insert_one(leave)
    new_leave = await db.leave_requests.find_one({"_id": result.inserted_id})

    # SRS 6.4.2 step 2: Notify Reporting Manager (fallback to HR Manager/CEO if no manager set)
    from app.services.notification import create_notification

    notify_targets = []
    if employee.get("reporting_manager"):
        manager = await db.employees.find_one({"employee_id": employee["reporting_manager"], "is_deleted": False})
        if manager:
            manager_user = await db.users.find_one({"email": manager["email"]})
            if manager_user:
                notify_targets.append(str(manager_user["_id"]))

    if not notify_targets:
        hr_users = await db.users.find({"role": {"$in": ["super_admin", "hr_manager"]}}).to_list(20)
        notify_targets = [str(u["_id"]) for u in hr_users]

    for target_id in notify_targets:
        await create_notification(
            user_id=target_id,
            message=f"{employee['full_name']} requested {leave_data.leave_type} leave from {leave_data.from_date} to {leave_data.to_date} ({total_days} day(s)).",
            notif_type="leave_request"
        )

    return leave_helper(new_leave), None


async def get_all_leave_requests(status: str = None, leave_type: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if leave_type:
        query["leave_type"] = leave_type
    leaves = await db.leave_requests.find(query).sort("created_at", -1).to_list(1000)
    return [leave_helper(l) for l in leaves]


async def get_employee_leave_requests(employee_id: str):
    db = get_db()
    leaves = await db.leave_requests.find({
        "employee_id": employee_id
    }).sort("created_at", -1).to_list(100)
    return [leave_helper(l) for l in leaves]


async def update_leave_status(leave_id: str, leave_update: LeaveUpdate, approved_by: str):
    """
    SRS 6.4.2 steps 3-5:
    - Reporting Manager / HR Manager / CEO approves or rejects.
    - On approval: leave balance deducted, attendance marked 'on_leave' for each day,
      HR Manager notified of the final decision, employee notified.
    """
    db = get_db()
    leave = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        return None, "Leave request not found"

    if leave["status"] != "pending":
        return None, f"Leave request is already {leave['status']}"

    await db.leave_requests.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {
            "status": leave_update.status,
            "admin_comment": leave_update.admin_comment,
            "approved_by": approved_by,
            "updated_at": datetime.utcnow()
        }}
    )

    if leave_update.status == "approved":
        # SRS 6.4.2 step 4: Deduct leave balance automatically
        await deduct_leave_balance(leave["employee_id"], leave["leave_type"], leave["total_days"])

        # SRS 6.4.2 step 5: Mark attendance as 'on_leave' for each day in range
        from_date = date.fromisoformat(leave["from_date"])
        to_date = date.fromisoformat(leave["to_date"])

        for day in _date_range(from_date, to_date):
            day_str = str(day)
            existing_att = await db.attendance.find_one({
                "employee_id": leave["employee_id"],
                "date": day_str
            })
            if not existing_att:
                employee = await db.employees.find_one({"employee_id": leave["employee_id"]})
                await db.attendance.insert_one({
                    "employee_id": leave["employee_id"],
                    "employee_name": leave["employee_name"],
                    "department": employee["department"] if employee else "",
                    "date": day_str,
                    "check_in": None,
                    "check_out": None,
                    "status": "on_leave",
                    "work_hours": None,
                    "ip_address": None,
                    "device_info": None,
                    "manual_override": False,
                    "override_reason": None,
                    "corrected": False,
                    "created_at": datetime.utcnow()
                })
            else:
                await db.attendance.update_one(
                    {"_id": existing_att["_id"]},
                    {"$set": {"status": "on_leave"}}
                )

    # SRS 6.4.2 step 3: Notify HR Manager of the final decision (if HR wasn't the approver)
    from app.services.notification import create_notification
    hr_users = await db.users.find({"role": {"$in": ["super_admin", "hr_manager"]}}).to_list(20)
    for u in hr_users:
        if str(u["_id"]) != approved_by:
            await create_notification(
                user_id=str(u["_id"]),
                message=f"Leave request for {leave['employee_name']} ({leave['leave_type']}, {leave['from_date']} to {leave['to_date']}) has been {leave_update.status}.",
                notif_type="leave_decision"
            )

    # Notify the employee of the decision
    employee = await db.employees.find_one({"employee_id": leave["employee_id"]})
    if employee:
        employee_user = await db.users.find_one({"email": employee["email"]})
        notify_id = str(employee_user["_id"]) if employee_user else leave["employee_id"]
        await create_notification(
            user_id=notify_id,
            message=f"Your {leave['leave_type']} leave request ({leave['from_date']} to {leave['to_date']}) has been {leave_update.status}.",
            notif_type="leave_decision"
        )

    updated = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    return leave_helper(updated), None


async def cancel_leave_request(leave_id: str, employee_id: str):
    """Employee cancels their own pending or approved (future) leave request."""
    db = get_db()
    leave = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        return None, "Leave request not found"

    if leave["employee_id"] != employee_id:
        return None, "You can only cancel your own leave requests"

    if leave["status"] not in ["pending", "approved"]:
        return None, f"Cannot cancel a leave request that is {leave['status']}"

    # If it was approved, restore the deducted balance
    if leave["status"] == "approved":
        await restore_leave_balance(leave["employee_id"], leave["leave_type"], leave["total_days"])

        from_date = date.fromisoformat(leave["from_date"])
        to_date = date.fromisoformat(leave["to_date"])
        for day in _date_range(from_date, to_date):
            await db.attendance.delete_one({
                "employee_id": leave["employee_id"],
                "date": str(day),
                "status": "on_leave"
            })

    await db.leave_requests.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
    )
    updated = await db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    return leave_helper(updated), None