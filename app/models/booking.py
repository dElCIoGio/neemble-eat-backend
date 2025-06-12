from app.db.crud import MongoCrud
from app.schema import bookings as booking_schema


class BookingModel(MongoCrud[booking_schema.BookingDocument]):
    def __init__(self):
        super().__init__(booking_schema.BookingDocument)
