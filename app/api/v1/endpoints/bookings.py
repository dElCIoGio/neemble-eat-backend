from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schema.bookings import BookingCreate, BookingUpdate
from app.services import booking as booking_service

router = APIRouter()


@router.post("/")
async def create_booking(data: BookingCreate):
    try:
        booking = await booking_service.create_booking(data.model_dump(by_alias=True))
        return booking.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.to_response()


@router.put("/{booking_id}")
async def update_booking(booking_id: str, data: BookingUpdate):
    updated = await booking_service.update_booking(booking_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found")
    return updated.to_response()


@router.delete("/{booking_id}")
async def delete_booking(booking_id: str):
    deleted = await booking_service.delete_booking(booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")
    return True


@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_bookings(restaurant_id: str):
    bookings = await booking_service.list_bookings_for_restaurant(restaurant_id)
    return [b.to_response() for b in bookings]


@router.get("/table/{table_id}")
async def list_table_bookings(table_id: str):
    bookings = await booking_service.list_bookings_for_table(table_id)
    return [b.to_response() for b in bookings]


@router.get("/upcoming/{restaurant_id}")
async def get_restaurant_upcoming_bookings(restaurant_id: str):
    try:
        bookings = await booking_service.list_upcoming_bookings(restaurant_id)
        return [b.to_response() for b in bookings]
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/date/{restaurant_id}/{day}")
async def get_bookings_by_date(restaurant_id: str, day: str):
    try:
        date = datetime.fromisoformat(day)
        bookings = await booking_service.list_bookings_for_date(restaurant_id, date)
        return [b.to_response() for b in bookings]
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
