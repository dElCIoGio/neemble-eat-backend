from datetime import datetime

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class SaleCreate(BaseModel):
    dish_name: str = Field(..., alias="dishName")
    quantity: int
    date: datetime
    restaurant_id: str = Field(..., alias="restaurantId")
    total: float


class SaleBase(SaleCreate):
    pass


SaleUpdate = make_optional_model(SaleBase)


class Sale(SaleBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class SaleDocument(Document, Sale):
    def to_response(self):
        return Sale(**self.model_dump(by_alias=True))

    class Settings:
        name = "sales"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("date", ASCENDING)], name="idx_date"),
        ]
