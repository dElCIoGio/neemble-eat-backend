from typing import List

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class PlanLimits(BaseModel):
    restaurants: int
    tables: int
    reservations: int
    menu_items: int
    staff: int


class PlanCreate(BaseModel):
    name: str
    price: float
    features: List[str]
    popular: bool
    limits: PlanLimits


class PlanBase(PlanCreate):
    pass


PlanUpdate = make_optional_model(PlanBase)


class Plan(PlanBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class PlanDocument(Document, Plan):
    def to_response(self):
        return Plan(**self.model_dump(by_alias=True))

    class Settings:
        name = "plans"
        bson_encoders = {ObjectId: str}

