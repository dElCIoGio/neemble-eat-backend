from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.schema.collection_id.object_id import PyObjectId


class DocumentId(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.now, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True
    )
