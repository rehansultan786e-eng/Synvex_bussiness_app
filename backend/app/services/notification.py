from app.database.connection import get_db
from bson import ObjectId
from datetime import datetime


def notification_helper(notification) -> dict:
    return {
        "id": str(notification["_id"]),
        "user_id": notification.get("user_id"),
        "type": notification["type"],
        "title": notification["title"],
        "message": notification["message"],
        "is_read": notification["is_read"],
        "created_at": notification["created_at"]
    }


async def create_notification(user_id: str, message: str, notif_type: str, title: str = None):
    """
    Creates a per-user in-app notification (SRS Section 8.1).
    If title is not provided, a default title is derived from notif_type.
    """
    db = get_db()

    default_titles = {
        "commission_status": "Commission Status Updated",
        "meeting_ceo_required": "Meeting Requires Your Participation",
        "lead_assigned": "New Lead Assigned",
        "milestone_due": "Milestone Due Soon",
        "milestone_overdue": "Milestone Overdue",
        "payroll_approved": "Payslip Ready",
        "leave_request": "New Leave Request",
        "leave_decision": "Leave Request Update",
        "asset_assigned": "New Asset Assigned",
        "asset_warranty": "Asset Warranty Expiring",
        "employee_onboarded": "New Employee Onboarded",
        "expense_approval": "Expense Pending Approval",
    }

    notification = {
        "user_id": user_id,
        "type": notif_type,
        "title": title or default_titles.get(notif_type, "Notification"),
        "message": message,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    result = await db.notifications.insert_one(notification)
    new_notification = await db.notifications.find_one({"_id": result.inserted_id})
    return notification_helper(new_notification)


async def get_all_notifications(user_id: str, is_read: bool = None):
    db = get_db()
    query = {"user_id": user_id}
    if is_read is not None:
        query["is_read"] = is_read
    notifications = await db.notifications.find(query).sort("created_at", -1).to_list(100)
    return [notification_helper(n) for n in notifications]


async def mark_notification_read(notification_id: str, user_id: str):
    db = get_db()
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": user_id},
        {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
    )
    return True


async def mark_all_read(user_id: str):
    db = get_db()
    await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
    )
    return True


async def get_unread_count(user_id: str):
    db = get_db()
    count = await db.notifications.count_documents({"user_id": user_id, "is_read": False})
    return count