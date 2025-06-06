from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import Field, BaseModel
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model



class TableCreate(BaseModel):
    restaurant_id: str = Field(..., alias="restaurantId")
    number: int = Field(..., description="Table number (e.g., 1, 2, 3...)")


class TableBase(TableCreate):
    current_session_id: Optional[str] = Field(default=None, alias="currentSessionId")
    url: Optional[str] = None
    is_active: bool = Field(default=True, alias="isActive", description="Whether the table is active or disabled")

TableUpdate = make_optional_model(TableBase)

class Table(TableBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class TableDocument(Document, Table):
    def to_response(self):
        return Table(**self.model_dump(by_alias=True))

    class Settings:
        name = "tables"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("restaurantId", ASCENDING), ("number", ASCENDING)], unique=True, name="idx_restaurant_number"),
            IndexModel([("restaurantId", ASCENDING)], name="idx_restaurant_id"),
            IndexModel([("isActive", ASCENDING)], name="idx_is_active")
        ]