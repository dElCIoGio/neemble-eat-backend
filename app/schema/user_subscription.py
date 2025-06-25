from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    ENDED = "ended"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    OTHER = "other"


class UserSubscriptionCreate(BaseModel):
    user_id: str = Field(..., alias="userId")
    plan_id: str = Field(..., alias="planId")
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: datetime = Field(default_factory=now_in_luanda, alias="startDate")
    end_date: Optional[datetime] = Field(default=None, alias="endDate")
    payment_method: Optional[PaymentMethod] = Field(default=None, alias="paymentMethod")
    last_payment: Optional[datetime] = Field(default=None, alias="lastPayment")
    next_payment_due: Optional[datetime] = Field(default=None, alias="nextPaymentDue")
    payment_reference: Optional[str] = Field(default=None, alias="paymentReference")
    is_auto_renew: bool = Field(default=True, alias="isAutoRenew")


class UserSubscriptionBase(UserSubscriptionCreate):
    pass


UserSubscriptionUpdate = make_optional_model(UserSubscriptionBase)


class UserSubscription(UserSubscriptionBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class UserSubscriptionDocument(Document, UserSubscription):
    def to_response(self):
        return UserSubscription(**self.model_dump(by_alias=True))

    class Settings:
        name = "user_subscriptions"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("userId", ASCENDING)], name="idx_user_id"),
            IndexModel([("planId", ASCENDING)], name="idx_plan_id"),
            IndexModel([("status", ASCENDING)], name="idx_status"),
        ]
