# app/services/employee.py
#
# Employee service — extended per SRS Section 6.2 (Onboarding).
#
# UPDATED:
# - employee_helper() now returns new fields (cnic, dob, emergency contact,
#   employment_type, reporting_manager, salary_id, onboarding_status)
# - create_employee() stores new fields + initializes onboarding_status checklist
# - update_employee() handles date_of_birth conversion
# - NEW: update_onboarding_checklist() to mark onboarding steps complete

from app.database.connection import get_db
from app.models.employee import EmployeeCreate, EmployeeUpdate, OnboardingChecklistUpdate
from bson import ObjectId
from datetime import datetime


def employee_helper(employee) -> dict:
    return {
        "id": str(employee["_id"]),
        "employee_id": employee["employee_id"],
        "full_name": employee["full_name"],
        "email": employee["email"],
        "phone": employee["phone"],
        "department": employee["department"],
        "designation": employee["designation"],
        "joining_date": str(employee["joining_date"]),
        "status": employee["status"],
        "created_at": employee["created_at"],

        # ===== NEW FIELDS =====
        "cnic": employee.get("cnic"),
        "date_of_birth": str(employee["date_of_birth"]) if employee.get("date_of_birth") else None,
        "personal_email": employee.get("personal_email"),
        "emergency_contact_name": employee.get("emergency_contact_name"),
        "emergency_contact_phone": employee.get("emergency_contact_phone"),
        "employment_type": employee.get("employment_type", "Full-time"),
        "reporting_manager": employee.get("reporting_manager"),
        "salary_id": employee.get("salary_id"),
        "onboarding_status": employee.get("onboarding_status", {
            "documents_submitted": False,
            "asset_assigned": False,
            "system_access_granted": False
        })
    }


async def create_employee(employee_data: EmployeeCreate):
    db = get_db()

    # Unique ID check
    existing_id = await db.employees.find_one({"employee_id": employee_data.employee_id})
    if existing_id:
        return None, "Employee ID already exists. Please use a unique ID."

    # Email unique check
    existing_email = await db.employees.find_one({"email": employee_data.email})
    if existing_email:
        return None, "Email already registered."

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    employee = {
        "employee_id": employee_data.employee_id,
        "full_name": employee_data.full_name,
        "email": employee_data.email,
        "phone": employee_data.phone,
        "department": employee_data.department,
        "designation": employee_data.designation,
        "joining_date": str(employee_data.joining_date),
        "status": employee_data.status,
        "password": pwd_context.hash(employee_data.password),
        "face_images": [],
        "is_deleted": False,
        "created_at": datetime.utcnow(),

        # ===== NEW FIELDS =====
        "cnic": employee_data.cnic,
        "date_of_birth": str(employee_data.date_of_birth) if employee_data.date_of_birth else None,
        "personal_email": employee_data.personal_email,
        "emergency_contact_name": employee_data.emergency_contact_name,
        "emergency_contact_phone": employee_data.emergency_contact_phone,
        "employment_type": employee_data.employment_type,
        "reporting_manager": employee_data.reporting_manager,
        "salary_id": None,  # set later when a salary record is created (Finance module)

        # Onboarding checklist - tracks document submission, asset assignment, system access
        "onboarding_status": {
            "documents_submitted": False,
            "asset_assigned": False,
            "system_access_granted": True  # employee account itself = system access
        }
    }
    result = await db.employees.insert_one(employee)
    new_employee = await db.employees.find_one({"_id": result.inserted_id})
    return employee_helper(new_employee), None


async def get_all_employees(department: str = None, status: str = None, search: str = None):
    db = get_db()
    query = {"is_deleted": False}
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}}
        ]
    employees = await db.employees.find(query).to_list(1000)
    return [employee_helper(e) for e in employees]


async def get_employee_by_id(employee_id: str):
    db = get_db()
    employee = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if employee:
        return employee_helper(employee)
    return None


async def update_employee(employee_id: str, employee_data: EmployeeUpdate):
    db = get_db()
    update_data = {k: v for k, v in employee_data.model_dump().items() if v is not None}

    if "joining_date" in update_data:
        update_data["joining_date"] = str(update_data["joining_date"])
    if "date_of_birth" in update_data:
        update_data["date_of_birth"] = str(update_data["date_of_birth"])

    update_data["updated_at"] = datetime.utcnow()
    await db.employees.update_one({"employee_id": employee_id}, {"$set": update_data})
    return await get_employee_by_id(employee_id)


async def delete_employee(employee_id: str):
    db = get_db()
    await db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )
    return True


# ===== NEW: Onboarding checklist update (SRS 6.2) =====

async def update_onboarding_checklist(employee_id: str, checklist: OnboardingChecklistUpdate):
    db = get_db()
    employee = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if not employee:
        return None

    current = employee.get("onboarding_status", {
        "documents_submitted": False,
        "asset_assigned": False,
        "system_access_granted": False
    })

    updates = {k: v for k, v in checklist.model_dump().items() if v is not None}
    current.update(updates)

    await db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {"onboarding_status": current, "updated_at": datetime.utcnow()}}
    )
    return await get_employee_by_id(employee_id)