import pytz
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime

from app.schema.collection_id.object_id import PyObjectId
from app.utils.time import now_in_luanda, to_luanda_timezone


class DocumentId(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=now_in_luanda, alias="createdAt")
    updated_at: datetime = Field(default_factory=now_in_luanda, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True
    )

    @field_serializer('created_at', 'updated_at')
    def serialize_date(self, value: datetime, _info):
        date = to_luanda_timezone(value)
        return date.isoformat()


    @field_serializer('id')
    def serialize_id(self, value: PyObjectId, _info):
        return str(value)

    # @field_serializer(datetime, check_fields=False)
    # def serialize_datetime(self, value: datetime, _info):
    #     return value.isoformat()
    #
    # @field_serializer(ObjectId, check_fields=False)
    # def serialize_object_id(self, value: PyObjectId, _info):
    #     return str(value)
