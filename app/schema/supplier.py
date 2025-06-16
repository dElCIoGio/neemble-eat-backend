from datetime import datetime
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class SupplierCreate(BaseModel):
    name: str
    contact: str
    email: str
    restaurant_id: str = Field(..., alias="restaurantId")
    phone: str
    address: str
    products: list[str] = Field(default_factory=list)
    rating: float


class SupplierBase(SupplierCreate):
    last_order: Optional[datetime] = Field(default=None, alias="lastOrder")


SupplierUpdate = make_optional_model(SupplierBase)


class Supplier(SupplierBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class SupplierDocument(Document, Supplier):
    def to_response(self):
        return Supplier(**self.model_dump(by_alias=True))

    class Settings:
        name = "suppliers"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("name", ASCENDING)], name="idx_name"),
        ]
