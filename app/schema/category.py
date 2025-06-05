from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schema.collection_id.document_id import DocumentId
from beanie import Document
from pymongo import IndexModel, ASCENDING
from app.utils.make_optional_model import make_optional_model


# =====================
# Base Schema
# =====================


class CategoryCreate(BaseModel):
    name: str
    restaurant_id: str = Field(..., alias="restaurantId")
    description: Optional[str] = ""
    menu_id: str = Field(..., alias="menuId")


class CategoryBase(CategoryCreate):

    item_ids: List[str] = Field(default_factory=list, alias="itemIds")

    position: int = 0
    is_active: bool = Field(default=True, alias="isActive")

    tags: Optional[List[str]] = Field(default_factory=list)
    slug: Optional[str] = None


CategoryUpdate = make_optional_model(CategoryBase)


# =====================
# Final Category Model
# =====================

class Category(CategoryBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


# =====================
# Beanie Document
# =====================

class CategoryDocument(Document, Category):
    def to_response(self):
        return Category(**self.model_dump(by_alias=True))

    class Settings:
        name = "menu_categories"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("restaurantId", ASCENDING)], name="idx_restaurant_id"),
            IndexModel([("isActive", ASCENDING)], name="idx_is_active"),
            IndexModel([("position", ASCENDING)], name="idx_position"),
            IndexModel([("slug", ASCENDING)], unique=True, name="idx_slug")
        ]
