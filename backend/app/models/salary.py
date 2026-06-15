from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

SalaryStatus = Literal["Draft", "Pending Approval", "Approved", "Paid"]
LoanStatus = Literal["Pending", "Approved", "Rejected", "Settled"]


class AllowanceBreakdown(BaseModel):
    transport: float = 0.0
    housing: float = 0.0
    medical: float = 0.0
    other: float = 0.0


class DeductionBreakdown(BaseModel):
    tax: float = 0.0
    loan_repayment: float = 0.0
    other: float = 0.0


class SalaryStructureCreate(BaseModel):
    """Sets up / updates an employee's base salary structure (not month-specific)."""
    employee_id: str
    basic_salary: float
    allowances: AllowanceBreakdown = AllowanceBreakdown()
    deductions: DeductionBreakdown = DeductionBreakdown()


class SalaryStructureUpdate(BaseModel):
    basic_salary: Optional[float] = None
    allowances: Optional[AllowanceBreakdown] = None
    deductions: Optional[DeductionBreakdown] = None


class SalaryRecordResponse(BaseModel):
    """A monthly salary/payroll record for one employee."""
    id: str
    salary_id: str
    employee_id: str
    employee_name: str
    month: int
    year: int
    basic_salary: float
    allowances: AllowanceBreakdown
    deductions: DeductionBreakdown
    commission_amount: float = 0.0
    bonus: float = 0.0
    advance_deduction: float = 0.0
    gross_pay: float
    net_pay: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class SalaryAdvanceRequest(BaseModel):
    amount: float
    reason: str


class SalaryAdvanceStatusUpdate(BaseModel):
    status: LoanStatus
    comments: Optional[str] = None


class SalaryAdvanceResponse(BaseModel):
    id: str
    advance_id: str
    employee_id: str
    employee_name: str
    amount: float
    reason: str
    status: str
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    deducted: bool = False
    created_at: datetime