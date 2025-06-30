from datetime import datetime
from enum import Enum
from typing import Optional, List

from beanie import Document
from bson import ObjectId
from pydantic import Field, BaseModel, conint, field_serializer, field_validator
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


class TableSessionStatus(str, Enum):
    ACTIVE = "active"
    PAID = "paid"
    NEED_BILL = "needs bill"
    CANCELLED = "cancelled"
    CLOSED = "closed"

class TableSessionReview(BaseModel):
    stars: conint(ge=1, le=5) = Field(..., description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(default=None, description="Optional written feedback from the customer")

class TableSessionBase(BaseModel):
    table_id: str = Field(..., alias="tableId")
    restaurant_id: str = Field(..., alias="restaurantId")
    invoice_id: Optional[str] = Field(default=None, alias="invoiceId")
    start_time: datetime = Field(default_factory=now_in_luanda, alias="startTime")
    end_time: Optional[datetime] = Field(default=None, alias="endTime")
    orders: List[str] = Field(default_factory=list)
    status: TableSessionStatus = Field(default=TableSessionStatus.ACTIVE)
    total: Optional[float] = None
    review: Optional[TableSessionReview] = None

    @field_serializer('start_time')
    def serialize_start_time(self, value: datetime, _info):
        return value.isoformat()


    @field_serializer('end_time')
    def serialize_end_time(self, value: datetime, _info):
        if value is not None:
            return value.isoformat()
        return value


class TableSessionCreate(TableSessionBase):

    @field_validator('start_time', mode='before')
    def parse_end_time(cls, value: datetime):
        if isinstance(value, datetime):
            return now_in_luanda()
        return value

TableSessionUpdate = make_optional_model(TableSessionBase)

class TableSession(TableSessionBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


class TableSessionDocument(Document, TableSession):
    def to_response(self):
        return TableSession(**self.model_dump(by_alias=True))

    class Settings:
        name = "table_sessions"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("tableId", ASCENDING), ("status", ASCENDING)], name="idx_table_active_status"),
            IndexModel([("restaurantId", ASCENDING)], name="idx_restaurant"),
            IndexModel([("status", ASCENDING)], name="idx_status")
        ]