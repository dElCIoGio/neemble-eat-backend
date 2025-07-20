from app.db.crud import MongoCrud
from app.schema import payment_history as payment_history_schema


class PaymentHistoryModel(MongoCrud[payment_history_schema.PaymentHistoryDocument]):
    def __init__(self) -> None:
        super().__init__(payment_history_schema.PaymentHistoryDocument)
