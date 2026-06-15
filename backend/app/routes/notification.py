from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.notification import (
    get_all_notifications, mark_notification_read,
    mark_all_read, get_unread_count
)
from app.utils.dependencies import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/")
async def get_notifications(
    is_read: Optional[bool] = Query(None),
    current_user=Depends(get_current_user)
):
    notifications = await get_all_notifications(current_user.get("user_id"), is_read)
    return {"message": "Success", "data": notifications, "total": len(notifications)}


@router.get("/unread-count")
async def unread_count(current_user=Depends(get_current_user)):
    count = await get_unread_count(current_user.get("user_id"))
    return {"unread_count": count}


@router.put("/{notification_id}/read")
async def read_notification(notification_id: str, current_user=Depends(get_current_user)):
    await mark_notification_read(notification_id, current_user.get("user_id"))
    return {"message": "Notification marked as read"}


@router.put("/mark-all-read")
async def read_all_notifications(current_user=Depends(get_current_user)):
    await mark_all_read(current_user.get("user_id"))
    return {"message": "All notifications marked as read"}