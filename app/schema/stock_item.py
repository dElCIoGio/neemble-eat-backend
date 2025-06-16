from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class StockStatus(str, Enum):
    OK = "OK"
    BAIXO = "Baixo"
    CRITICO = "Cr\u00edtico"


class StockItemCreate(BaseModel):
    name: str
    unit: str
    current_quantity: float = Field(..., alias="currentQuantity")
    min_quantity: float = Field(..., alias="minQuantity")
    last_entry: datetime = Field(..., alias="lastEntry")
    supplier: str
    status: StockStatus
    category: str


class StockItemBase(StockItemCreate):
    max_quantity: Optional[float] = Field(default=None, alias="maxQuantity")
    notes: Optional[str] = None
    cost: Optional[float] = None
    expiry_date: Optional[datetime] = Field(default=None, alias="expiryDate")
    barcode: Optional[str] = None
    location: Optional[str] = None
    auto_reorder: Optional[bool] = Field(default=False, alias="autoReorder")
    reorder_point: Optional[float] = Field(default=None, alias="reorderPoint")
    reorder_quantity: Optional[float] = Field(default=None, alias="reorderQuantity")


StockItemUpdate = make_optional_model(StockItemBase)


class StockItem(StockItemBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class StockItemDocument(Document, StockItem):
    def to_response(self):
        return StockItem(**self.model_dump(by_alias=True))

    class Settings:
        name = "stock_items"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("name", ASCENDING)], name="idx_name"),
            IndexModel([("supplier", ASCENDING)], name="idx_supplier"),
        ]
