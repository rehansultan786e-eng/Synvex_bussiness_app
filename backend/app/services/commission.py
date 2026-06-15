from app.database.connection import get_db
from app.models.commission import CommissionCreate, CommissionStatusUpdate, CommissionRateOverride
from datetime import datetime, date


def commission_helper(commission) -> dict:
    return {
        "id": str(commission["_id"]),
        "commission_id": commission["commission_id"],
        "lead_id": commission["lead_id"],
        "sales_rep_id": commission["sales_rep_id"],
        "sales_rep_name": commission["sales_rep_name"],
        "contract_value": commission["contract_value"],
        "rate": commission["rate"],
        "amount": commission["amount"],
        "status": commission["status"],
        "splits": commission.get("splits"),
        "approved_by": commission.get("approved_by"),
        "paid_date": commission.get("paid_date"),
        "comments": commission.get("comments"),
        "created_at": commission["created_at"],
        "updated_at": commission.get("updated_at")
    }


async def generate_commission_id():
    db = get_db()
    count = await db.commissions.count_documents({})
    return f"COMM-{count + 1:05d}"


async def get_default_commission_rate(sales_rep_id: str) -> float:
    """Fetches the sales rep's default commission percentage from their user profile."""
    db = get_db()
    from bson import ObjectId
    try:
        user = await db.users.find_one({"_id": ObjectId(sales_rep_id)})
    except Exception:
        user = None
    if user and user.get("commission_rate"):
        return user["commission_rate"]
    return 5.0  # SRS default example: 5%


async def create_commission_for_won_lead(lead_id: str):
    """
    Called automatically when a Lead status transitions to "Won" (SRS 3.2.1).
    Commission Amount = Contract Value x Commission Rate (%)
    Contract value is taken from the lead's estimated_value at this stage;
    Finance module will create the formal Contract record separately.
    """
    db = get_db()

    lead = await db.leads.find_one({"lead_id": lead_id, "is_deleted": False})
    if not lead:
        return None, "Lead not found"

    existing = await db.commissions.find_one({"lead_id": lead_id})
    if existing:
        return commission_helper(existing), None

    rate = await get_default_commission_rate(lead["sales_rep_id"])
    contract_value = lead["estimated_value"]
    amount = round(contract_value * (rate / 100), 2)

    commission_id = await generate_commission_id()

    commission = {
        "commission_id": commission_id,
        "lead_id": lead_id,
        "sales_rep_id": lead["sales_rep_id"],
        "sales_rep_name": lead["sales_rep_name"],
        "contract_value": contract_value,
        "rate": rate,
        "amount": amount,
        "status": "Pending",
        "splits": None,
        "approved_by": None,
        "paid_date": None,
        "comments": None,
        "created_at": datetime.utcnow()
    }
    result = await db.commissions.insert_one(commission)
    new_commission = await db.commissions.find_one({"_id": result.inserted_id})
    return commission_helper(new_commission), None


async def override_commission_rate(commission_id: str, override: CommissionRateOverride, updated_by_role: str):
    """Only HR Manager or CEO (super_admin) can override commission rate per deal (SRS 3.3.1)."""
    if updated_by_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can override commission rate"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    if commission["status"] in ["Paid"]:
        return None, "Cannot modify a commission that has already been paid"

    new_amount = round(commission["contract_value"] * (override.rate / 100), 2)

    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {"rate": override.rate, "amount": new_amount, "updated_at": datetime.utcnow()}}
    )
    updated = await db.commissions.find_one({"commission_id": commission_id})
    return commission_helper(updated), None


async def update_commission_status(commission_id: str, status_update: CommissionStatusUpdate, updated_by: str, updated_by_role: str):
    """
    Commission Status Lifecycle (SRS 3.3.2):
    - Pending -> Approved   : CEO or Finance Manager
    - Approved -> Paid       : Finance Manager marks as paid
    - Any -> On Hold          : CEO or Finance Manager (dispute/cancellation)

    SAL-06: Sends an in-app notification to the Sales Rep when status changes.
    """
    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    new_status = status_update.status
    current_status = commission["status"]

    if updated_by_role not in ["super_admin", "finance_manager"]:
        return None, "Only CEO or Finance Manager can change commission status"

    valid_transitions = {
        "Pending": ["Approved", "On Hold"],
        "Approved": ["Paid", "On Hold"],
        "On Hold": ["Pending", "Approved"],
        "Paid": []
    }

    if new_status not in valid_transitions.get(current_status, []):
        return None, f"Invalid status transition from {current_status} to {new_status}"

    update_data = {
        "status": new_status,
        "comments": status_update.comments,
        "updated_at": datetime.utcnow()
    }

    if new_status == "Approved":
        update_data["approved_by"] = updated_by
    if new_status == "Paid":
        update_data["paid_date"] = str(date.today())

    await db.commissions.update_one({"commission_id": commission_id}, {"$set": update_data})
    updated = await db.commissions.find_one({"commission_id": commission_id})

    # SAL-06: Notify the Sales Rep about the status change
    from app.services.notification import create_notification
    await create_notification(
        user_id=commission["sales_rep_id"],
        message=f"Your commission {commission_id} for lead {commission['lead_id']} status changed from {current_status} to {new_status}.",
        notif_type="commission_status"
    )

    return commission_helper(updated), None


async def get_all_commissions(status: str = None, sales_rep_id: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if sales_rep_id:
        query["sales_rep_id"] = sales_rep_id
    commissions = await db.commissions.find(query).sort("created_at", -1).to_list(1000)
    return [commission_helper(c) for c in commissions]


async def get_commission_summary(sales_rep_id: str = None):
    """
    Returns commission dashboard summary (SRS 3.4 / 3.5):
    - Pending vs Approved vs Paid breakdown
    - Total commission liability (pending + approved unpaid)
    """
    db = get_db()
    query = {}
    if sales_rep_id:
        query["sales_rep_id"] = sales_rep_id

    commissions = await db.commissions.find(query).to_list(10000)

    summary = {
        "total_pending": 0.0,
        "total_approved": 0.0,
        "total_paid": 0.0,
        "total_on_hold": 0.0,
        "total_liability": 0.0,  # pending + approved unpaid
        "count_pending": 0,
        "count_approved": 0,
        "count_paid": 0,
        "count_on_hold": 0
    }

    for c in commissions:
        amount = c["amount"]
        status = c["status"]
        if status == "Pending":
            summary["total_pending"] += amount
            summary["count_pending"] += 1
        elif status == "Approved":
            summary["total_approved"] += amount
            summary["count_approved"] += 1
        elif status == "Paid":
            summary["total_paid"] += amount
            summary["count_paid"] += 1
        elif status == "On Hold":
            summary["total_on_hold"] += amount
            summary["count_on_hold"] += 1

    summary["total_liability"] = summary["total_pending"] + summary["total_approved"]
    return summary


async def get_rep_rankings():
    """Manager/CEO view: all reps ranked by commissions earned (SRS 3.5)."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$sales_rep_id",
            "sales_rep_name": {"$first": "$sales_rep_name"},
            "total_earned": {"$sum": "$amount"},
            "total_paid": {
                "$sum": {"$cond": [{"$eq": ["$status", "Paid"]}, "$amount", 0]}
            },
            "deal_count": {"$sum": 1}
        }},
        {"$sort": {"total_earned": -1}}
    ]
    results = await db.commissions.aggregate(pipeline).to_list(1000)
    return [
        {
            "sales_rep_id": r["_id"],
            "sales_rep_name": r["sales_rep_name"],
            "total_earned": r["total_earned"],
            "total_paid": r["total_paid"],
            "deal_count": r["deal_count"]
        }
        for r in results
    ]
async def set_commission_splits(commission_id: str, splits: list, updated_by_role: str):
    """
    SAL-04: Support split commission attribution for multi-rep deals.
    splits: list of CommissionSplit objects (sales_rep_id, sales_rep_name, percentage)
    Total percentage across splits must equal 100.
    Only HR Manager or CEO can configure splits.
    """
    if updated_by_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can configure commission splits"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    if commission["status"] == "Paid":
        return None, "Cannot modify splits on a commission that has already been paid"

    total_percentage = sum(s.percentage for s in splits)
    if round(total_percentage, 2) != 100.0:
        return None, f"Split percentages must total 100%, got {total_percentage}%"

    splits_data = [s.model_dump() for s in splits]

    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {"splits": splits_data, "updated_at": datetime.utcnow()}}
    )
    updated = await db.commissions.find_one({"commission_id": commission_id})
    return commission_helper(updated), None