from typing import List

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from app.schema.collection_id.document_id import DocumentId  # your existing DocumentId with id, createdAt, updatedAt
from app.utils.make_optional_model import make_optional_model
from enum import Enum


class Sections(Enum):
    GENERAL="Geral"
    MENU="Menu"
    QRCODES="Mesas e QR Code"
    RESERVATIONS="Reservas"

class Permissions(BaseModel):
    can_view: bool = Field(alias="canView", default=False)
    can_edit: bool = Field(alias="canEdit", default=False)
    can_delete: bool = Field(alias="canDelete", default=False)


class SectionPermission(BaseModel):
    section: str
    permissions: Permissions = Field(default_factory=Permissions)


class RoleBase(BaseModel):
    name: str = Field(..., description="Role name, e.g., Manager, Chef")
    description: str = Field(default="", description="Role description")
    permissions: List[SectionPermission] = Field(default_factory=list)
    restaurant_id: str = Field(..., alias="restaurantId")
    level: int = Field(default=0)

    model_config = {
        "populate_by_name": True,
    }


class RoleCreate(RoleBase):
    pass  # Same fields when creating


class Role(RoleBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

RoleUpdate = make_optional_model(RoleBase)

class RoleDocument(Document, Role):
    """Database representation for roles."""

    def to_response(self) -> "Role":
        """Convert document to API response model."""
        return Role(**self.model_dump(by_alias=True))

    class Settings:
        name = "roles"
        bson_encoders = {ObjectId: str}

