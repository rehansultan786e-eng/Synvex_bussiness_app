from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

AssetCategory = Literal[
    "Laptop", "Monitor", "Phone", "Peripheral",
    "Furniture", "Networking", "Other"
]

AssetCondition = Literal["New", "Good", "Fair", "Damaged"]

AssetStatus = Literal["Available", "Assigned", "Under Maintenance", "Disposed"]


class MaintenanceRecord(BaseModel):
    date: date
    issue: str
    cost: float
    vendor: str
    notes: Optional[str] = None


class AssetCreate(BaseModel):
    name: str
    category: AssetCategory
    make: str
    model: str
    serial_number: str
    purchase_date: date
    purchase_cost: float
    vendor: str
    warranty_expiry_date: Optional[date] = None
    condition: AssetCondition = "New"
    notes: Optional[str] = None
    photo_base64: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[AssetCategory] = None
    make: Optional[str] = None
    model: Optional[str] = None
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_expiry_date: Optional[date] = None
    condition: Optional[AssetCondition] = None
    status: Optional[AssetStatus] = None
    notes: Optional[str] = None


class AssetAssignRequest(BaseModel):
    employee_id: str
    assignment_date: date
    expected_return_date: Optional[date] = None
    notes: Optional[str] = None


class AssetReturnRequest(BaseModel):
    return_date: date
    condition_on_return: AssetCondition
    notes: Optional[str] = None


class AssetTransferRequest(BaseModel):
    to_employee_id: str
    transfer_date: date
    notes: Optional[str] = None


class MaintenanceLogRequest(BaseModel):
    date: date
    issue: str
    cost: float
    vendor: str
    notes: Optional[str] = None


class AssetAcknowledgement(BaseModel):
    acknowledged: bool = True


class AssetResponse(BaseModel):
    id: str
    asset_id: str
    name: str
    category: str
    make: str
    model: str
    serial_number: str
    purchase_date: str
    purchase_cost: float
    vendor: str
    warranty_expiry_date: Optional[str] = None
    condition: str
    status: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assignment_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    acknowledged: bool = False
    has_photo: bool = False
    notes: Optional[str] = None
    depreciated_value: Optional[float] = None
    maintenance_history: list = []
    assignment_history: list = []
    created_at: datetime
    updated_at: Optional[datetime] = None