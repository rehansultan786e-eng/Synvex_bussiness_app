# app/routes/performance.py
#
# Performance Review routes (SRS 6.6).

from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.performance import (
    PerformanceReviewCreate, SelfAssessmentSubmit, ManagerAssessmentSubmit
)
from app.services.performance import (
    create_performance_review, get_review_by_id, get_employee_reviews,
    get_all_reviews, submit_self_assessment, submit_manager_assessment, delete_review
)
from app.utils.dependencies import get_current_user, get_current_hr
from typing import Optional

router = APIRouter(prefix="/api/performance", tags=["Performance Reviews"])


@router.post("/", status_code=201)
async def create_review(
    review_data: PerformanceReviewCreate,
    current_user=Depends(get_current_hr)
):
    """HR Manager or CEO creates a new performance review cycle for an employee."""
    review, error = await create_performance_review(review_data, created_by=current_user.get("user_id"))
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"message": "Performance review created successfully", "data": review}


@router.get("/")
async def list_reviews(
    status: Optional[str] = Query(None),
    cycle: Optional[str] = Query(None),
    current_user=Depends(get_current_hr)
):
    """HR Manager / CEO view: all reviews, optionally filtered."""
    reviews = await get_all_reviews(status=status, cycle=cycle)
    return {"message": "Success", "data": reviews, "total": len(reviews)}


@router.get("/my")
async def my_reviews(current_user=Depends(get_current_user)):
    """Employee self-service: own performance review history (SRS 6.5)."""
    employee_id = current_user.get("employee_id") or current_user.get("user_id")
    reviews = await get_employee_reviews(employee_id)
    return {"message": "Success", "data": reviews, "total": len(reviews)}


@router.get("/employee/{employee_id}")
async def employee_review_history(employee_id: str, current_user=Depends(get_current_hr)):
    """HR/CEO view: performance history for a specific employee."""
    reviews = await get_employee_reviews(employee_id)
    return {"message": "Success", "data": reviews, "total": len(reviews)}


@router.get("/{review_id}")
async def get_review(review_id: str, current_user=Depends(get_current_user)):
    review = await get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    role = current_user.get("role")
    if role not in ["super_admin", "hr_manager"]:
        employee_id = current_user.get("employee_id") or current_user.get("user_id")
        if review["employee_id"] != employee_id:
            raise HTTPException(status_code=403, detail="You can only view your own performance review")

    return {"message": "Success", "data": review}


@router.put("/{review_id}/self-assessment")
async def submit_self_assessment_route(
    review_id: str,
    assessment: SelfAssessmentSubmit,
    current_user=Depends(get_current_user)
):
    """Employee submits self-assessment for their review (SRS 6.6)."""
    employee_id = current_user.get("employee_id") or current_user.get("user_id")
    review, error = await submit_self_assessment(review_id, assessment, employee_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Self-assessment submitted successfully", "data": review}


@router.put("/{review_id}/manager-assessment")
async def submit_manager_assessment_route(
    review_id: str,
    assessment: ManagerAssessmentSubmit,
    current_user=Depends(get_current_hr)
):
    """HR Manager / CEO submits final manager assessment and rating (SRS 6.6)."""
    review, error = await submit_manager_assessment(review_id, assessment, reviewer_role=current_user.get("role"))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Manager assessment submitted - review completed", "data": review}


@router.delete("/{review_id}")
async def delete_review_route(review_id: str, current_user=Depends(get_current_hr)):
    deleted = await delete_review(review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Performance review deleted successfully"}