from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


class StockStatus(str, Enum):
    OK = "OK"
    BAIXO = "Baixo"
    CRITICO = "Critico"


class StockItemCreate(BaseModel):
    name: str
    restaurant_id: str = Field(..., alias="restaurantId")
    unit: str
    current_quantity: float = Field(..., alias="currentQuantity")
    min_quantity: float = Field(..., alias="minQuantity")
    last_entry: str = Field(..., alias="lastEntry")
    supplier: str
    status: StockStatus
    category: str


class StockItemBase(StockItemCreate):
    max_quantity: Optional[float] = Field(default=0, alias="maxQuantity")
    notes: Optional[str] = ""
    cost: Optional[float] = 0.0
    expiry_date: Optional[datetime] = Field(default_factory=now_in_luanda, alias="expiryDate")
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
