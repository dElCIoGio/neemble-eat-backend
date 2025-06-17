from typing import List

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING
from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class RecipeIngredient(BaseModel):
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    quantity: float
    unit: str


class RecipeCreate(BaseModel):
    dish_name: str = Field(..., alias="dishName")
    ingredients: List[RecipeIngredient]
    servings: int
    cost: float
    restaurant_id: str = Field(..., alias="restaurantId")
    menu_item_id: str = Field(..., alias="menuItemId")


class RecipeBase(RecipeCreate):
    pass


RecipeUpdate = make_optional_model(RecipeBase)


class Recipe(RecipeBase, DocumentId):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class RecipeDocument(Document, Recipe):
    def to_response(self):
        return Recipe(**self.model_dump(by_alias=True))

    class Settings:
        name = "recipes"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("dishName", ASCENDING)], name="idx_dish_name"),
        ]

