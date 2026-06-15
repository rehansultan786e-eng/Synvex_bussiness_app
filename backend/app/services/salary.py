from app.database.connection import get_db
from app.models.salary import (
    SalaryStructureCreate, SalaryStructureUpdate,
    SalaryAdvanceRequest, SalaryAdvanceStatusUpdate
)
from datetime import datetime


def salary_structure_helper(structure) -> dict:
    return {
        "id": str(structure["_id"]),
        "employee_id": structure["employee_id"],
        "basic_salary": structure["basic_salary"],
        "allowances": structure["allowances"],
        "deductions": structure["deductions"],
        "created_at": structure["created_at"],
        "updated_at": structure.get("updated_at")
    }


def advance_helper(advance) -> dict:
    return {
        "id": str(advance["_id"]),
        "advance_id": advance["advance_id"],
        "employee_id": advance["employee_id"],
        "employee_name": advance["employee_name"],
        "amount": advance["amount"],
        "reason": advance["reason"],
        "status": advance["status"],
        "approved_by": advance.get("approved_by"),
        "comments": advance.get("comments"),
        "deducted": advance.get("deducted", False),
        "created_at": advance["created_at"]
    }


# ===== SALARY STRUCTURE (SRS 4.4.1) =====

async def create_or_update_salary_structure(structure_data: SalaryStructureCreate):
    db = get_db()

    employee = await db.employees.find_one({"employee_id": structure_data.employee_id, "is_deleted": False})
    if not employee:
        return None, "Employee not found"

    existing = await db.salary_structures.find_one({"employee_id": structure_data.employee_id})

    structure_doc = {
        "employee_id": structure_data.employee_id,
        "basic_salary": structure_data.basic_salary,
        "allowances": structure_data.allowances.model_dump(),
        "deductions": structure_data.deductions.model_dump(),
        "updated_at": datetime.utcnow()
    }

    if existing:
        await db.salary_structures.update_one(
            {"employee_id": structure_data.employee_id},
            {"$set": structure_doc}
        )
    else:
        structure_doc["created_at"] = datetime.utcnow()
        result = await db.salary_structures.insert_one(structure_doc)
        # Link salary_id to employee record
        await db.employees.update_one(
            {"employee_id": structure_data.employee_id},
            {"$set": {"salary_id": str(result.inserted_id)}}
        )

    updated = await db.salary_structures.find_one({"employee_id": structure_data.employee_id})
    return salary_structure_helper(updated), None


async def get_salary_structure(employee_id: str):
    db = get_db()
    structure = await db.salary_structures.find_one({"employee_id": employee_id})
    if not structure:
        return None
    return salary_structure_helper(structure)


async def get_all_salary_structures():
    db = get_db()
    structures = await db.salary_structures.find({}).to_list(1000)
    return [salary_structure_helper(s) for s in structures]


# ===== SALARY ADVANCE / LOAN (SRS 4.4.3) =====

async def generate_advance_id():
    db = get_db()
    count = await db.salary_advances.count_documents({})
    return f"ADV-{count + 1:05d}"


async def request_salary_advance(advance_data: SalaryAdvanceRequest, employee_id: str, employee_name: str):
    db = get_db()
    advance_id = await generate_advance_id()

    advance = {
        "advance_id": advance_id,
        "employee_id": employee_id,
        "employee_name": employee_name,
        "amount": advance_data.amount,
        "reason": advance_data.reason,
        "status": "Pending",
        "approved_by": None,
        "comments": None,
        "deducted": False,
        "created_at": datetime.utcnow()
    }
    result = await db.salary_advances.insert_one(advance)
    new_advance = await db.salary_advances.find_one({"_id": result.inserted_id})
    return advance_helper(new_advance)


async def update_advance_status(advance_id: str, status_update: SalaryAdvanceStatusUpdate, approved_by: str, approver_role: str):
    """HR Manager approves; on approval, amount is auto-deducted from next payslip (SRS 4.4.3)."""
    if approver_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can approve salary advances"

    db = get_db()
    advance = await db.salary_advances.find_one({"advance_id": advance_id})
    if not advance:
        return None, "Advance request not found"

    if advance["status"] != "Pending":
        return None, f"Advance request is already {advance['status']}"

    update_data = {
        "status": status_update.status,
        "approved_by": approved_by,
        "comments": status_update.comments
    }

    if status_update.status == "Approved":
        # Add to employee's salary structure deductions for next payslip
        structure = await db.salary_structures.find_one({"employee_id": advance["employee_id"]})
        if structure:
            deductions = structure.get("deductions", {})
            deductions["loan_repayment"] = deductions.get("loan_repayment", 0) + advance["amount"]
            await db.salary_structures.update_one(
                {"employee_id": advance["employee_id"]},
                {"$set": {"deductions": deductions, "updated_at": datetime.utcnow()}}
            )
        update_data["deducted"] = True

    await db.salary_advances.update_one({"advance_id": advance_id}, {"$set": update_data})
    updated = await db.salary_advances.find_one({"advance_id": advance_id})

    from app.services.notification import create_notification
    await create_notification(
        user_id=advance["employee_id"],
        message=f"Your salary advance request {advance_id} has been {status_update.status.lower()}.",
        notif_type="leave_decision"
    )

    return advance_helper(updated), None


async def get_all_advances(status: str = None, employee_id: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if employee_id:
        query["employee_id"] = employee_id
    advances = await db.salary_advances.find(query).sort("created_at", -1).to_list(1000)
    return [advance_helper(a) for a in advances]