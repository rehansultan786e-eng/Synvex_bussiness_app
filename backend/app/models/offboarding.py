# app/models/offboarding.py
#
# Offboarding model (SRS 6.7).
# HR initiates offboarding when an employee resigns or is terminated.
# System generates a checklist: assets to return, knowledge transfer,
# final payslip, experience letter generation. Access revoked on last working date.

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

OffboardingReason = Literal["Resignation", "Termination", "End of Contract", "Other"]
OffboardingStatus = Literal["In Progress", "Completed", "Cancelled"]


class OffboardingInitiate(BaseModel):
    employee_id: str
    reason: OffboardingReason
    last_working_date: date
    notes: Optional[str] = None


class OffboardingChecklistUpdate(BaseModel):
    """HR updates individual checklist items as offboarding progresses."""
    assets_returned: Optional[bool] = None
    knowledge_transfer_completed: Optional[bool] = None
    final_payslip_generated: Optional[bool] = None
    exit_interview_completed: Optional[bool] = None
    access_revoked: Optional[bool] = None


class ExperienceLetterDraft(BaseModel):
    """HR manually edits this draft text before generating the final PDF."""
    letter_body: str


class OffboardingResponse(BaseModel):
    id: str
    offboarding_id: str
    employee_id: str
    employee_name: str
    designation: str
    department: str
    joining_date: str
    reason: str
    last_working_date: str
    status: str
    notes: Optional[str] = None
    checklist: dict
    experience_letter_draft: Optional[str] = None
    experience_letter_generated: bool = False
    initiated_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None