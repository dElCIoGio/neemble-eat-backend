from datetime import datetime
from enum import Enum
from typing import List, Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class OrderPrepStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

class OrderCustomizationSelection(BaseModel):
    rule_name: str  # Name of the customization rule (e.g., "Choose Side")
    selected_options: List[str]  # What options the customer picked


class OrderBase(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    item_id: str = Field(..., alias="itemId")
    order_time: datetime = Field(default_factory=datetime.now, alias="orderTime")

    quantity: int
    unit_price: float = Field(default=0.0, alias="unitPrice")
    total: float = Field(default=0.0)
    ordered_item_name: Optional[str] = Field(default=None, alias="orderedItemName")
    restaurant_id: str = Field(..., alias="restaurantId")

    prep_status: OrderPrepStatus = Field(default=OrderPrepStatus.QUEUED, alias="prepStatus")

    customizations: List[OrderCustomizationSelection] = Field(default_factory=list)
    additional_note: Optional[str] = Field(default=None, alias="additionalNote")


class OrderCreate(OrderBase):
    pass

OrderUpdate = make_optional_model(OrderBase)

class Order(OrderBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class OrderDocument(Document, Order):
    def to_response(self):
        return Order(**self.model_dump(by_alias=True))

    class Settings:
        name = "orders"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("sessionId", ASCENDING)], name="idx_session_id"),
            IndexModel([("prepStatus", ASCENDING)], name="idx_prep_status"),
        ]