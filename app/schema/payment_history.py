from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class PaymentStatus(str, Enum):
    PAGO = "pago"
    EM_FALTA = "em_falta"
    EM_ANALISE = "em_analise"


class PaymentHistoryCreate(BaseModel):
    subscription_id: str = Field(..., alias="subscriptionId")
    period: str
    amount: str
    status: PaymentStatus
    payment_date: datetime = Field(..., alias="paymentDate")
    receipt_url: Optional[str] = Field(default=None, alias="receiptUrl")


class PaymentHistoryBase(PaymentHistoryCreate):
    pass


PaymentHistoryUpdate = make_optional_model(PaymentHistoryBase)


class PaymentHistory(PaymentHistoryBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class PaymentHistoryDocument(Document, PaymentHistory):
    def to_response(self):
        return PaymentHistory(**self.model_dump(by_alias=True))

    class Settings:
        name = "payment_history"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("subscriptionId", ASCENDING)], name="idx_subscription_id"),
            IndexModel([("status", ASCENDING)], name="idx_status"),
        ]
