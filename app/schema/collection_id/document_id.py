from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.schema.collection_id.object_id import PyObjectId
from app.utils.time import now_in_luanda


class DocumentId(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=now_in_luanda, alias="createdAt")
    updated_at: datetime = Field(default_factory=now_in_luanda, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True
    )
