from app.database.connection import get_db
from datetime import datetime


def payroll_batch_helper(batch) -> dict:
    return {
        "id": str(batch["_id"]),
        "batch_id": batch["batch_id"],
        "month": batch["month"],
        "year": batch["year"],
        "status": batch["status"],
        "total_employees": batch["total_employees"],
        "total_gross": batch["total_gross"],
        "total_net": batch["total_net"],
        "total_commission": batch["total_commission"],
        "records": batch["records"],
        "initiated_by": batch["initiated_by"],
        "reviewed_by": batch.get("reviewed_by"),
        "approved_by": batch.get("approved_by"),
        "created_at": batch["created_at"],
        "approved_at": batch.get("approved_at")
    }


async def generate_batch_id(month: int, year: int):
    return f"PAY-{year}-{month:02d}"


async def run_monthly_payroll(month: int, year: int, initiated_by: str):
    """
    SRS 4.4.2:
    - HR Manager initiates payroll at month-end.
    - FIN-03: Only Approved milestone commission payouts are included.
    - Any commission tied to Unpaid/Overdue milestone is completely ignored.
    """
    db = get_db()

    batch_id = await generate_batch_id(month, year)

    existing = await db.payroll_batches.find_one({"batch_id": batch_id})
    if existing and existing["status"] not in ["Draft", "Pending Review"]:
        return None, f"Payroll for {month}/{year} has already been processed (status: {existing['status']})"

    employees = await db.employees.find(
        {"is_deleted": False, "status": "active"}
    ).to_list(1000)

    structures = await db.salary_structures.find({}).to_list(1000)
    structure_map = {s["employee_id"]: s for s in structures}

    # FIN-03: Only fetch Approved milestone commission payouts (never Pending/Overdue)
    from app.services.commission import get_approved_commission_totals_by_rep
    commission_map = await get_approved_commission_totals_by_rep()

    records = []
    total_gross = 0.0
    total_net = 0.0
    total_commission = 0.0

    for emp in employees:
        structure = structure_map.get(emp["employee_id"])
        if not structure:
            continue

        basic = structure["basic_salary"]
        allowances = structure.get("allowances", {})
        deductions = structure.get("deductions", {})

        allowances_total = round(sum(allowances.values()), 2)
        deductions_total = round(sum(deductions.values()), 2)

        # FIN-03: commission_map only contains Approved payouts
        commission_amount = round(commission_map.get(emp["employee_id"], 0.0), 2)
        bonus = 0.0

        gross_pay = round(basic + allowances_total + commission_amount + bonus, 2)
        net_pay = round(gross_pay - deductions_total, 2)

        records.append({
            "employee_id": emp["employee_id"],
            "employee_name": emp["full_name"],
            "department": emp["department"],
            "basic_salary": basic,
            "allowances_total": allowances_total,
            "deductions_total": deductions_total,
            "commission_amount": commission_amount,
            "bonus": bonus,
            "gross_pay": gross_pay,
            "net_pay": net_pay
        })

        total_gross += gross_pay
        total_net += net_pay
        total_commission += commission_amount

    batch = {
        "batch_id": batch_id,
        "month": month,
        "year": year,
        "status": "Pending Review",
        "total_employees": len(records),
        "total_gross": round(total_gross, 2),
        "total_net": round(total_net, 2),
        "total_commission": round(total_commission, 2),
        "records": records,
        "initiated_by": initiated_by,
        "reviewed_by": None,
        "approved_by": None,
        "created_at": datetime.utcnow(),
        "approved_at": None
    }

    if existing:
        await db.payroll_batches.replace_one({"batch_id": batch_id}, batch)
    else:
        await db.payroll_batches.insert_one(batch)

    saved = await db.payroll_batches.find_one({"batch_id": batch_id})
    return payroll_batch_helper(saved), None


async def review_payroll_batch(batch_id: str, reviewed_by: str, reviewer_role: str):
    """Finance Manager reviews payroll summary and submits for CEO approval (SRS 4.4.2)."""
    if reviewer_role not in ["super_admin", "finance_manager"]:
        return None, "Only Finance Manager or CEO can review payroll"

    db = get_db()
    batch = await db.payroll_batches.find_one({"batch_id": batch_id})
    if not batch:
        return None, "Payroll batch not found"

    if batch["status"] != "Pending Review":
        return None, f"Payroll batch is in '{batch['status']}' status, cannot review"

    await db.payroll_batches.update_one(
        {"batch_id": batch_id},
        {"$set": {
            "status": "Pending Approval",
            "reviewed_by": reviewed_by
        }}
    )
    updated = await db.payroll_batches.find_one({"batch_id": batch_id})
    return payroll_batch_helper(updated), None


async def approve_payroll_batch(batch_id: str, approved_by: str, approver_role: str):
    """
    SRS 4.4.2 / 7.2: CEO approves payroll.
    - Marks included Approved commission milestone payouts as Paid.
    - Triggers payslip generation for all employees.
    - Marks batch as Paid.
    """
    if approver_role != "super_admin":
        return None, "Only the CEO can approve payroll"

    db = get_db()
    batch = await db.payroll_batches.find_one({"batch_id": batch_id})
    if not batch:
        return None, "Payroll batch not found"

    if batch["status"] != "Pending Approval":
        return None, f"Payroll batch is in '{batch['status']}' status, cannot approve"

    await db.payroll_batches.update_one(
        {"batch_id": batch_id},
        {"$set": {
            "status": "Approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow()
        }}
    )

    # Mark included Approved milestone payouts as Paid
    await _mark_commission_payouts_paid(batch)

    # Generate payslips for all employees in this batch
    from app.services.payslip import generate_payslips_for_batch
    await generate_payslips_for_batch(batch_id)

    # Final status: Paid
    await db.payroll_batches.update_one(
        {"batch_id": batch_id},
        {"$set": {"status": "Paid"}}
    )

    updated = await db.payroll_batches.find_one({"batch_id": batch_id})
    return payroll_batch_helper(updated), None


async def _mark_commission_payouts_paid(batch: dict):
    """
    After CEO approval, marks all Approved milestone commission payouts as Paid
    for employees included in this payroll batch.
    """
    db = get_db()
    employee_ids_in_batch = {r["employee_id"] for r in batch.get("records", []) if r["commission_amount"] > 0}
    if not employee_ids_in_batch:
        return

    commissions = await db.commissions.find(
        {"sales_rep_id": {"$in": list(employee_ids_in_batch)}}
    ).to_list(1000)

    now_str = datetime.utcnow().strftime("%Y-%m-%d")
    payout_cycle = f"{batch['month']:02d}-{batch['year']}"

    for commission in commissions:
        milestones = commission.get("milestone_payouts", [])
        changed = False
        for mp in milestones:
            if mp["status"] == "Approved":
                mp["status"] = "Paid"
                mp["payout_cycle_month"] = payout_cycle
                changed = True

        if changed:
            all_statuses = [mp["status"] for mp in milestones]
            overall = "Paid" if all(s in ["Paid", "Cancelled", "Reversed"] for s in all_statuses) else "Approved"
            await db.commissions.update_one(
                {"commission_id": commission["commission_id"]},
                {"$set": {
                    "milestone_payouts": milestones,
                    "overall_status": overall,
                    "updated_at": datetime.utcnow()
                }}
            )


async def get_payroll_batch(batch_id: str):
    db = get_db()
    batch = await db.payroll_batches.find_one({"batch_id": batch_id})
    if not batch:
        return None
    return payroll_batch_helper(batch)


async def get_all_payroll_batches():
    db = get_db()
    batches = await db.payroll_batches.find({}).sort("created_at", -1).to_list(100)
    return [payroll_batch_helper(b) for b in batches]


async def get_payroll_summary_report(year: int = None):
    """FIN: Payroll Summary — total salary cost, commissions, deductions per month."""
    db = get_db()
    query = {"status": "Paid"}
    if year:
        query["year"] = year

    batches = await db.payroll_batches.find(query).sort("month", 1).to_list(100)
    return [
        {
            "month": b["month"],
            "year": b["year"],
            "total_employees": b["total_employees"],
            "total_gross": b["total_gross"],
            "total_net": b["total_net"],
            "total_commission": b["total_commission"]
        }
        for b in batches
    ]