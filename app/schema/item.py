from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import IndexModel, ASCENDING
from enum import Enum
from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class LimitType(str, Enum):
    UP_TO = "UP_TO"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    ALL = "ALL"


class OptionLimitType(str, Enum):
    UP_TO = "UP_TO"
    UNLIMITED = "UNLIMITED"


class CustomizationOption(BaseModel):
    name: str
    price_modifier: float = 0.0
    max_quantity: Optional[int] = 1


class CustomizationRule(BaseModel):
    name: str
    description: Optional[str] = ""
    is_required: bool = Field(alias="isRequired", default=False)
    limit_type: LimitType = Field(alias="limitType", default=LimitType.UP_TO)
    limit: int
    options: List[CustomizationOption] = Field(default_factory=list)


class ItemCreate(BaseModel):
    name: str
    price: float
    restaurant_id: str = Field(..., alias="restaurantId")
    category_id: str = Field(..., alias="categoryId")
    description: Optional[str] = ""
    customizations: List[CustomizationRule] = Field(default_factory=list, alias="customizations")


class ItemBase(ItemCreate):
    image_url: str = Field(..., alias="imageUrl")

    # Optional
    is_available: bool = Field(default=True, alias="isAvailable")
    slug: Optional[str] = None


ItemUpdate = make_optional_model(ItemBase)


class Item(ItemBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class ItemDocument(Document, Item):

    def to_response(self):
        return Item(**self.model_dump(by_alias=True))

    class Settings:
        name = "items"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True, name="idx_slug")
        ]


