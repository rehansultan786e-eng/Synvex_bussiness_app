# app/routes/employee.py
#
# Employee management routes.
#
# Access: get_current_admin = super_admin, hr_manager, finance_manager
# (HR manages employees per SRS; finance_manager kept for legacy compatibility
#  with existing attendance reports access pattern)
#
# NEW: onboarding checklist endpoint (SRS 6.2 - onboarding tracking)

from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.employee import EmployeeCreate, EmployeeUpdate, OnboardingChecklistUpdate
from pydantic import BaseModel
from app.services.employee import (
    create_employee, get_all_employees,
    get_employee_by_id, update_employee, delete_employee,
    update_onboarding_checklist
)
from app.utils.dependencies import get_current_admin, get_current_hr
from typing import Optional

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.post("/", status_code=201)
async def create_new_employee(
    employee_data: EmployeeCreate,
    admin=Depends(get_current_hr)
):
    # Pass the authenticated HR user details down as the actor metadata parameters
    employee, error = await create_employee(
        employee_data,
        actor_id=admin.get("user_id", "system"),
        actor_name=admin.get("full_name", "System Automated"),
        actor_role=admin.get("role", "system")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Employee created successfully", "data": employee}


@router.get("/")
async def list_employees(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    employees = await get_all_employees(department, status, search)
    return {"data": employees}


@router.get("/{employee_id}")
async def get_employee(employee_id: str, admin=Depends(get_current_admin)):
    employee = await get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"data": employee}


@router.put("/{employee_id}")
async def update_existing_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    admin=Depends(get_current_hr)
):
    # Pass the authenticated HR user details down as the actor metadata parameters
    employee = await update_employee(
        employee_id, 
        employee_data,
        actor_id=admin.get("user_id", "system"),
        actor_name=admin.get("full_name", "System Automated"),
        actor_role=admin.get("role", "system")
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully", "data": employee}


@router.delete("/{employee_id}")
async def delete_existing_employee(employee_id: str, admin=Depends(get_current_hr)):
    employee = await get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Pass the authenticated HR user details down as the actor metadata parameters
    await delete_employee(
        employee_id,
        actor_id=admin.get("user_id", "system"),
        actor_name=admin.get("full_name", "System Automated"),
        actor_role=admin.get("role", "system")
    )
    return {"message": "Employee deleted successfully"}


# ===== NEW: Onboarding checklist (SRS 6.2) =====

@router.put("/{employee_id}/onboarding")
async def update_employee_onboarding(
    employee_id: str,
    checklist: OnboardingChecklistUpdate,
    admin=Depends(get_current_hr)
):
    # Pass the authenticated HR user details down as the actor metadata parameters
    employee = await update_onboarding_checklist(
        employee_id, 
        checklist,
        actor_id=admin.get("user_id", "system"),
        actor_name=admin.get("full_name", "System Automated"),
        actor_role=admin.get("role", "system")
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Onboarding checklist updated", "data": employee}


# ===== Face enrollment (existing, unchanged) =====

from app.deepface_service.face_recognition import save_face_images

class FaceEnrollRequest(BaseModel):
    images: list

@router.post("/{employee_id}/enroll-face")
async def enroll_face(
    employee_id: str,
    request: FaceEnrollRequest,
    admin=Depends(get_current_hr)
):
    employee = await get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    saved_images = await save_face_images(employee_id, request.images)
    return {
        "message": f"{len(saved_images)} face images saved successfully",
        "employee_id": employee_id,
        "total_images": len(saved_images)
    }