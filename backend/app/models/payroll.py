from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

PayrollBatchStatus = Literal["Draft", "Pending Review", "Pending Approval", "Approved", "Paid"]


class PayrollRunRequest(BaseModel):
    month: int
    year: int


class PayrollBatchApproval(BaseModel):
    comments: Optional[str] = None


class PayrollRecordResponse(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    basic_salary: float
    allowances_total: float
    deductions_total: float
    commission_amount: float
    bonus: float
    gross_pay: float
    net_pay: float


class PayrollBatchResponse(BaseModel):
    id: str
    batch_id: str
    month: int
    year: int
    status: str
    total_employees: int
    total_gross: float
    total_net: float
    total_commission: float
    records: list[PayrollRecordResponse]
    initiated_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None