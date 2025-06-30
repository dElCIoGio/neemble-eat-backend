from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class NotificationType(str, Enum):
    SYSTEM="system"
    DATA="data"
    FINANCES="finances"
    NOTICE="notice"

class NotificationPriority(str, Enum):
    LOW="low"
    MEDIUM="medium"
    HIGH="high"


class NotificationCreate(BaseModel):
    restaurant_id: str = Field(..., alias="restaurantId")
    user_id: str = Field(..., alias="userId")
    notification_type: NotificationType = Field(..., alias="notificationType")
    title: str
    message: str
    category: str
    priority: NotificationPriority


class NotificationBase(NotificationCreate):
    is_read: bool = Field(..., alias="isRead")
    read_on: Optional[datetime] = Field(default=None, alias="readOn")

    @field_serializer('read_on')
    def serialize_read_on(self, value: datetime, _info):
        if value is not None:
            return value.isoformat()
        return value




NotificationUpdate = make_optional_model(NotificationBase)


class Notification(NotificationBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class NotificationDocument(Document, Notification):

    def to_response(self):
        return Notification(**self.model_dump(by_alias=True))

    class Settings:
        name = "notifications"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("userId", ASCENDING), ("restaurantId", ASCENDING)], name="idx_user_restaurant"),
        ]