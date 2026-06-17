from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.salary import (
    SalaryStructureCreate, SalaryAdvanceRequest, SalaryAdvanceStatusUpdate
)
from app.models.payroll import PayrollRunRequest
from app.services.salary import (
    create_or_update_salary_structure, get_salary_structure, get_all_salary_structures,
    request_salary_advance, update_advance_status, get_all_advances
)
from app.services.payroll import (
    run_monthly_payroll, review_payroll_batch, approve_payroll_batch,
    get_payroll_batch, get_all_payroll_batches, get_payroll_summary_report
)
from app.services.payslip import (
    get_payslip_pdf_bytes, get_employee_payslips, get_all_payslips
)
from app.utils.dependencies import get_current_user, get_current_hr, get_current_finance, get_current_super_admin
from typing import Optional
import io

router = APIRouter(prefix="/api/payroll", tags=["Payroll & Salaries"])


@router.post("/salary-structure")
async def set_salary_structure(
    structure_data: SalaryStructureCreate,
    current_user=Depends(get_current_hr)
):
    structure, error = await create_or_update_salary_structure(structure_data)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Salary structure saved successfully", "data": structure}


@router.get("/salary-structure/{employee_id}")
async def get_employee_salary_structure(employee_id: str, current_user=Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["super_admin", "hr_manager", "finance_manager"] and employee_id != current_user.get("employee_id"):
        raise HTTPException(status_code=403, detail="Access denied")

    structure = await get_salary_structure(employee_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return {"message": "Success", "data": structure}


@router.get("/salary-structures")
async def list_all_salary_structures(current_user=Depends(get_current_hr)):
    structures = await get_all_salary_structures()
    return {"message": "Success", "data": structures, "total": len(structures)}


@router.post("/advances")
async def submit_advance_request(
    advance_data: SalaryAdvanceRequest,
    current_user=Depends(get_current_user)
):
    employee_id = current_user.get("employee_id") or current_user.get("user_id")
    employee_name = current_user.get("full_name", "Unknown")

    from app.database.connection import get_db
    db = get_db()
    if current_user.get("employee_id"):
        emp = await db.employees.find_one({"employee_id": current_user.get("employee_id")})
        if emp:
            employee_name = emp["full_name"]

    advance = await request_salary_advance(advance_data, employee_id=employee_id, employee_name=employee_name)
    return {"message": "Salary advance request submitted successfully", "data": advance}


@router.get("/advances")
async def list_advances(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    role = current_user.get("role")
    employee_id = None
    if role not in ["super_admin", "hr_manager", "finance_manager"]:
        employee_id = current_user.get("employee_id") or current_user.get("user_id")

    advances = await get_all_advances(status=status, employee_id=employee_id)
    return {"message": "Success", "data": advances, "total": len(advances)}


@router.put("/advances/{advance_id}/status")
async def update_advance_status_route(
    advance_id: str,
    status_update: SalaryAdvanceStatusUpdate,
    current_user=Depends(get_current_hr)
):
    advance, error = await update_advance_status(
        advance_id, status_update,
        approved_by=current_user.get("user_id"),
        approver_role=current_user.get("role")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Salary advance {status_update.status.lower()} successfully", "data": advance}


@router.post("/run")
async def run_payroll(request: PayrollRunRequest, current_user=Depends(get_current_hr)):
    batch, error = await run_monthly_payroll(request.month, request.year, initiated_by=current_user.get("user_id"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Payroll run completed - pending review", "data": batch}


@router.put("/batches/{batch_id}/review")
async def review_batch(batch_id: str, current_user=Depends(get_current_finance)):
    batch, error = await review_payroll_batch(batch_id, reviewed_by=current_user.get("user_id"), reviewer_role=current_user.get("role"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Payroll batch submitted for CEO approval", "data": batch}


@router.put("/batches/{batch_id}/approve")
async def approve_batch(batch_id: str, current_user=Depends(get_current_super_admin)):
    batch, error = await approve_payroll_batch(batch_id, approved_by=current_user.get("user_id"), approver_role=current_user.get("role"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Payroll approved and payslips generated successfully", "data": batch}


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str, current_user=Depends(get_current_finance)):
    batch = await get_payroll_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Payroll batch not found")
    return {"message": "Success", "data": batch}


@router.get("/batches")
async def list_batches(current_user=Depends(get_current_finance)):
    batches = await get_all_payroll_batches()
    return {"message": "Success", "data": batches, "total": len(batches)}


@router.get("/reports/summary")
async def payroll_summary(year: Optional[int] = Query(None), current_user=Depends(get_current_finance)):
    summary = await get_payroll_summary_report(year=year)
    return {"message": "Success", "data": summary}


@router.get("/payslips/my")
async def get_my_payslips(current_user=Depends(get_current_user)):
    employee_id = current_user.get("employee_id") or current_user.get("user_id")
    payslips = await get_employee_payslips(employee_id)
    return {"message": "Success", "data": payslips}


@router.get("/payslips/employee/{employee_id}")
async def get_employee_payslips_route(employee_id: str, current_user=Depends(get_current_hr)):
    payslips = await get_employee_payslips(employee_id)
    return {"message": "Success", "data": payslips}


@router.get("/payslips")
async def list_all_payslips(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    current_user=Depends(get_current_finance)
):
    payslips = await get_all_payslips(month=month, year=year)
    return {"message": "Success", "data": payslips, "total": len(payslips)}


@router.get("/payslips/{payslip_id}/download")
async def download_payslip(payslip_id: str, current_user=Depends(get_current_user)):
    pdf_bytes = await get_payslip_pdf_bytes(payslip_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Payslip not found")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={payslip_id}.pdf"}
    )