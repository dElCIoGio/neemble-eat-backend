from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field

from app.schema.collection_id.document_id import DocumentId
from app.utils.make_optional_model import make_optional_model


class BookingBase(BaseModel):
    restaurant_id: str = Field(..., alias="restaurantId")
    table_id: str = Field(..., alias="tableId")
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    number_of_guest: int = Field(..., alias="numberOfGuest")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    phone_number: str = Field(..., alias="phoneNumber")
    email: str = Field(..., alias="email")
    occasion: str = Field(..., alias="occasion")
    notes: str = Field(..., alias="notes")


class BookingCreate(BookingBase):
    pass


BookingUpdate = make_optional_model(BookingBase)


class Booking(BookingBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class BookingDocument(Booking):

    def to_response(self):
        return Booking(**self.model_dump(by_alias=True))

    class Settings:
        name = "bookings"
        bson_encoders = {
            ObjectId: str
        }
        indexes = []