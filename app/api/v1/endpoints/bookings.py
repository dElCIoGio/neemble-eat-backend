from datetime import datetime, timedelta

from beanie.odm.operators.find.comparison import Eq, GTE
from beanie.odm.operators.find.logical import And
from fastapi import APIRouter

from app.schema.bookings import BookingDocument


router = APIRouter()

@router.get("/upcoming/{restaurant_id}")
async def get_restaurant_upcoming_bookings(
    restaurant_id: str
):
    try:
        day = datetime.now()
        day = day.replace(hour=day.hour - 1, minute=0, second=0, microsecond=0)

        bookings = await BookingDocument.find(
            And(
                Eq(BookingDocument.restaurant_id, restaurant_id),
                GTE(BookingDocument.start_time, day),
            )
        ).to_list()

        return bookings
    except Exception as error:
        print(error)
