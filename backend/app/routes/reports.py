from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.financial_reports import (
    get_revenue_overview, get_profit_and_loss,
    get_cash_flow, get_outstanding_receivables,
    get_executive_dashboard_summary
)
from app.services.export import export_to_excel, export_to_pdf
from app.utils.dependencies import get_current_finance, get_current_super_admin, get_current_user
from typing import Optional

router = APIRouter(prefix="/api/reports", tags=["Financial Reports"])


# ===== EXECUTIVE DASHBOARD (SRS 12.2) =====
@router.get("/dashboard")
async def executive_dashboard(current_user=Depends(get_current_super_admin)):
    """CEO-only unified KPI dashboard."""
    summary = await get_executive_dashboard_summary()
    return {"message": "Success", "data": summary}


# ===== REVENUE OVERVIEW (SRS 4.5) =====
@router.get("/revenue")
async def revenue_overview(current_user=Depends(get_current_finance)):
    """Real-time revenue: total contracts, received, pending, overdue."""
    data = await get_revenue_overview()
    return {"message": "Success", "data": data}


# ===== PROFIT & LOSS (SRS 4.5) =====
@router.get("/profit-loss")
async def profit_loss_report(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    current_user=Depends(get_current_finance)
):
    """P&L report — revenue minus expenses and salaries."""
    data = await get_profit_and_loss(month=month, year=year)
    return {"message": "Success", "data": data}


# ===== CASH FLOW (SRS 4.5) =====
@router.get("/cash-flow")
async def cash_flow_report(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    current_user=Depends(get_current_finance)
):
    """Cash flow: inflows (payments received) vs outflows (salaries + expenses)."""
    data = await get_cash_flow(month=month, year=year)
    return {"message": "Success", "data": data}


# ===== OUTSTANDING RECEIVABLES (SRS 4.5) =====
@router.get("/receivables")
async def outstanding_receivables(current_user=Depends(get_current_finance)):
    """All overdue and upcoming milestones with client info."""
    data = await get_outstanding_receivables()
    return {"message": "Success", "data": data, "total": len(data)}


# ===== EXPORTS =====
@router.get("/profit-loss/export/excel")
async def export_pl_excel(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    current_user=Depends(get_current_finance)
):
    data = await get_profit_and_loss(month=month, year=year)
    rows = [{
        "metric": k,
        "value": v
    } for k, v in data.items() if k != "period"]
    columns = [("metric", "Metric"), ("value", "Value")]
    return export_to_excel(rows, columns, title="Profit and Loss Report")


@router.get("/profit-loss/export/pdf")
async def export_pl_pdf(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    current_user=Depends(get_current_finance)
):
    data = await get_profit_and_loss(month=month, year=year)
    rows = [{
        "metric": k,
        "value": str(v)
    } for k, v in data.items() if k != "period"]
    columns = [("metric", "Metric"), ("value", "Value")]
    return export_to_pdf(rows, columns, title="Profit and Loss Report")


@router.get("/receivables/export/excel")
async def export_receivables_excel(current_user=Depends(get_current_finance)):
    data = await get_outstanding_receivables()
    columns = [
        ("contract_id", "Contract ID"),
        ("client_name", "Client"),
        ("project_name", "Project"),
        ("milestone_id", "Milestone ID"),
        ("description", "Description"),
        ("due_date", "Due Date"),
        ("amount", "Amount"),
        ("currency", "Currency"),
        ("status", "Status"),
        ("days_overdue", "Days Overdue"),
    ]
    return export_to_excel(data, columns, title="Outstanding Receivables")


@router.get("/cash-flow/export/excel")
async def export_cashflow_excel(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    current_user=Depends(get_current_finance)
):
    data = await get_cash_flow(month=month, year=year)
    all_rows = data["inflows"] + data["outflows"]
    all_rows.sort(key=lambda x: x["date"])
    columns = [
        ("date", "Date"),
        ("description", "Description"),
        ("amount", "Amount"),
        ("type", "Type"),
    ]
    return export_to_excel(all_rows, columns, title="Cash Flow Statement")