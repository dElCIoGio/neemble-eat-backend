from datetime import datetime, timedelta
from typing import List, Optional

from beanie.odm.operators.find.comparison import Eq, GTE, LTE
from beanie.odm.operators.find.logical import And

from app.models.booking import BookingModel
from app.schema import bookings as booking_schema
from app.schema.bookings import BookingDocument

booking_model = BookingModel()


async def create_booking(data: dict) -> booking_schema.BookingDocument:
    return await booking_model.create(data)


async def get_booking(booking_id: str) -> Optional[booking_schema.BookingDocument]:
    return await booking_model.get(booking_id)


async def update_booking(booking_id: str, data: booking_schema.BookingUpdate) -> Optional[booking_schema.BookingDocument]:
    return await booking_model.update(booking_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_booking(booking_id: str) -> bool:
    return await booking_model.delete(booking_id)


async def list_bookings_for_restaurant(restaurant_id: str) -> List[booking_schema.BookingDocument]:
    return await booking_model.get_by_fields({"restaurantId": restaurant_id})


async def list_bookings_for_table(table_id: str) -> List[booking_schema.BookingDocument]:
    return await booking_model.get_by_fields({"tableId": table_id})


async def list_upcoming_bookings(restaurant_id: str) -> List[booking_schema.BookingDocument]:
    day = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    return await BookingDocument.find(
        And(
            Eq(BookingDocument.restaurant_id, restaurant_id),
            GTE(BookingDocument.start_time, day),
        )
    ).to_list()


async def list_bookings_for_date(restaurant_id: str, date: datetime) -> List[booking_schema.BookingDocument]:
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return await BookingDocument.find(
        And(
            Eq(BookingDocument.restaurant_id, restaurant_id),
            GTE(BookingDocument.start_time, start),
            LTE(BookingDocument.start_time, end),
        )
    ).to_list()
