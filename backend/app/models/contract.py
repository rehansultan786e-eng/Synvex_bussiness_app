from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

MilestoneStatus = Literal["Upcoming", "Due", "Received", "Overdue"]
PaymentMethod = Literal["Bank Transfer", "Cash", "Cheque", "Online Payment", "Other"]


class MilestoneCreate(BaseModel):
    description: str
    due_date: date
    amount: float


class MilestoneUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[MilestoneStatus] = None


class MilestonePaymentReceived(BaseModel):
    payment_method: PaymentMethod
    paid_date: date


class MilestoneResponse(BaseModel):
    milestone_id: str
    milestone_number: int
    description: str
    due_date: str
    amount: float
    status: str
    paid_date: Optional[str] = None
    payment_method: Optional[str] = None


class ContractCreate(BaseModel):
    lead_id: Optional[str] = None
    client_name: str
    project_name: str
    start_date: date
    end_date: date
    total_value: float
    currency: str = "USD"
    payment_terms: Optional[str] = None
    sales_rep_id: Optional[str] = None
    sales_rep_name: Optional[str] = None
    milestones: list[MilestoneCreate] = []


class ContractUpdate(BaseModel):
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_value: Optional[float] = None
    currency: Optional[str] = None
    payment_terms: Optional[str] = None
    document_url: Optional[str] = None


class ContractResponse(BaseModel):
    id: str
    contract_id: str
    lead_id: Optional[str] = None
    client_name: str
    project_name: str
    start_date: str
    end_date: str
    total_value: float
    currency: str
    payment_terms: Optional[str] = None
    document_url: Optional[str] = None
    sales_rep_id: Optional[str] = None
    sales_rep_name: Optional[str] = None
    milestones: list[MilestoneResponse] = []
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None