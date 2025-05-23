from typing import List, Optional

from beanie import Indexed, Document
from bson import ObjectId
from pydantic import Field, BaseModel, EmailStr
from pymongo import IndexModel

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model

class UserPreferences(BaseModel):
    language: Optional[str] = Field(default="pt", description="Preferred language (default: Portuguese)")
    notifications_enabled: Optional[bool] = Field(alias="notificationsEnabled", default=True, description="Allow notifications")
    dark_mode: Optional[bool] = Field(alias="darkMode", default=False, description="UI dark mode preference")

class UserRestaurantMembership(BaseModel):
    role_id: str = Field(..., alias="roleId")
    is_active: bool = Field(alias="isActive", default=True)

class UserBase(BaseModel):
    firebase_uuid: str = Field(..., alias="firebaseUUID")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: EmailStr
    phone_number: str = Field(..., alias="phoneNumber")

    # Optional Fields
    current_restaurant_id: Optional[str] = Field(alias="currentRestaurantId", default=None)
    is_admin: Optional[bool] = Field(alias="isAdmin", default=False)
    is_developer: Optional[bool] = Field(alias="isDeveloper", default=False)
    is_verified: Optional[bool] = Field(alias="isVerified", default=False)
    is_active: Optional[bool] = Field(alias="isActive", default=False)
    is_onboarding_completed: Optional[bool] = Field(alias="isOnboardingCompleted", default=False)
    memberships: List[UserRestaurantMembership] = Field(default_factory=list)
    preferences: Optional[UserPreferences] = Field(default_factory=UserPreferences)


class UserCreate(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: EmailStr
    phone_number: str = Field(..., alias="phoneNumber")


UserUpdate = make_optional_model(UserBase)

class User(UserBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class UserDocument(Document, User):
    email: Indexed(EmailStr, unique=True, name="idx_email")  # Ensure email is unique
    firebase_uid: Indexed(str, unique=True, name="idx_firebase_uid")

    def to_response(self):
        return User(**self.model_dump(by_alias=True))

    class Settings:
        name = "users"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel(
                "email",
                unique=True,
                name="idx_email"
            ),
            IndexModel(
                "firebase_uid",
                unique=True,
                name="idx_firebase_uid"
            )
        ]