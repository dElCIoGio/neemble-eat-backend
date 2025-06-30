from typing import Optional, List, Dict, Any

from app.utils.time import now_in_luanda

from app.models.notification import NotificationModel
from app.schema import notification as notification_schema

notification_model = NotificationModel()


async def get_notification(notification_id: str) -> Optional[notification_schema.NotificationDocument]:
    return await notification_model.get(notification_id)


async def list_notifications(
    user_id: str,
    n_type: Optional[notification_schema.NotificationType] = None,
    is_read: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> List[notification_schema.NotificationDocument]:
    filters: Dict[str, Any] = {"userId": user_id}
    if n_type:
        filters["notificationType"] = n_type
    if is_read is not None:
        filters["isRead"] = is_read
    if search:
        regex = {"$regex": search, "$options": "i"}
        filters["$or"] = [{"title": regex}, {"message": regex}]

    skip = max(page - 1, 0) * page_size
    return await notification_model.get_by_fields(filters, skip=skip, limit=page_size)


async def count_unread_notifications(user_id: str) -> int:
    filters = {"userId": user_id, "isRead": False}
    return await notification_schema.NotificationDocument.find(filters).count()


async def create_notification(
    data: notification_schema.NotificationCreate,
) -> notification_schema.NotificationDocument:
    payload = data.model_dump(by_alias=False)
    payload["is_read"] = False
    payload["read_on"] = None
    return await notification_model.create(payload)


async def mark_notification_read(
    notification_id: str,
) -> Optional[notification_schema.NotificationDocument]:
    update = {"isRead": True, "readOn": now_in_luanda()}
    return await notification_model.update(notification_id, update)


async def mark_notification_unread(
    notification_id: str,
) -> Optional[notification_schema.NotificationDocument]:
    update = {"isRead": False, "readOn": None}
    return await notification_model.update(notification_id, update)


async def mark_all_notifications_read(user_id: str) -> int:
    coll = notification_schema.NotificationDocument.get_motor_collection()
    result = await coll.update_many(
        {"userId": user_id, "isRead": False},
        {"$set": {"isRead": True, "readOn": now_in_luanda()}},
    )
    return result.modified_count


async def delete_notification(notification_id: str) -> bool:
    return await notification_model.delete(notification_id)
