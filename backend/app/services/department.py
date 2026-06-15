from app.database.connection import get_db
from app.models.department import DepartmentCreate, DepartmentUpdate
from datetime import datetime

def department_helper(department) -> dict:
    return {
        "id": str(department["_id"]),
        "department_name": department["department_name"],
        "department_code": department["department_code"],
        "manager_name": department["manager_name"],
        "description": department.get("description"),
        "total_employees": department.get("total_employees", 0),
        "created_at": department["created_at"]
    }

async def create_department(department_data: DepartmentCreate):
    db = get_db()
    existing = await db.departments.find_one({"department_code": department_data.department_code})
    if existing:
        return None, "Department code already exists"
    
    department = {
        **department_data.model_dump(),
        "total_employees": 0,
        "is_deleted": False,
        "created_at": datetime.utcnow()
    }
    result = await db.departments.insert_one(department)
    new_dept = await db.departments.find_one({"_id": result.inserted_id})
    return department_helper(new_dept), None

async def get_all_departments():
    db = get_db()
    departments = await db.departments.find({"is_deleted": False}).to_list(1000)
    result = []
    for dept in departments:
        total = await db.employees.count_documents({
            "department": dept["department_name"],
            "is_deleted": False
        })
        dept["total_employees"] = total
        result.append(department_helper(dept))
    return result

async def get_department_by_code(department_code: str):
    db = get_db()
    dept = await db.departments.find_one({"department_code": department_code, "is_deleted": False})
    if dept:
        return department_helper(dept)
    return None

async def update_department(department_code: str, department_data: DepartmentUpdate):
    db = get_db()
    update_data = {k: v for k, v in department_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    await db.departments.update_one({"department_code": department_code}, {"$set": update_data})
    return await get_department_by_code(department_code)

async def delete_department(department_code: str):
    db = get_db()
    await db.departments.update_one(
        {"department_code": department_code},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )
    return True