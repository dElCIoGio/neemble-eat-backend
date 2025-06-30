from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.user import UserModel
from app.schema import notification as notification_schema
from app.services import notification as notification_service
from app.utils.auth import get_current_user

router = APIRouter()
user_model = UserModel()


@router.post("/")
async def create_notification(data: notification_schema.NotificationCreate):
    notification = await notification_service.create_notification(data)
    return notification.to_response()


@router.get("/")
async def list_notifications(
    n_type: Optional[notification_schema.NotificationType] = Query(None, alias="type"),
    is_read: Optional[bool] = Query(None, alias="is_read"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    firebase_uid: str = Depends(get_current_user),
):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = await notification_service.list_notifications(
        str(user.id), n_type=n_type, is_read=is_read, search=search, page=page
    )
    return [n.to_response() for n in notifications]


@router.get("/unread-count")
async def unread_count(firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count = await notification_service.count_unread_notifications(str(user.id))
    return {"unread": count}


@router.get("/{notification_id}")
async def get_notification(notification_id: str, firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = await notification_service.get_notification(notification_id)
    if not notification or notification.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification.to_response()


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str, firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = await notification_service.get_notification(notification_id)
    if not notification or notification.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")

    updated = await notification_service.mark_notification_read(notification_id)
    return updated.to_response() if updated else None


@router.post("/{notification_id}/unread")
async def mark_notification_unread(notification_id: str, firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = await notification_service.get_notification(notification_id)
    if not notification or notification.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")

    updated = await notification_service.mark_notification_unread(notification_id)
    return updated.to_response() if updated else None


@router.post("/read-all")
async def mark_all_read(firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count = await notification_service.mark_all_notifications_read(str(user.id))
    return {"updated": count}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, firebase_uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = await notification_service.get_notification(notification_id)
    if not notification or notification.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")

    deleted = await notification_service.delete_notification(notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return True
