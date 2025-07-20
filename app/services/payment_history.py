from datetime import datetime
from typing import Optional, List

from fastapi import UploadFile

from app.models.payment_history import PaymentHistoryModel
from app.schema import payment_history as payment_schema
from app.services.google_bucket import get_google_bucket_manager

payment_history_model = PaymentHistoryModel()


async def list_payments(
    subscription_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    status: Optional[payment_schema.PaymentStatus] = None,
) -> List[payment_schema.PaymentHistoryDocument]:
    filters: dict = {"subscriptionId": subscription_id}

    if from_date or to_date:
        date_filter: dict = {}
        if from_date:
            date_filter["$gte"] = from_date
        if to_date:
            date_filter["$lte"] = to_date
        filters["paymentDate"] = date_filter

    if status:
        filters["status"] = status

    return await payment_history_model.get_by_fields(filters)


async def add_payment_record(
    data: payment_schema.PaymentHistoryCreate,
) -> payment_schema.PaymentHistoryDocument:
    return await payment_history_model.create(data.model_dump(by_alias=True))


async def save_payment_proof(
    file: UploadFile, subscription_id: str
):
    manager = get_google_bucket_manager()
    folder = f"subscriptions/{subscription_id}/payments"
    return manager.upload_image(
        await file.read(), filename=file.filename, folder=folder, public=True
    )

