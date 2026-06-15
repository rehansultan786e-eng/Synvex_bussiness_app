from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DepartmentCreate(BaseModel):
    department_name: str
    department_code: str
    manager_name: str
    description: Optional[str] = None

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    manager_name: Optional[str] = None
    description: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: str
    department_name: str
    department_code: str
    manager_name: str
    description: Optional[str]
    total_employees: int
    created_at: datetime