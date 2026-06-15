from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PayslipResponse(BaseModel):
    id: str
    payslip_id: str
    employee_id: str
    employee_name: str
    month: int
    year: int
    pdf_url: Optional[str] = None
    generated_at: datetime
    sent_at: Optional[datetime] = None