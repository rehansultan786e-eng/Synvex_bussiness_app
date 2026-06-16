from app.database.connection import get_db
from app.models.contract import ContractCreate, ContractUpdate, MilestoneUpdate, MilestonePaymentReceived
from datetime import datetime, date


def contract_helper(contract) -> dict:
    return {
        "id": str(contract["_id"]),
        "contract_id": contract["contract_id"],
        "lead_id": contract.get("lead_id"),
        "client_name": contract["client_name"],
        "project_name": contract["project_name"],
        "start_date": str(contract["start_date"]),
        "end_date": str(contract["end_date"]),
        "total_value": contract["total_value"],
        "currency": contract["currency"],
        "payment_terms": contract.get("payment_terms"),
        "document_url": contract.get("document_url"),
        "sales_rep_id": contract.get("sales_rep_id"),
        "sales_rep_name": contract.get("sales_rep_name"),
        "milestones": contract.get("milestones", []),
        "created_by": contract["created_by"],
        "created_at": contract["created_at"],
        "updated_at": contract.get("updated_at")
    }


async def generate_contract_id():
    db = get_db()
    count = await db.contracts.count_documents({})
    return f"CON-{count + 1:05d}"


async def create_contract(contract_data: ContractCreate, created_by: str):
    db = get_db()
    contract_id = await generate_contract_id()

    milestones = []
    for idx, m in enumerate(contract_data.milestones, start=1):
        milestones.append({
            "milestone_id": f"{contract_id}-M{idx}",
            "milestone_number": idx,
            "description": m.description,
            "due_date": str(m.due_date),
            "amount": m.amount,
            "status": "Upcoming",
            "paid_date": None,
            "payment_method": None
        })

    contract = {
        "contract_id": contract_id,
        "lead_id": contract_data.lead_id,
        "client_name": contract_data.client_name,
        "project_name": contract_data.project_name,
        "start_date": str(contract_data.start_date),
        "end_date": str(contract_data.end_date),
        "total_value": contract_data.total_value,
        "currency": contract_data.currency,
        "payment_terms": contract_data.payment_terms,
        "document_url": None,
        "sales_rep_id": contract_data.sales_rep_id,
        "sales_rep_name": contract_data.sales_rep_name,
        "milestones": milestones,
        "is_deleted": False,
        "created_by": created_by,
        "created_at": datetime.utcnow()
    }
    result = await db.contracts.insert_one(contract)
    new_contract = await db.contracts.find_one({"_id": result.inserted_id})
    return contract_helper(new_contract)


async def get_all_contracts(client_name: str = None):
    db = get_db()
    query = {"is_deleted": False}
    if client_name:
        query["client_name"] = {"$regex": client_name, "$options": "i"}

    contracts = await db.contracts.find(query).sort("created_at", -1).to_list(1000)
    for c in contracts:
        _refresh_overdue_milestones(c)
    return [contract_helper(c) for c in contracts]


async def get_contract_by_id(contract_id: str):
    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract:
        return None

    refreshed = _refresh_overdue_milestones(contract)
    if refreshed:
        await db.contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"milestones": contract["milestones"]}}
        )
    return contract_helper(contract)


def _refresh_overdue_milestones(contract: dict) -> bool:
    """
    FIN-01: Auto-flags milestones as Overdue if due_date passed without payment.
    Mutates contract["milestones"] in place. Returns True if any changed.
    """
    today = date.today()
    changed = False
    for m in contract.get("milestones", []):
        if m["status"] in ["Upcoming", "Due"]:
            due = date.fromisoformat(m["due_date"])
            if due < today:
                m["status"] = "Overdue"
                changed = True
            elif due == today and m["status"] == "Upcoming":
                m["status"] = "Due"
                changed = True
    return changed


async def update_contract(contract_id: str, contract_data: ContractUpdate):
    db = get_db()
    update_data = {k: v for k, v in contract_data.model_dump().items() if v is not None}
    for date_field in ["start_date", "end_date"]:
        if date_field in update_data:
            update_data[date_field] = str(update_data[date_field])
    update_data["updated_at"] = datetime.utcnow()
    await db.contracts.update_one({"contract_id": contract_id}, {"$set": update_data})
    return await get_contract_by_id(contract_id)


async def delete_contract(contract_id: str):
    """
    SAL-05: When a contract is deleted/cancelled, all pending commission
    payouts for the linked lead are automatically cancelled.
    """
    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract:
        return False

    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )

    # SAL-05: Cancel remaining pending commission payouts for this lead
    if contract.get("lead_id"):
        from app.services.commission import cancel_remaining_commission_payouts
        await cancel_remaining_commission_payouts(contract["lead_id"])

    return True


async def add_milestone(contract_id: str, milestone_data):
    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract:
        return None, "Contract not found"

    next_number = len(contract.get("milestones", [])) + 1
    milestone = {
        "milestone_id": f"{contract_id}-M{next_number}",
        "milestone_number": next_number,
        "description": milestone_data.description,
        "due_date": str(milestone_data.due_date),
        "amount": milestone_data.amount,
        "status": "Upcoming",
        "paid_date": None,
        "payment_method": None
    }
    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$push": {"milestones": milestone}, "$set": {"updated_at": datetime.utcnow()}}
    )
    return await get_contract_by_id(contract_id), None


async def update_milestone(contract_id: str, milestone_id: str, milestone_data: MilestoneUpdate):
    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract:
        return None, "Contract not found"

    milestones = contract.get("milestones", [])
    found = False
    for m in milestones:
        if m["milestone_id"] == milestone_id:
            found = True
            if milestone_data.description is not None:
                m["description"] = milestone_data.description
            if milestone_data.due_date is not None:
                m["due_date"] = str(milestone_data.due_date)
            if milestone_data.amount is not None:
                m["amount"] = milestone_data.amount
            if milestone_data.status is not None:
                m["status"] = milestone_data.status

    if not found:
        return None, "Milestone not found"

    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"milestones": milestones, "updated_at": datetime.utcnow()}}
    )
    return await get_contract_by_id(contract_id), None


async def mark_milestone_received(contract_id: str, milestone_id: str, payment_data: MilestonePaymentReceived):
    """
    FIN-02: Finance Manager marks milestone as Received.
    Automatically triggers commission payout calculation for this milestone (SAL-03).
    """
    db = get_db()
    contract = await db.contracts.find_one({"contract_id": contract_id, "is_deleted": False})
    if not contract:
        return None, "Contract not found"

    milestones = contract.get("milestones", [])
    found = False
    milestone_amount = 0

    for m in milestones:
        if m["milestone_id"] == milestone_id:
            if m["status"] == "Received":
                return None, "Milestone is already marked as Received"
            found = True
            m["status"] = "Received"
            m["paid_date"] = str(payment_data.paid_date)
            m["payment_method"] = payment_data.payment_method
            milestone_amount = m["amount"]
            break

    if not found:
        return None, "Milestone not found"

    await db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"milestones": milestones, "updated_at": datetime.utcnow()}}
    )

    # FIN-02 / SAL-03: Trigger proportional commission for this milestone
    if contract.get("lead_id"):
        from app.services.commission import trigger_milestone_commission
        await trigger_milestone_commission(
            lead_id=contract["lead_id"],
            milestone_id=milestone_id,
            milestone_amount=milestone_amount
        )

        # FIN notifications: Finance Manager + CEO notified of milestone received
        from app.services.notification import create_notification
        notif_users = await db.users.find(
            {"role": {"$in": ["super_admin", "finance_manager"]}}
        ).to_list(20)
        for u in notif_users:
            await create_notification(
                user_id=str(u["_id"]),
                message=f"Milestone {milestone_id} for contract {contract_id} ({contract['client_name']}) marked as Received. Amount: {milestone_amount} {contract['currency']}.",
                notif_type="milestone_due"
            )

    return await get_contract_by_id(contract_id), None


async def get_overdue_milestones():
    """Outstanding Receivables — all overdue milestones with client info."""
    db = get_db()
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)

    overdue = []
    for c in contracts:
        _refresh_overdue_milestones(c)
        for m in c.get("milestones", []):
            if m["status"] == "Overdue":
                overdue.append({
                    "contract_id": c["contract_id"],
                    "client_name": c["client_name"],
                    "project_name": c["project_name"],
                    "milestone_id": m["milestone_id"],
                    "description": m["description"],
                    "due_date": m["due_date"],
                    "amount": m["amount"],
                    "currency": c["currency"]
                })
    return overdue


async def get_upcoming_milestones(days: int = 7):
    """FIN-04: Milestones due within N days — for payment reminders."""
    from datetime import timedelta
    db = get_db()
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)

    today = date.today()
    target = today + timedelta(days=days)

    upcoming = []
    for c in contracts:
        for m in c.get("milestones", []):
            if m["status"] in ["Upcoming", "Due"]:
                due = date.fromisoformat(m["due_date"])
                if today <= due <= target:
                    upcoming.append({
                        "contract_id": c["contract_id"],
                        "client_name": c["client_name"],
                        "project_name": c["project_name"],
                        "milestone_id": m["milestone_id"],
                        "description": m["description"],
                        "due_date": m["due_date"],
                        "amount": m["amount"],
                        "currency": c["currency"]
                    })
    return upcoming