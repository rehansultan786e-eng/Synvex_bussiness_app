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
    - HR Manager initiates payroll at month-end; system compiles all salary records.
    - System auto-includes approved commissions from the Sales module.
    - Result is a Draft batch awaiting Finance Manager review.
    """
    db = get_db()

    batch_id = await generate_batch_id(month, year)

    existing = await db.payroll_batches.find_one({"batch_id": batch_id})
    if existing and existing["status"] != "Draft":
        return None, f"Payroll for {month}/{year} has already been processed (status: {existing['status']})"

    employees = await db.employees.find({"is_deleted": False, "status": "active"}).to_list(1000)
    structures = await db.salary_structures.find({}).to_list(1000)
    structure_map = {s["employee_id"]: s for s in structures}

    # Approved commissions not yet paid, grouped by sales_rep_id (sales reps are in "users", not "employees")
    commissions = await db.commissions.find({"status": "Approved"}).to_list(10000)
    commission_map = {}
    for c in commissions:
        commission_map[c["sales_rep_id"]] = commission_map.get(c["sales_rep_id"], 0) + c["amount"]

    records = []
    total_gross = 0.0
    total_net = 0.0
    total_commission = 0.0

    for emp in employees:
        structure = structure_map.get(emp["employee_id"])
        if not structure:
            continue  # skip employees without a configured salary structure

        basic = structure["basic_salary"]
        allowances = structure.get("allowances", {})
        deductions = structure.get("deductions", {})

        allowances_total = sum(allowances.values())
        deductions_total = sum(deductions.values())

        # commission only applies if this employee's linked user account is a sales rep
        commission_amount = commission_map.get(emp["employee_id"], 0.0)
        bonus = 0.0

        gross_pay = basic + allowances_total + commission_amount + bonus
        net_pay = gross_pay - deductions_total

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
        await db.payroll_batches.update_one({"batch_id": batch_id}, {"$set": batch})
    else:
        await db.payroll_batches.insert_one(batch)

    saved = await db.payroll_batches.find_one({"batch_id": batch_id})
    return payroll_batch_helper(saved), None


async def review_payroll_batch(batch_id: str, reviewed_by: str, reviewer_role: str):
    """Finance Manager reviews the payroll summary and submits for CEO approval."""
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
        {"$set": {"status": "Pending Approval", "reviewed_by": reviewed_by}}
    )
    updated = await db.payroll_batches.find_one({"batch_id": batch_id})
    return payroll_batch_helper(updated), None


async def approve_payroll_batch(batch_id: str, approved_by: str, approver_role: str):
    """
    CEO approves payroll; system marks salaries as Paid and triggers
    payslip generation (SRS 4.4.2 / 7.2).
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

    # Mark approved commissions as Paid (they were included in this payroll)
    await db.commissions.update_many(
        {"status": "Approved"},
        {"$set": {"status": "Paid", "paid_date": datetime.utcnow().strftime("%Y-%m-%d")}}
    )

    updated = await db.payroll_batches.find_one({"batch_id": batch_id})

    # Trigger payslip generation for all records (Step 27)
    from app.services.payslip import generate_payslips_for_batch
    await generate_payslips_for_batch(batch_id)

    # Update final status to Paid after payslips generated
    await db.payroll_batches.update_one({"batch_id": batch_id}, {"$set": {"status": "Paid"}})
    updated = await db.payroll_batches.find_one({"batch_id": batch_id})

    return payroll_batch_helper(updated), None


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
    """FIN: Payroll Summary report — total salary cost, commissions, deductions per month."""
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