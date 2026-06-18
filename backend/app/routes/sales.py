from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.lead import LeadCreate, LeadUpdate, MeetingCreate
from app.models.commission import (
    CommissionRateOverride, CommissionSplitsRequest, MilestonePayoutApproval
)
from app.services.lead import (
    create_lead, get_all_leads, get_lead_by_id, update_lead, delete_lead
)
from app.services.meeting import create_meeting, get_meetings_by_lead, get_all_meetings
from app.services.commission import (
    create_commission_for_won_lead, override_commission_rate,
    get_all_commissions, get_commission_summary, get_rep_rankings,
    set_commission_splits, approve_milestone_payout, reverse_milestone_commission
)
from app.services.export import export_to_excel, export_to_pdf
from app.utils.dependencies import get_current_user, get_current_sales, get_current_sales_manager
from typing import Optional

router = APIRouter(prefix="/api/sales", tags=["Sales"])


# ===== LEADS (SRS 3.2) =====

@router.post("/leads", status_code=201)
async def create_new_lead(lead_data: LeadCreate, current_user=Depends(get_current_sales)):
    db_user_id = current_user.get("user_id")

    from app.database.connection import get_db
    from bson import ObjectId
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(db_user_id)})
    sales_rep_name = user["full_name"] if user else "Unknown"

    lead = await create_lead(
        lead_data, 
        sales_rep_id=db_user_id, 
        sales_rep_name=sales_rep_name,
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated"),
        actor_role=current_user.get("role", "system")
    )
    return {"message": "Lead created successfully", "data": lead}


@router.get("/leads")
async def list_leads(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    current_user=Depends(get_current_sales)
):
    role = current_user.get("role")
    sales_rep_id = current_user.get("user_id") if role == "sales_rep" else None
    leads = await get_all_leads(status=status, sales_rep_id=sales_rep_id, platform=platform)
    return {"message": "Success", "data": leads, "total": len(leads)}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, current_user=Depends(get_current_sales)):
    lead = await get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.get("role") == "sales_rep" and lead["sales_rep_id"] != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="You can only view your own leads")

    return {"message": "Success", "data": lead}


@router.put("/leads/{lead_id}")
async def update_existing_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    current_user=Depends(get_current_sales)
):
    """When status moves to Won, commission record is created automatically (SAL-01/02)."""
    role = current_user.get("role")

    lead = await get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if role == "sales_rep" and lead["sales_rep_id"] != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="You can only update your own leads")

    updated_lead, flag = await update_lead(
        lead_id, 
        lead_data, 
        updated_by_role=role,
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated")
    )
    if updated_lead is None:
        raise HTTPException(status_code=403, detail=flag)

    if flag == "WON_TRANSITION":
        await create_commission_for_won_lead(lead_id)

    return {"message": "Lead updated successfully", "data": updated_lead}


@router.delete("/leads/{lead_id}")
async def delete_existing_lead(lead_id: str, current_user=Depends(get_current_sales_manager)):
    await delete_lead(
        lead_id,
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated"),
        actor_role=current_user.get("role", "system")
    )
    return {"message": "Lead deleted successfully"}


# ===== MEETINGS (SRS 3.2.2) =====

@router.post("/meetings", status_code=201)
async def log_meeting(meeting_data: MeetingCreate, current_user=Depends(get_current_sales)):
    meeting, error = await create_meeting(meeting_data, created_by=current_user.get("user_id"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Meeting logged successfully", "data": meeting}


@router.get("/meetings/lead/{lead_id}")
async def get_lead_meetings(lead_id: str, current_user=Depends(get_current_sales)):
    meetings = await get_meetings_by_lead(lead_id)
    return {"message": "Success", "data": meetings}


@router.get("/meetings")
async def list_all_meetings(
    requires_ceo: Optional[bool] = Query(None),
    current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["super_admin", "sales_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    meetings = await get_all_meetings(requires_ceo)
    return {"message": "Success", "data": meetings}


# ===== SALES REPS LOOKUP (used by Finance module's Contract creation form) =====

@router.get("/reps")
async def list_sales_reps(current_user=Depends(get_current_user)):
    """
    Returns active sales reps for use in dropdowns (e.g. assigning a
    sales rep to a Finance contract). Per SRS role split, contracts are
    a Finance Manager responsibility, with Sales Manager also needing
    visibility into team assignments. Sales Reps themselves do not need
    this lookup, so they are excluded here.
    """
    if current_user.get("role") not in ["super_admin", "finance_manager", "sales_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.database.connection import get_db
    db = get_db()
    reps = await db.users.find(
        {"role": "sales_rep", "is_active": True}
    ).to_list(1000)

    return {
        "message": "Success",
        "data": [
            {
                "id": str(rep["_id"]),
                "full_name": rep["full_name"],
                "email": rep["email"]
            }
            for rep in reps
        ]
    }


# ===== COMMISSIONS (SAL-01 to SAL-06) =====

@router.get("/commissions")
async def list_commissions(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_sales)
):
    """status filters by overall_status: Pending, Approved, Paid, Cancelled, Reversed."""
    role = current_user.get("role")
    sales_rep_id = current_user.get("user_id") if role == "sales_rep" else None
    commissions = await get_all_commissions(status=status, sales_rep_id=sales_rep_id)
    return {"message": "Success", "data": commissions, "total": len(commissions)}


@router.get("/commissions/summary")
async def commission_summary(current_user=Depends(get_current_sales)):
    role = current_user.get("role")
    sales_rep_id = current_user.get("user_id") if role == "sales_rep" else None
    summary = await get_commission_summary(sales_rep_id=sales_rep_id)
    return {"message": "Success", "data": summary}


@router.get("/commissions/rankings")
async def commission_rankings(current_user=Depends(get_current_sales_manager)):
    rankings = await get_rep_rankings()
    return {"message": "Success", "data": rankings}


@router.put("/commissions/{commission_id}/rate")
async def update_commission_rate(
    commission_id: str,
    override: CommissionRateOverride,
    current_user=Depends(get_current_user)
):
    commission, error = await override_commission_rate(
        commission_id, 
        override, 
        updated_by_role=current_user.get("role"),
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated")
    )
    if error:
        raise HTTPException(status_code=403, detail=error)
    return {"message": "Commission rate updated successfully", "data": commission}


@router.put("/commissions/{commission_id}/splits")
async def update_commission_splits(
    commission_id: str,
    request: CommissionSplitsRequest,
    current_user=Depends(get_current_user)
):
    commission, error = await set_commission_splits(
        commission_id, 
        request.splits, 
        updated_by_role=current_user.get("role"),
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Commission splits updated successfully", "data": commission}


@router.put("/commissions/{commission_id}/approve-milestone")
async def approve_commission_milestone(
    commission_id: str,
    approval: MilestonePayoutApproval,
    current_user=Depends(get_current_user)
):
    """SAL-04: Approve a specific milestone's commission payout."""
    commission, error = await approve_milestone_payout(
        commission_id, 
        approval.milestone_id,
        approved_by=current_user.get("user_id"),
        approver_role=current_user.get("role"),
        actor_name=current_user.get("full_name", "System Automated")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Milestone commission payout approved successfully", "data": commission}


@router.put("/commissions/{commission_id}/reverse-milestone")
async def reverse_commission_milestone(
    commission_id: str,
    milestone_id: str,
    current_user=Depends(get_current_user)
):
    """SAL-06: Clawback - reverse a previously approved/paid milestone commission."""
    commission, error = await reverse_milestone_commission(
        commission_id, 
        milestone_id,
        reversed_by_role=current_user.get("role"),
        actor_id=current_user.get("user_id", "system"),
        actor_name=current_user.get("full_name", "System Automated")
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Commission milestone reversed successfully", "data": commission}


# ===== EXPORTS (SAL-08) =====

COMMISSION_EXPORT_COLUMNS = [
    ("commission_id", "Commission ID"),
    ("lead_id", "Lead ID"),
    ("sales_rep_name", "Sales Rep"),
    ("total_contract_value", "Contract Value"),
    ("rate", "Rate (%)"),
    ("total_commission_calculated", "Total Commission"),
    ("overall_status", "Status"),
]


@router.get("/commissions/export/excel")
async def export_commissions_excel(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_sales)
):
    role = current_user.get("role")
    sales_rep_id = current_user.get("user_id") if role == "sales_rep" else None
    commissions = await get_all_commissions(status=status, sales_rep_id=sales_rep_id)
    return export_to_excel(commissions, COMMISSION_EXPORT_COLUMNS, title="Commission Report")


@router.get("/commissions/export/pdf")
async def export_commissions_pdf(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_sales)
):
    role = current_user.get("role")
    sales_rep_id = current_user.get("user_id") if role == "sales_rep" else None
    commissions = await get_all_commissions(status=status, sales_rep_id=sales_rep_id)
    return export_to_pdf(commissions, COMMISSION_EXPORT_COLUMNS, title="Commission Report")