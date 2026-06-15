from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InvoiceGenerateRequest(BaseModel):
    contract_id: str
    milestone_id: str


class InvoiceResponse(BaseModel):
    id: str
    invoice_id: str
    contract_id: str
    milestone_id: str
    client_name: str
    project_name: str
    description: str
    amount: float
    currency: str
    pdf_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime