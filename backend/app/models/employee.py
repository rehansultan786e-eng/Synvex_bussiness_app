# app/models/employee.py
#
# Employee model — extended per SRS Section 6.2 (Onboarding) and
# Section 11 (Entity table: Employees, Users).
#
# UNIFIED LOGIN: "password" here is used once, at creation time, to set
# up the employee's linked login account in the "users" collection
# (see services/employee.py). It is not stored on the employee document
# itself.

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime, date

EmploymentType = Literal["Full-time", "Part-time", "Contract"]


class EmployeeCreate(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    phone: str
    department: str
    designation: str
    joining_date: date
    status: str = "active"
    password: str  # used to create the linked login account

    cnic: Optional[str] = None
    date_of_birth: Optional[date] = None
    personal_email: Optional[EmailStr] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    employment_type: EmploymentType = "Full-time"
    reporting_manager: Optional[str] = None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    status: Optional[str] = None
    password: Optional[str] = None  # if provided, updates the linked login account's password

    cnic: Optional[str] = None
    date_of_birth: Optional[date] = None
    personal_email: Optional[EmailStr] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    reporting_manager: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    full_name: str
    email: str
    phone: str
    department: str
    designation: str
    joining_date: str
    status: str
    created_at: datetime

    cnic: Optional[str] = None
    date_of_birth: Optional[str] = None
    personal_email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    employment_type: str = "Full-time"
    reporting_manager: Optional[str] = None
    salary_id: Optional[str] = None
    onboarding_status: Optional[dict] = None


class OnboardingChecklistUpdate(BaseModel):
    documents_submitted: Optional[bool] = None
    asset_assigned: Optional[bool] = None
    system_access_granted: Optional[bool] = None