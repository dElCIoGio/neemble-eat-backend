from datetime import datetime

from beanie import Document, Indexed
from bson import ObjectId
from pydantic import Field, BaseModel, EmailStr
from pymongo import IndexModel

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class InvitationCreate(BaseModel):
    name: str
    restaurant_id: str = Field(..., alias="restaurantId")
    manager_id: str = Field(..., alias="managerId")
    role_id: str = Field(..., alias="roleId")

class InvitationBase(InvitationCreate):
    pass


InvitationUpdate = make_optional_model(InvitationBase)


class Invitation(InvitationBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class InvitationDocument(Document, Invitation):
    # expires_at: datetime = Indexed(
    #     datetime, expire_after_seconds=60 * 60 * 24 * 7, name="ttl_expires_at"
    # )
    def to_response(self):
        return Invitation(**self.model_dump(by_alias=True))

    class Settings:
        name = "invitations"
        bson_encoders = {ObjectId: str}
        indexes = [
            IndexModel(
                [("restaurantId", 1)],
                name="idx_restaurant_id"),
            IndexModel("expires_at", expireAfterSeconds=60 * 60 * 24 * 7, name="ttl_expires_at")
        ]