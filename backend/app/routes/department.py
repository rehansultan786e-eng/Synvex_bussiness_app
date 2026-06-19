from fastapi import APIRouter, HTTPException, Depends
from app.models.department import DepartmentCreate, DepartmentUpdate
from app.services.department import (
    create_department, get_all_departments,
    get_department_by_code, update_department, delete_department
)
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.post("/", status_code=201)
async def create_new_department(
    department_data: DepartmentCreate,
    admin=Depends(get_current_admin)
):
    department, error = await create_department(department_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Department created successfully", "data": department}


@router.get("/")
async def get_departments(admin=Depends(get_current_admin)):
    departments = await get_all_departments()
    return {"message": "Success", "data": departments, "total": len(departments)}


@router.get("/{department_code}")
async def get_department(department_code: str, admin=Depends(get_current_admin)):
    department = await get_department_by_code(department_code)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Success", "data": department}


@router.put("/{department_code}")
async def update_existing_department(
    department_code: str,
    department_data: DepartmentUpdate,
    admin=Depends(get_current_admin)
):
    department = await update_department(department_code, department_data)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department updated successfully", "data": department}


@router.delete("/{department_code}")
async def delete_existing_department(department_code: str, admin=Depends(get_current_admin)):
    await delete_department(department_code)
    return {"message": "Department deleted successfully"}