# app/services/performance.py
#
# Performance Review service (SRS 6.6).
# Workflow: HR/CEO creates review -> Employee submits self-assessment ->
# Manager/HR submits final assessment + rating -> Completed.
# Performance history is stored per employee. Final rating can optionally
# feed into bonus/salary increment decisions (flagged, handled manually by HR/Finance).

from app.database.connection import get_db
from app.models.performance import (
    PerformanceReviewCreate, SelfAssessmentSubmit, ManagerAssessmentSubmit
)
from datetime import datetime


def review_helper(review) -> dict:
    return {
        "id": str(review["_id"]),
        "review_id": review["review_id"],
        "employee_id": review["employee_id"],
        "employee_name": review["employee_name"],
        "cycle": review["cycle"],
        "period_start": str(review["period_start"]),
        "period_end": str(review["period_end"]),
        "status": review["status"],
        "kpis": review.get("kpis", []),
        "self_comments": review.get("self_comments"),
        "manager_comments": review.get("manager_comments"),
        "final_rating": review.get("final_rating"),
        "feeds_into_increment": review.get("feeds_into_increment", False),
        "created_by": review["created_by"],
        "created_at": review["created_at"],
        "submitted_at": review.get("submitted_at"),
        "completed_at": review.get("completed_at")
    }


async def generate_review_id():
    db = get_db()
    count = await db.performance_reviews.count_documents({})
    return f"PERF-{count + 1:05d}"


async def create_performance_review(review_data: PerformanceReviewCreate, created_by: str):
    """HR Manager or CEO creates a new review cycle for an employee (SRS 6.6)."""
    db = get_db()

    employee = await db.employees.find_one({"employee_id": review_data.employee_id, "is_deleted": False})
    if not employee:
        return None, "Employee not found"

    review_id = await generate_review_id()

    review = {
        "review_id": review_id,
        "employee_id": review_data.employee_id,
        "employee_name": employee["full_name"],
        "cycle": review_data.cycle,
        "period_start": str(review_data.period_start),
        "period_end": str(review_data.period_end),
        "status": "Self-Assessment Pending",
        "kpis": [k.model_dump() for k in review_data.kpis],
        "self_comments": None,
        "manager_comments": None,
        "final_rating": None,
        "feeds_into_increment": False,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "submitted_at": None,
        "completed_at": None
    }

    result = await db.performance_reviews.insert_one(review)
    new_review = await db.performance_reviews.find_one({"_id": result.inserted_id})

    # Notify employee to fill self-assessment
    from app.services.notification import create_notification
    user = await db.users.find_one({"email": employee["email"]})
    notify_id = str(user["_id"]) if user else employee["employee_id"]
    await create_notification(
        user_id=notify_id,
        message=f"A {review_data.cycle.lower()} performance review has been started for you ({review_id}). Please complete your self-assessment.",
        notif_type="performance_review"
    )

    return review_helper(new_review), None


async def get_review_by_id(review_id: str):
    db = get_db()
    review = await db.performance_reviews.find_one({"review_id": review_id})
    if not review:
        return None
    return review_helper(review)


async def get_employee_reviews(employee_id: str):
    """Performance history per employee (SRS 6.6)."""
    db = get_db()
    reviews = await db.performance_reviews.find({"employee_id": employee_id}).sort("created_at", -1).to_list(1000)
    return [review_helper(r) for r in reviews]


async def get_all_reviews(status: str = None, cycle: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if cycle:
        query["cycle"] = cycle
    reviews = await db.performance_reviews.find(query).sort("created_at", -1).to_list(1000)
    return [review_helper(r) for r in reviews]


async def submit_self_assessment(review_id: str, assessment: SelfAssessmentSubmit, employee_id: str):
    """Employee fills self-assessment (SRS 6.6)."""
    db = get_db()
    review = await db.performance_reviews.find_one({"review_id": review_id})
    if not review:
        return None, "Review not found"

    if review["employee_id"] != employee_id:
        return None, "You can only submit your own self-assessment"

    if review["status"] != "Self-Assessment Pending":
        return None, f"Review is in '{review['status']}' status, cannot submit self-assessment"

    # Merge self_rating into existing KPI list (matched by kpi_name)
    existing_kpis = {k["kpi_name"]: k for k in review.get("kpis", [])}
    for incoming in assessment.kpis:
        kpi_dict = incoming.model_dump()
        if incoming.kpi_name in existing_kpis:
            existing_kpis[incoming.kpi_name]["self_rating"] = kpi_dict.get("self_rating")
            existing_kpis[incoming.kpi_name]["comments"] = kpi_dict.get("comments") or existing_kpis[incoming.kpi_name].get("comments")
        else:
            existing_kpis[incoming.kpi_name] = kpi_dict

    await db.performance_reviews.update_one(
        {"review_id": review_id},
        {"$set": {
            "kpis": list(existing_kpis.values()),
            "self_comments": assessment.self_comments,
            "status": "Manager Review Pending",
            "submitted_at": datetime.utcnow()
        }}
    )

    updated = await db.performance_reviews.find_one({"review_id": review_id})

    # Notify HR/CEO that self-assessment is ready for manager review
    from app.services.notification import create_notification
    reviewers = await db.users.find({"role": {"$in": ["super_admin", "hr_manager"]}}).to_list(20)
    for r in reviewers:
        await create_notification(
            user_id=str(r["_id"]),
            message=f"{review['employee_name']} has submitted self-assessment for review {review_id}. Manager review pending.",
            notif_type="performance_review"
        )

    return review_helper(updated), None


async def submit_manager_assessment(review_id: str, assessment: ManagerAssessmentSubmit, reviewer_role: str):
    """Manager/HR/CEO completes the review with final rating (SRS 6.6)."""
    if reviewer_role not in ["super_admin", "hr_manager"]:
        return None, "Only HR Manager or CEO can submit the manager assessment"

    db = get_db()
    review = await db.performance_reviews.find_one({"review_id": review_id})
    if not review:
        return None, "Review not found"

    if review["status"] != "Manager Review Pending":
        return None, f"Review is in '{review['status']}' status, cannot submit manager assessment"

    existing_kpis = {k["kpi_name"]: k for k in review.get("kpis", [])}
    for incoming in assessment.kpis:
        kpi_dict = incoming.model_dump()
        if incoming.kpi_name in existing_kpis:
            existing_kpis[incoming.kpi_name]["manager_rating"] = kpi_dict.get("manager_rating")
            if kpi_dict.get("comments"):
                existing_kpis[incoming.kpi_name]["comments"] = kpi_dict.get("comments")
        else:
            existing_kpis[incoming.kpi_name] = kpi_dict

    await db.performance_reviews.update_one(
        {"review_id": review_id},
        {"$set": {
            "kpis": list(existing_kpis.values()),
            "manager_comments": assessment.manager_comments,
            "final_rating": assessment.final_rating,
            "feeds_into_increment": assessment.feeds_into_increment,
            "status": "Completed",
            "completed_at": datetime.utcnow()
        }}
    )

    updated = await db.performance_reviews.find_one({"review_id": review_id})

    # Notify employee that review is completed
    from app.services.notification import create_notification
    employee = await db.employees.find_one({"employee_id": review["employee_id"]})
    if employee:
        user = await db.users.find_one({"email": employee["email"]})
        notify_id = str(user["_id"]) if user else employee["employee_id"]
        await create_notification(
            user_id=notify_id,
            message=f"Your performance review {review_id} has been completed. Final rating: {assessment.final_rating}.",
            notif_type="performance_review"
        )

    return review_helper(updated), None


async def delete_review(review_id: str):
    db = get_db()
    result = await db.performance_reviews.delete_one({"review_id": review_id})
    return result.deleted_count > 0