from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

ExpenseCategory = Literal[
    "Office Rent & Utilities",
    "Software Subscriptions",
    "Marketing & Advertising",
    "Travel & Accommodation",
    "Employee Benefits & Training",
    "Equipment & Asset Purchases",
    "Miscellaneous"
]

ExpenseStatus = Literal["Pending", "Approved", "Rejected"]


class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: float
    expense_date: date
    description: str
    vendor_name: Optional[str] = None
    receipt_base64: Optional[str] = None  # image/PDF receipt, stored as base64


class ExpenseStatusUpdate(BaseModel):
    status: ExpenseStatus
    comments: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: str
    expense_id: str
    category: str
    amount: float
    expense_date: str
    description: str
    vendor_name: Optional[str] = None
    has_receipt: bool = False
    status: str
    submitted_by: str
    submitted_by_name: str
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    requires_ceo_approval: bool
    created_at: datetime
    updated_at: Optional[datetime] = None