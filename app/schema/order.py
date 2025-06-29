from datetime import datetime
from enum import Enum
from typing import List, Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


class OrderPrepStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class SelectedOption(BaseModel):
    option_name: str = Field(..., alias="optionName")
    quantity: int
    priceModifier: float

class OrderCustomizationSelection(BaseModel):
    rule_name: str = Field(..., alias="ruleName")  # Name of the customization rule (e.g., "Choose Side")
    selected_options: List[SelectedOption] = Field(alias="selectedOptions", default_factory=list)  # What options the customer picked


class OrderCreate(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    item_id: str = Field(..., alias="itemId")
    quantity: int
    unit_price: float = Field(default=0.0, alias="unitPrice")
    ordered_item_name: Optional[str] = Field(default=None, alias="orderedItemName")
    total: float = Field(default=0.0)
    restaurant_id: str = Field(..., alias="restaurantId")
    customisations: Optional[List[OrderCustomizationSelection]] = Field(default_factory=list)
    additional_note: Optional[str] = Field(default=None, alias="additionalNote")
    table_number: int = Field(..., alias="tableNumber")


class OrderBase(OrderCreate):

    order_time: datetime = Field(default_factory=now_in_luanda, alias="orderTime")
    prep_status: OrderPrepStatus = Field(default=OrderPrepStatus.QUEUED, alias="prepStatus")

    @field_serializer('order_time')
    def serialize_order_time(self, value: datetime, _info):
        return value.isoformat()




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