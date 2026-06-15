from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

CommissionStatus = Literal["Pending", "Approved", "Paid", "On Hold"]


class CommissionSplit(BaseModel):
    """For multi-rep deals — split commission attribution (SRS 3.3.1)."""
    sales_rep_id: str
    sales_rep_name: str
    percentage: float = Field(..., gt=0, le=100)


class CommissionCreate(BaseModel):
    """
    Created automatically when a lead status moves to "Won".
    rate can be overridden per deal by HR Manager or CEO.
    """
    lead_id: str
    contract_value: float
    rate: float = Field(..., gt=0, le=100)  # commission percentage
    splits: Optional[list[CommissionSplit]] = None  # for multi-rep deals


class CommissionRateOverride(BaseModel):
    rate: float = Field(..., gt=0, le=100)


class CommissionStatusUpdate(BaseModel):
    status: CommissionStatus
    comments: Optional[str] = None


class CommissionResponse(BaseModel):
    id: str
    commission_id: str
    lead_id: str
    sales_rep_id: str
    sales_rep_name: str
    contract_value: float
    rate: float
    amount: float
    status: str
    splits: Optional[list[CommissionSplit]] = None
    approved_by: Optional[str] = None
    paid_date: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class CommissionSplitsRequest(BaseModel):
    splits: list[CommissionSplit]