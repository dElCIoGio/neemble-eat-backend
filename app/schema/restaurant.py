from typing import Optional, List

from beanie import Document
from bson import ObjectId
from pydantic import Field, BaseModel
from pymongo import IndexModel, ASCENDING

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class RestaurantCreate(BaseModel):
    name: str
    address: str
    description: str
    phone_number: str = Field(..., alias="phoneNumber")
    banner_url: Optional[str] = Field(default=None, alias="bannerUrl")


class OpeningHours(BaseModel):
    monday: Optional[str] = Field(default="09:00-22:00")
    tuesday: Optional[str] = Field(default="09:00-22:00")
    wednesday: Optional[str] = Field(default="09:00-22:00")
    thursday: Optional[str] = Field(default="09:00-22:00")
    friday: Optional[str] = Field(default="09:00-23:00")
    saturday: Optional[str] = Field(default="10:00-23:00")
    sunday: Optional[str] = Field(default="10:00-20:00")


class RestaurantSettings(BaseModel):
    accepts_online_orders: bool = Field(default=True, description="Allow customers to order online via QR")
    auto_accept_orders: bool = Field(default=False, description="Automatically accept incoming orders without manual confirmation")
    opening_hours: Optional[OpeningHours] = Field(alias="openingHours", description="Restaurant opening hours by day")


class RestaurantBase(RestaurantCreate):

    # Optional fields
    is_active: bool = Field(alias="isActive", default=False, description="Whether the restaurant is active or deactivated")
    menu_ids: List[str] = Field(default_factory=list, alias="menuIds")     # Menus
    table_ids: List[str] = Field(default_factory=list, alias="tableIds")    # Tables
    session_ids: List[str] = Field(default_factory=list, alias="sessionIds") # Sessions
    order_ids: List[str] = Field(default_factory=list, alias="orderIds")    # Orders

    settings: Optional[RestaurantSettings] = Field(default_factory=RestaurantSettings)


RestaurantUpdate = make_optional_model(RestaurantBase)

class Restaurant(RestaurantBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class RestaurantDocument(Document, Restaurant):


    def to_response(self):
        return Restaurant(**self.model_dump(by_alias=True))

    class Settings:
        name = "restaurants"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel([("name", ASCENDING)], name="idx_name"),
            IndexModel([("isActive", ASCENDING)], name="idx_is_active"),
            # Optional if you want to guarantee unique phone numbers:
            IndexModel([("phoneNumber", ASCENDING)], unique=True, name="idx_phone_number")
        ]