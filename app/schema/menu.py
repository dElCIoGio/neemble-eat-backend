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

class MenuPreferences(BaseModel):
    highlight_featured_items: bool = Field(default=False, description="Highlight featured items at the top", alias="highlightFeaturedItems")
    show_prices: bool = Field(default=True, description="Show item prices in this menu", alias="showPrices")
    show_item_images: bool = Field(default=True, description="Show item images in this menu", alias="showItemImages")

class MenuCreate(BaseModel):
    restaurant_id: str = Field(..., alias="restaurantId")
    name: str
    description: Optional[str] = ""
    is_active: bool = Field(default=True, alias="isActive")
    preferences: Optional[MenuPreferences] = Field(default_factory=MenuPreferences)


class MenuBase(MenuCreate):
    category_ids: List[str] = Field(default_factory=list, alias="categoryIds")
    position: int = 0  # Menu ordering preference (e.g., Lunch = 1, Dinner = 2)
    slug: Optional[str] = None


MenuUpdate = make_optional_model(MenuBase)


# =====================
# Final Menu Model
# =====================

class Menu(MenuBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


# =====================
# Beanie Document
# =====================

class MenuDocument(Document, Menu):
    def to_response(self):
        return Menu(**self.model_dump(by_alias=True))

    class Settings:
        name = "menus"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("restaurantId", ASCENDING)], name="idx_restaurant_id"),
            IndexModel([("isActive", ASCENDING)], name="idx_is_active"),
            IndexModel([("position", ASCENDING)], name="idx_position"),
            IndexModel([("slug", ASCENDING)], unique=True, name="idx_slug")
        ]
