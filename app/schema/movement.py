from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


class MovementType(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"


class MovementCreate(BaseModel):
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    type: MovementType
    quantity: float
    restaurant_id: str = Field(..., alias="restaurantId")
    unit: str
    date: datetime
    reason: str
    user: str
    cost: Optional[float] = None

    @field_serializer('date')
    def serialize_start_time(self, value: datetime, _info):
        return now_in_luanda()


class MovementBase(MovementCreate):
    pass


MovementUpdate = make_optional_model(MovementBase)


class Movement(MovementBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class MovementDocument(Document, Movement):
    def to_response(self):
        return Movement(**self.model_dump(by_alias=True))

    class Settings:
        name = "movements"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("productId", ASCENDING)], name="idx_product_id"),
            IndexModel([("type", ASCENDING)], name="idx_type"),
        ]
