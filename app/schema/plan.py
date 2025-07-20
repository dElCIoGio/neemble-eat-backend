from typing import List, Optional

from enum import Enum

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.schema.subscription_plan import RecurringInterval


class Currency(str, Enum):
    AOA = "AOA"
    USD = "USD"


class PlanLimits(BaseModel):
    restaurants: int
    tables: int
    reservations: int
    menu_items: int
    staff: int


class PlanCreate(BaseModel):
    name: str
    price: float
    currency: Optional["Currency"] = None
    interval: Optional[RecurringInterval] = None
    description: Optional[str] = None
    popular: Optional[bool] = False
    features: List[str] = Field(default_factory=list)
    limits: PlanLimits


class PlanBase(PlanCreate):
    pass


PlanUpdate = make_optional_model(PlanBase)


class Plan(PlanBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class PlanDocument(Document, Plan):
    def to_response(self):
        return Plan(**self.model_dump(by_alias=True))

    class Settings:
        name = "plans"
        bson_encoders = {ObjectId: str}

