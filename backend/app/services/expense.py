from app.database.connection import get_db
from app.models.expense import ExpenseCreate, ExpenseStatusUpdate
from datetime import datetime
from bson import ObjectId


# FIN-06: Expenses above this threshold require CEO approval. Configurable.
EXPENSE_APPROVAL_THRESHOLD = 50000.0  # in base currency (e.g., PKR), adjustable via settings


def expense_helper(expense) -> dict:
    return {
        "id": str(expense["_id"]),
        "expense_id": expense["expense_id"],
        "category": expense["category"],
        "amount": expense["amount"],
        "expense_date": str(expense["expense_date"]),
        "description": expense["description"],
        "vendor_name": expense.get("vendor_name"),
        "has_receipt": bool(expense.get("receipt_base64")),
        "status": expense["status"],
        "submitted_by": expense["submitted_by"],
        "submitted_by_name": expense["submitted_by_name"],
        "approved_by": expense.get("approved_by"),
        "comments": expense.get("comments"),
        "requires_ceo_approval": expense["requires_ceo_approval"],
        "created_at": expense["created_at"],
        "updated_at": expense.get("updated_at")
    }


async def generate_expense_id():
    db = get_db()
    count = await db.expenses.count_documents({})
    return f"EXP-{count + 1:05d}"


async def create_expense(expense_data: ExpenseCreate, submitted_by: str, submitted_by_name: str):
    db = get_db()
    expense_id = await generate_expense_id()

    requires_ceo = expense_data.amount > EXPENSE_APPROVAL_THRESHOLD

    expense = {
        "expense_id": expense_id,
        "category": expense_data.category,
        "amount": expense_data.amount,
        "expense_date": str(expense_data.expense_date),
        "description": expense_data.description,
        "vendor_name": expense_data.vendor_name,
        "receipt_base64": expense_data.receipt_base64.split(',')[-1] if expense_data.receipt_base64 else None,
        "status": "Pending",
        "submitted_by": submitted_by,
        "submitted_by_name": submitted_by_name,
        "approved_by": None,
        "comments": None,
        "requires_ceo_approval": requires_ceo,
        "is_deleted": False,
        "created_at": datetime.utcnow()
    }
    result = await db.expenses.insert_one(expense)
    new_expense = await db.expenses.find_one({"_id": result.inserted_id})

    # SRS notification trigger: "Expense submitted for approval" -> Finance Manager / CEO
    from app.services.notification import create_notification
    target_roles = ["super_admin"] if requires_ceo else ["super_admin", "finance_manager"]
    approvers = await db.users.find({"role": {"$in": target_roles}}).to_list(20)
    for approver in approvers:
        await create_notification(
            user_id=str(approver["_id"]),
            message=f"New expense {expense_id} ({expense_data.category}) of {expense_data.amount} submitted by {submitted_by_name} requires approval.",
            notif_type="expense_approval"
        )

    return expense_helper(new_expense)


async def get_all_expenses(status: str = None, category: str = None, submitted_by: str = None):
    db = get_db()
    query = {"is_deleted": False}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if submitted_by:
        query["submitted_by"] = submitted_by

    expenses = await db.expenses.find(query).sort("created_at", -1).to_list(1000)
    return [expense_helper(e) for e in expenses]


async def get_expense_by_id(expense_id: str):
    db = get_db()
    expense = await db.expenses.find_one({"expense_id": expense_id, "is_deleted": False})
    if expense:
        return expense_helper(expense)
    return None


async def get_expense_receipt_bytes(expense_id: str):
    db = get_db()
    expense = await db.expenses.find_one({"expense_id": expense_id, "is_deleted": False})
    if not expense or not expense.get("receipt_base64"):
        return None
    import base64
    return base64.b64decode(expense["receipt_base64"])


async def update_expense_status(expense_id: str, status_update: ExpenseStatusUpdate, approved_by: str, approver_role: str):
    """
    FIN-06: Finance Manager can approve standard expenses;
    CEO (super_admin) approves expenses requiring CEO approval (above threshold).
    """
    db = get_db()
    expense = await db.expenses.find_one({"expense_id": expense_id, "is_deleted": False})
    if not expense:
        return None, "Expense not found"

    if expense["status"] != "Pending":
        return None, f"Expense is already {expense['status']}"

    if expense["requires_ceo_approval"] and approver_role != "super_admin":
        return None, "This expense requires CEO approval"

    if not expense["requires_ceo_approval"] and approver_role not in ["super_admin", "finance_manager"]:
        return None, "Only Finance Manager or CEO can approve expenses"

    update_data = {
        "status": status_update.status,
        "approved_by": approved_by,
        "comments": status_update.comments,
        "updated_at": datetime.utcnow()
    }
    await db.expenses.update_one({"expense_id": expense_id}, {"$set": update_data})
    updated = await db.expenses.find_one({"expense_id": expense_id})

    # Notify the submitter of the decision
    from app.services.notification import create_notification
    await create_notification(
        user_id=expense["submitted_by"],
        message=f"Your expense {expense_id} ({expense['category']}) has been {status_update.status.lower()}.",
        notif_type="expense_approval"
    )

    return expense_helper(updated), None


async def get_expense_breakdown(year: int = None, month: int = None):
    """FIN: Expense Breakdown report — by category, by month."""
    db = get_db()
    query = {"is_deleted": False, "status": "Approved"}

    expenses = await db.expenses.find(query).to_list(10000)

    breakdown = {}
    for e in expenses:
        exp_date = e["expense_date"]
        exp_year, exp_month = int(exp_date[:4]), int(exp_date[5:7])

        if year and exp_year != year:
            continue
        if month and exp_month != month:
            continue

        category = e["category"]
        breakdown[category] = breakdown.get(category, 0) + e["amount"]

    total = sum(breakdown.values())
    return {
        "breakdown": breakdown,
        "total": total,
        "year": year,
        "month": month
    }