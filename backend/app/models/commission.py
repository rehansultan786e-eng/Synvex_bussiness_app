from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

CommissionStatus = Literal["Pending", "Approved", "Paid", "On Hold", "Cancelled", "Reversed"]
MilestonePayoutStatus = Literal["Pending", "Approved", "Paid", "Cancelled", "Reversed"]


class CommissionSplit(BaseModel):
    """For multi-rep deals — split commission attribution (SAL-04)."""
    sales_rep_id: str
    sales_rep_name: str
    percentage: float = Field(..., gt=0, le=100)


class MilestonePayout(BaseModel):
    """
    Represents one milestone's proportional commission share.
    Created automatically when a milestone is marked Received in Finance module.
    """
    milestone_id: str
    milestone_amount: float
    commission_share: float
    status: MilestonePayoutStatus = "Pending"
    triggered_by_invoice_id: Optional[str] = None
    payout_cycle_month: Optional[str] = None  # e.g. "July-2026"
    reversed_at: Optional[str] = None
    cancelled_at: Optional[str] = None


class CommissionCreate(BaseModel):
    """
    Created automatically when a lead status moves to Won (SAL-01).
    Stores total potential commission; actual payouts are milestone-driven.
    """
    lead_id: str
    contract_value: float
    rate: float = Field(..., gt=0, le=100)
    splits: Optional[list[CommissionSplit]] = None


class CommissionRateOverride(BaseModel):
    rate: float = Field(..., gt=0, le=100)


class CommissionStatusUpdate(BaseModel):
    status: CommissionStatus
    comments: Optional[str] = None


class CommissionSplitsRequest(BaseModel):
    splits: list[CommissionSplit]


class MilestonePayoutApproval(BaseModel):
    """CEO or Finance Manager approves a specific milestone payout."""
    milestone_id: str
    comments: Optional[str] = None


class CommissionResponse(BaseModel):
    id: str
    commission_id: str
    lead_id: str
    sales_rep_id: str
    sales_rep_name: str
    total_contract_value: float
    rate: float
    total_commission_calculated: float
    milestone_payouts: list[MilestonePayout] = []
    overall_status: str
    splits: Optional[list[CommissionSplit]] = None
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None