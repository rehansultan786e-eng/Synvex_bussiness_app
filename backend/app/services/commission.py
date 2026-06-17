from app.database.connection import get_db
from app.models.commission import CommissionCreate, CommissionRateOverride, CommissionSplitsRequest, MilestonePayoutApproval
from app.services.audit_log import log_action
from datetime import datetime, date


def commission_helper(commission) -> dict:
    return {
        "id": str(commission["_id"]),
        "commission_id": commission["commission_id"],
        "lead_id": commission["lead_id"],
        "sales_rep_id": commission["sales_rep_id"],
        "sales_rep_name": commission["sales_rep_name"],
        "total_contract_value": commission["total_contract_value"],
        "rate": commission["rate"],
        "total_commission_calculated": commission["total_commission_calculated"],
        "milestone_payouts": commission.get("milestone_payouts", []),
        "overall_status": commission["overall_status"],
        "splits": commission.get("splits"),
        "approved_by": commission.get("approved_by"),
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
    return 5.0  # SRS default: 5%


async def create_commission_for_won_lead(lead_id: str):
    """
    SAL-01: Called automatically when a Lead transitions to Won.
    Creates commission record with status Pending (Accrued).
    Actual milestone payouts are created separately when milestones are received.
    """
    db = get_db()

    lead = await db.leads.find_one({"lead_id": lead_id, "is_deleted": False})
    if not lead:
        return None, "Lead not found"

    existing = await db.commissions.find_one({"lead_id": lead_id})
    if existing:
        return commission_helper(existing), None

    rate = await get_default_commission_rate(lead["sales_rep_id"])
    total_contract_value = lead["estimated_value"]
    total_commission_calculated = round(total_contract_value * (rate / 100), 2)

    commission_id = await generate_commission_id()

    commission = {
        "commission_id": commission_id,
        "lead_id": lead_id,
        "sales_rep_id": lead["sales_rep_id"],
        "sales_rep_name": lead["sales_rep_name"],
        "total_contract_value": total_contract_value,
        "rate": rate,
        "total_commission_calculated": total_commission_calculated,
        "milestone_payouts": [],  # populated as milestones are received
        "overall_status": "Pending",
        "splits": None,
        "approved_by": None,
        "comments": None,
        "created_at": datetime.utcnow()
    }
    result = await db.commissions.insert_one(commission)
    new_commission = await db.commissions.find_one({"_id": result.inserted_id})

    # Notify sales rep
    from app.services.notification import create_notification
    await create_notification(
        user_id=lead["sales_rep_id"],
        message=f"Deal {lead_id} marked as Won. Commission of {total_commission_calculated} ({rate}%) has been accrued and is pending milestone payments.",
        notif_type="commission_status"
    )

    return commission_helper(new_commission), None


async def trigger_milestone_commission(lead_id: str, milestone_id: str, milestone_amount: float, invoice_id: str = None):
    """
    SAL-03 / FIN-02: Called automatically when a milestone is marked Received.
    Calculates proportional commission share for that milestone and adds it
    to the commission's milestone_payouts array with status Pending.
    """
    db = get_db()

    commission = await db.commissions.find_one({"lead_id": lead_id})
    if not commission:
        return None, "Commission record not found for this lead"

    for mp in commission.get("milestone_payouts", []):
        if mp["milestone_id"] == milestone_id:
            return commission_helper(commission), None

    contract = await db.contracts.find_one({"lead_id": lead_id, "is_deleted": False})
    total_contract_value = contract["total_value"] if contract else commission["total_contract_value"]

    if total_contract_value > 0:
        proportion = milestone_amount / total_contract_value
    else:
        proportion = 0

    commission_share = round(proportion * commission["total_commission_calculated"], 2)
    now = datetime.utcnow()
    payout_cycle_month = now.strftime("%B-%Y")

    new_payout = {
        "milestone_id": milestone_id,
        "milestone_amount": milestone_amount,
        "commission_share": commission_share,
        "status": "Pending",
        "triggered_by_invoice_id": invoice_id,
        "payout_cycle_month": payout_cycle_month,
        "reversed_at": None,
        "cancelled_at": None
    }

    await db.commissions.update_one(
        {"lead_id": lead_id},
        {
            "$push": {"milestone_payouts": new_payout},
            "$set": {"updated_at": now}
        }
    )

    updated = await db.commissions.find_one({"lead_id": lead_id})

    approvers = await db.users.find({"role": {"$in": ["super_admin", "finance_manager"]}}).to_list(20)
    for approver in approvers:
        from app.services.notification import create_notification
        await create_notification(
            user_id=str(approver["_id"]),
            message=f"Milestone {milestone_id} received. Commission share of {commission_share} is pending approval for {commission['sales_rep_name']}.",
            notif_type="commission_status"
        )

    return commission_helper(updated), None


async def approve_milestone_payout(
    commission_id: str, 
    milestone_id: str, 
    approved_by: str, 
    approver_role: str,
    actor_name: str = "System Automated"
):
    """
    SAL-04: CEO or Finance Manager approves a specific milestone commission payout.
    """
    if approver_role not in ["super_admin", "finance_manager"]:
        return None, "Only CEO or Finance Manager can approve commission payouts"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"
        
    old_payload = commission_helper(commission)

    milestones = commission.get("milestone_payouts", [])
    found = False
    for mp in milestones:
        if mp["milestone_id"] == milestone_id:
            if mp["status"] != "Pending":
                return None, f"Milestone payout is already {mp['status']}"
            mp["status"] = "Approved"
            found = True
            break

    if not found:
        return None, "Milestone payout not found"

    all_statuses = [mp["status"] for mp in milestones]
    overall = "Approved" if all(s in ["Approved", "Paid", "Cancelled"] for s in all_statuses) else "Pending"

    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {
            "milestone_payouts": milestones,
            "overall_status": overall,
            "approved_by": approved_by,
            "updated_at": datetime.utcnow()
        }}
    )
    updated = await db.commissions.find_one({"commission_id": commission_id})

    from app.services.notification import create_notification
    await create_notification(
        user_id=commission["sales_rep_id"],
        message=f"Your commission share of {next((mp['commission_share'] for mp in milestones if mp['milestone_id'] == milestone_id), 0)} for milestone {milestone_id} has been approved.",
        notif_type="commission_status"
    )

    # Trigger Audit Log
    await log_action(
        user_id=approved_by,
        user_name=actor_name,
        user_role=approver_role,
        action="UPDATE",
        entity="commission_milestone",
        entity_id=commission_id,
        old_value=old_payload,
        new_value=commission_helper(updated),
        description=f"Approved milestone payout {milestone_id} for commission ledger {commission_id}."
    )

    return commission_helper(updated), None


async def cancel_remaining_commission_payouts(lead_id: str):
    """
    SAL-05: Called when a contract is cancelled/terminated.
    """
    db = get_db()
    commission = await db.commissions.find_one({"lead_id": lead_id})
    if not commission:
        return None, "Commission not found"

    milestones = commission.get("milestone_payouts", [])
    now = datetime.utcnow().isoformat()
    for mp in milestones:
        if mp["status"] == "Pending":
            mp["status"] = "Cancelled"
            mp["cancelled_at"] = now

    await db.commissions.update_one(
        {"lead_id": lead_id},
        {"$set": {
            "milestone_payouts": milestones,
            "overall_status": "Cancelled",
            "updated_at": datetime.utcnow()
        }}
    )
    updated = await db.commissions.find_one({"lead_id": lead_id})

    from app.services.notification import create_notification
    await create_notification(
        user_id=commission["sales_rep_id"],
        message=f"Contract for lead {lead_id} has been cancelled. All pending commission payouts have been cancelled.",
        notif_type="commission_status"
    )

    return commission_helper(updated), None


async def reverse_milestone_commission(
    commission_id: str, 
    milestone_id: str, 
    reversed_by_role: str,
    actor_id: str = "system",
    actor_name: str = "System Automated"
):
    """
    SAL-06: Clawback/Recovery Rule — deducts from next payroll.
    """
    if reversed_by_role not in ["super_admin", "finance_manager"]:
        return None, "Only CEO or Finance Manager can reverse a commission"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    old_payload = commission_helper(commission)
    milestones = commission.get("milestone_payouts", [])
    reversed_amount = 0
    found = False
    for mp in milestones:
        if mp["milestone_id"] == milestone_id:
            if mp["status"] not in ["Approved", "Paid"]:
                return None, f"Can only reverse Approved or Paid commission payouts"
            mp["status"] = "Reversed"
            mp["reversed_at"] = datetime.utcnow().isoformat()
            reversed_amount = mp["commission_share"]
            found = True
            break

    if not found:
        return None, "Milestone payout not found"

    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {
            "milestone_payouts": milestones,
            "overall_status": "Reversed",
            "updated_at": datetime.utcnow()
        }}
    )

    if reversed_amount > 0:
        structure = await db.salary_structures.find_one({"employee_id": commission["sales_rep_id"]})
        if structure:
            deductions = structure.get("deductions", {})
            deductions["other"] = deductions.get("other", 0) + reversed_amount
            await db.salary_structures.update_one(
                {"employee_id": commission["sales_rep_id"]},
                {"$set": {"deductions": deductions, "updated_at": datetime.utcnow()}}
            )

    updated = await db.commissions.find_one({"commission_id": commission_id})

    from app.services.notification import create_notification
    await create_notification(
        user_id=commission["sales_rep_id"],
        message=f"Commission of {reversed_amount} for milestone {milestone_id} has been reversed due to a chargeback. This amount will be deducted from your next payroll.",
        notif_type="commission_status"
    )

    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=reversed_by_role,
        action="REVERSE",
        entity="commission_milestone",
        entity_id=commission_id,
        old_value=old_payload,
        new_value=commission_helper(updated),
        description=f"Clawback applied: Reversed milestone payout {milestone_id} for commission {commission_id}. Deducted {reversed_amount} from rep payroll structure."
    )

    return commission_helper(updated), None


async def override_commission_rate(
    commission_id: str, 
    override, 
    updated_by_role: str,
    actor_id: str = "system",
    actor_name: str = "System Automated"
):
    """Only HR Manager or CEO can override commission rate per deal."""
    if updated_by_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can override commission rate"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    if commission["overall_status"] in ["Paid"]:
        return None, "Cannot modify a commission that has already been fully paid"

    old_payload = commission_helper(commission)
    new_total = round(commission["total_contract_value"] * (override.rate / 100), 2)

    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {
            "rate": override.rate,
            "total_commission_calculated": new_total,
            "updated_at": datetime.utcnow()
        }}
    )
    updated = await db.commissions.find_one({"commission_id": commission_id})
    
    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=updated_by_role,
        action="UPDATE_RATE",
        entity="commission",
        entity_id=commission_id,
        old_value=old_payload,
        new_value=commission_helper(updated),
        description=f"Overridden core commission rate for deal {commission_id} to {override.rate}%."
    )

    return commission_helper(updated), None


async def set_commission_splits(
    commission_id: str, 
    splits: list, 
    updated_by_role: str,
    actor_id: str = "system",
    actor_name: str = "System Automated"
):
    """SAL multi-rep: split commission attribution."""
    if updated_by_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can configure commission splits"

    db = get_db()
    commission = await db.commissions.find_one({"commission_id": commission_id})
    if not commission:
        return None, "Commission not found"

    if commission["overall_status"] == "Paid":
        return None, "Cannot modify splits on a fully paid commission"

    old_payload = commission_helper(commission)
    total_percentage = sum(s.percentage for s in splits)
    if round(total_percentage, 2) != 100.0:
        return None, f"Split percentages must total 100%, got {total_percentage}%"

    splits_data = [s.model_dump() for s in splits]
    await db.commissions.update_one(
        {"commission_id": commission_id},
        {"$set": {"splits": splits_data, "updated_at": datetime.utcnow()}}
    )
    updated = await db.commissions.find_one({"commission_id": commission_id})
    
    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=updated_by_role,
        action="UPDATE_SPLIT",
        entity="commission",
        entity_id=commission_id,
        old_value=old_payload,
        new_value=commission_helper(updated),
        description=f"Applied modified distribution split layout for commission {commission_id}."
    )
    
    return commission_helper(updated), None


async def get_all_commissions(status: str = None, sales_rep_id: str = None):
    db = get_db()
    query = {}
    if status:
        query["overall_status"] = status
    if sales_rep_id:
        query["sales_rep_id"] = sales_rep_id
    commissions = await db.commissions.find(query).sort("created_at", -1).to_list(1000)
    return [commission_helper(c) for c in commissions]


async def get_commission_summary(sales_rep_id: str = None):
    db = get_db()
    query = {}
    if sales_rep_id:
        query["sales_rep_id"] = sales_rep_id

    commissions = await db.commissions.find(query).to_list(10000)

    summary = {
        "total_calculated": 0.0,
        "total_pending": 0.0,
        "total_approved": 0.0,
        "total_paid": 0.0,
        "total_cancelled": 0.0,
        "total_reversed": 0.0,
        "total_liability": 0.0
    }

    for c in commissions:
        for mp in c.get("milestone_payouts", []):
            amount = mp["commission_share"]
            status = mp["status"]
            if status == "Pending":
                summary["total_pending"] += amount
            elif status == "Approved":
                summary["total_approved"] += amount
            elif status == "Paid":
                summary["total_paid"] += amount
            elif status == "Cancelled":
                summary["total_cancelled"] += amount
            elif status == "Reversed":
                summary["total_reversed"] += amount
        summary["total_calculated"] += c["total_commission_calculated"]

    summary["total_liability"] = summary["total_pending"] + summary["total_approved"]
    return summary


async def get_rep_rankings():
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$sales_rep_id",
            "sales_rep_name": {"$first": "$sales_rep_name"},
            "total_calculated": {"$sum": "$total_commission_calculated"},
            "deal_count": {"$sum": 1}
        }},
        {"$sort": {"total_calculated": -1}}
    ]
    results = await db.commissions.aggregate(pipeline).to_list(1000)
    return [
        {
            "sales_rep_id": r["_id"],
            "sales_rep_name": r["sales_rep_name"],
            "total_calculated": r["total_calculated"],
            "deal_count": r["deal_count"]
        }
        for r in results
    ]


async def get_approved_commission_totals_by_rep():
    db = get_db()
    commissions = await db.commissions.find({}).to_list(10000)

    totals = {}
    for c in commissions:
        rep_id = c["sales_rep_id"]
        for mp in c.get("milestone_payouts", []):
            if mp["status"] == "Approved":
                totals[rep_id] = totals.get(rep_id, 0) + mp["commission_share"]

    return totals