from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.expense import ExpenseCreate, ExpenseStatusUpdate
from app.services.expense import (
    create_expense, get_all_expenses, get_expense_by_id,
    get_expense_receipt_bytes, update_expense_status, get_expense_breakdown
)
from app.services.export import export_to_excel, export_to_pdf
from app.utils.dependencies import get_current_user, get_current_finance
from typing import Optional
import io

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("/", status_code=201)
async def submit_expense(expense_data: ExpenseCreate, current_user=Depends(get_current_user)):
    """Any authorized user can submit an expense (SRS 4.3.2)."""
    from app.database.connection import get_db
    from bson import ObjectId

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(current_user.get("user_id"))})
    submitted_by_name = user["full_name"] if user else "Unknown"

    expense = await create_expense(expense_data, submitted_by=current_user.get("user_id"), submitted_by_name=submitted_by_name)
    return {"message": "Expense submitted successfully", "data": expense}


@router.get("/")
async def list_expenses(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    """
    super_admin / finance_manager: see all expenses
    others: see only their own submitted expenses
    """
    role = current_user.get("role")
    submitted_by = None if role in ["super_admin", "finance_manager"] else current_user.get("user_id")

    expenses = await get_all_expenses(status=status, category=category, submitted_by=submitted_by)
    return {"message": "Success", "data": expenses, "total": len(expenses)}


@router.get("/{expense_id}")
async def get_expense(expense_id: str, current_user=Depends(get_current_user)):
    expense = await get_expense_by_id(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    role = current_user.get("role")
    if role not in ["super_admin", "finance_manager"] and expense["submitted_by"] != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="You can only view your own expenses")

    return {"message": "Success", "data": expense}


@router.get("/{expense_id}/receipt")
async def download_receipt(expense_id: str, current_user=Depends(get_current_user)):
    receipt_bytes = await get_expense_receipt_bytes(expense_id)
    if not receipt_bytes:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return StreamingResponse(io.BytesIO(receipt_bytes), media_type="application/octet-stream")


@router.put("/{expense_id}/status")
async def update_expense_status_route(
    expense_id: str,
    status_update: ExpenseStatusUpdate,
    current_user=Depends(get_current_user)
):
    """FIN-06: Finance Manager approves standard expenses; CEO approves expenses above threshold."""
    expense, error = await update_expense_status(
        expense_id, status_update,
        approved_by=current_user.get("user_id"),
        approver_role=current_user.get("role")
    )
    if error:
        raise HTTPException(status_code=403, detail=error)
    return {"message": f"Expense {status_update.status.lower()} successfully", "data": expense}


@router.get("/reports/breakdown")
async def expense_breakdown_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    current_user=Depends(get_current_finance)
):
    """FIN: Expense Breakdown report by category."""
    breakdown = await get_expense_breakdown(year=year, month=month)
    return {"message": "Success", "data": breakdown}


@router.get("/export/excel")
async def export_expenses_excel(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_finance)
):
    expenses = await get_all_expenses(status=status)
    columns = [
        ("expense_id", "Expense ID"),
        ("category", "Category"),
        ("amount", "Amount"),
        ("expense_date", "Date"),
        ("vendor_name", "Vendor"),
        ("status", "Status"),
        ("submitted_by_name", "Submitted By"),
    ]
    return export_to_excel(expenses, columns, title="Expense Report")


@router.get("/export/pdf")
async def export_expenses_pdf(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_finance)
):
    expenses = await get_all_expenses(status=status)
    columns = [
        ("expense_id", "Expense ID"),
        ("category", "Category"),
        ("amount", "Amount"),
        ("expense_date", "Date"),
        ("vendor_name", "Vendor"),
        ("status", "Status"),
        ("submitted_by_name", "Submitted By"),
    ]
    return export_to_pdf(expenses, columns, title="Expense Report")