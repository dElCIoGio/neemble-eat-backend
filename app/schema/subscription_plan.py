from enum import Enum
from typing import List, Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class RecurringInterval(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    currency: str = "USD"
    interval: RecurringInterval
    features: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    trial_days: Optional[int] = Field(default=0, alias="trialDays")
    is_active: bool = Field(default=True, alias="isActive")


class SubscriptionPlanBase(SubscriptionPlanCreate):
    pass


SubscriptionPlanUpdate = make_optional_model(SubscriptionPlanBase)


class SubscriptionPlan(SubscriptionPlanBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class SubscriptionPlanDocument(Document, SubscriptionPlan):
    def to_response(self):
        return SubscriptionPlan(**self.model_dump(by_alias=True))

    class Settings:
        name = "subscription_plans"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("name", ASCENDING)], name="idx_name"),
            IndexModel([("isActive", ASCENDING)], name="idx_is_active"),
        ]
