from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schema.collection_id.document_id import DocumentId
from beanie import Document
from pymongo import IndexModel, ASCENDING
from enum import Enum

from app.utils.make_optional_model import make_optional_model
from app.utils.time import now_in_luanda


# =====================
# Status Enum
# =====================

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"

# =====================
# Base Schema
# =====================

class InvoiceBase(BaseModel):
    restaurant_id: str = Field(..., alias="restaurantId")
    session_id: str = Field(..., alias="sessionId")
    orders: List[str] = Field(default_factory=list)

    total: Optional[float] = 0.0
    tax: Optional[float] = None
    discount: Optional[float] = None

    generated_time: datetime = Field(default_factory=now_in_luanda, alias="generatedTime")

    status: InvoiceStatus = Field(default=InvoiceStatus.PENDING)
    is_active: bool = Field(default=True, alias="isActive")

# =====================
# Create / Update
# =====================

class InvoiceCreate(InvoiceBase):
    pass

InvoiceUpdate = make_optional_model(InvoiceBase)

# =====================
# Final Invoice Model
# =====================

class Invoice(InvoiceBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

# =====================
# Beanie Document
# =====================

class InvoiceDocument(Document, Invoice):
    def to_response(self):
        return Invoice(**self.model_dump(by_alias=True))

    class Settings:
        name = "invoices"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("sessionId", ASCENDING)], name="idx_session_id"),
            IndexModel([("restaurantId", ASCENDING)], name="idx_restaurant_id"),
            IndexModel([("status", ASCENDING)], name="idx_status")
        ]
