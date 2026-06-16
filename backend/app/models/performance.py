# app/models/performance.py
#
# Performance Review model (SRS 6.6).
# Review cycles: monthly / quarterly / annual.
# Rating scale: text categories (Poor / Average / Good / Excellent).

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date

ReviewCycle = Literal["Monthly", "Quarterly", "Annual"]
RatingScale = Literal["Poor", "Average", "Good", "Excellent"]
ReviewStatus = Literal["Draft", "Self-Assessment Pending", "Manager Review Pending", "Completed"]


class KPIScore(BaseModel):
    """Individual KPI with its own rating, part of a review."""
    kpi_name: str
    description: Optional[str] = None
    self_rating: Optional[RatingScale] = None
    manager_rating: Optional[RatingScale] = None
    comments: Optional[str] = None


class PerformanceReviewCreate(BaseModel):
    """HR Manager or CEO creates a new review cycle for an employee."""
    employee_id: str
    cycle: ReviewCycle
    period_start: date
    period_end: date
    kpis: list[KPIScore] = []


class SelfAssessmentSubmit(BaseModel):
    """Employee fills in their self-assessment for each KPI."""
    kpis: list[KPIScore]
    self_comments: Optional[str] = None


class ManagerAssessmentSubmit(BaseModel):
    """Reporting manager / HR fills in manager assessment and final rating."""
    kpis: list[KPIScore]
    manager_comments: Optional[str] = None
    final_rating: RatingScale
    feeds_into_increment: bool = False


class PerformanceReviewResponse(BaseModel):
    id: str
    review_id: str
    employee_id: str
    employee_name: str
    cycle: str
    period_start: str
    period_end: str
    status: str
    kpis: list[KPIScore] = []
    self_comments: Optional[str] = None
    manager_comments: Optional[str] = None
    final_rating: Optional[str] = None
    feeds_into_increment: bool = False
    created_by: str
    created_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None