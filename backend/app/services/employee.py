# app/services/employee.py
#
# Employee service — extended per SRS Section 6.2 (Onboarding).
#
# UPDATED:
# - employee_helper() now returns new fields (cnic, dob, emergency contact,
#   employment_type, reporting_manager, salary_id, onboarding_status)
# - create_employee() stores new fields + initializes onboarding_status checklist + logs action
# - update_employee() handles date_of_birth conversion + logs action
# - delete_employee() updates deletion state + logs action
# - NEW: update_onboarding_checklist() to mark onboarding steps complete + logs action

from app.database.connection import get_db
from app.models.employee import EmployeeCreate, EmployeeUpdate, OnboardingChecklistUpdate
from app.services.audit_log import log_action
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

async def create_employee(
    employee_data: EmployeeCreate,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
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

    # SRS 6.4.1: Initialize leave balance for the new employee
    from app.services.leave_balance import initialize_leave_balance
    await initialize_leave_balance(employee_data.employee_id)

    # Transform data for safe audit payload mapping (stripping credential paths)
    audit_new_payload = employee_helper(new_employee)

    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="CREATE",
        entity="employee",
        entity_id=employee_data.employee_id,
        old_value=None,
        new_value=audit_new_payload,
        description=f"Onboarded and registered new employee file for {employee_data.full_name} ({employee_data.employee_id})."
    )

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


async def update_employee(
    employee_id: str, 
    employee_data: EmployeeUpdate,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
    db = get_db()
    
    # Retrieve pre-update state for structured delta analytics
    old_record = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if not old_record:
        return None

    old_payload = employee_helper(old_record)

    update_data = {k: v for k, v in employee_data.model_dump().items() if v is not None}

    if "joining_date" in update_data:
        update_data["joining_date"] = str(update_data["joining_date"])
    if "date_of_birth" in update_data:
        update_data["date_of_birth"] = str(update_data["date_of_birth"])

    update_data["updated_at"] = datetime.utcnow()
    await db.employees.update_one({"employee_id": employee_id}, {"$set": update_data})
    
    updated_payload = await get_employee_by_id(employee_id)

    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE",
        entity="employee",
        entity_id=employee_id,
        old_value=old_payload,
        new_value=updated_payload,
        description=f"Updated demographic profiles or registry indices for employee ID: {employee_id}."
    )

    return updated_payload


async def delete_employee(
    employee_id: str,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
    db = get_db()
    
    old_record = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if not old_record:
        return False
        
    old_payload = employee_helper(old_record)

    await db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )

    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="DELETE",
        entity="employee",
        entity_id=employee_id,
        old_value=old_payload,
        new_value={"is_deleted": True},
        description=f"Soft deleted employee file entry from internal access structures for ID: {employee_id}."
    )

    return True


# ===== NEW: Onboarding checklist update (SRS 6.2) =====

async def update_onboarding_checklist(
    employee_id: str, 
    checklist: OnboardingChecklistUpdate,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
    db = get_db()
    employee = await db.employees.find_one({"employee_id": employee_id, "is_deleted": False})
    if not employee:
        return None

    old_payload = employee_helper(employee)

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
    
    updated_payload = await get_employee_by_id(employee_id)

    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="UPDATE_ONBOARDING",
        entity="employee",
        entity_id=employee_id,
        old_value={"onboarding_status": old_payload.get("onboarding_status")},
        new_value={"onboarding_status": updated_payload.get("onboarding_status")},
        description=f"Modified specific operational onboarding checklist parameters for employee ID: {employee_id}."
    )

    return updated_payload