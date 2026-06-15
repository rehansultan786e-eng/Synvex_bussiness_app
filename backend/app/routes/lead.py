from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime, date

LeadPlatform = Literal["Upwork", "Direct", "Referral", "Other"]
LeadStatus = Literal["New", "In Discussion", "Meeting Scheduled", "Negotiation", "Won", "Lost"]


class LeadCreate(BaseModel):
    client_name: str
    platform: LeadPlatform
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    service_required: str
    estimated_value: float
    currency: str = "USD"
    first_contact_date: date
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    client_name: Optional[str] = None
    platform: Optional[LeadPlatform] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    service_required: Optional[str] = None
    estimated_value: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    lead_id: str
    sales_rep_id: str
    sales_rep_name: str
    client_name: str
    platform: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_required: str
    estimated_value: float
    currency: str
    status: str
    first_contact_date: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class MeetingPlatform(str):
    pass

MeetingOutcomePlatform = Literal["Zoom", "Google Meet", "In-person", "Other"]


class MeetingCreate(BaseModel):
    lead_id: str
    meeting_date: date
    meeting_time: str
    attendees: list[str]
    platform: MeetingOutcomePlatform
    outcome_notes: Optional[str] = None
    requires_ceo: bool = False


class MeetingResponse(BaseModel):
    id: str
    meeting_id: str
    lead_id: str
    meeting_date: str
    meeting_time: str
    attendees: list[str]
    platform: str
    outcome_notes: Optional[str] = None
    requires_ceo: bool
    created_by: str
    created_at: datetime