from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Response

from app.services import payment_history as payment_service
from app.services import subscription as subscription_service
from app.schema import payment_history as payment_schema
from app.utils.auth import get_current_user

router = APIRouter()


@router.get('/history')
async def list_payment_history(
    status: Optional[payment_schema.PaymentStatus] = Query(None),
    from_date: Optional[datetime] = Query(None, alias='from'),
    to_date: Optional[datetime] = Query(None, alias='to'),
    uid: str = Depends(get_current_user),
):
    sub = await subscription_service.get_user_current_subscription(uid)
    if not sub:
        return []
    payments = await payment_service.list_payments(
        str(sub.id),
        from_date=from_date,
        to_date=to_date,
        status=status,
    )
    return [p.to_response() for p in payments]


@router.post('/proofs')
async def upload_payment_proof(
    period: str = Form(...),
    amount: str = Form(...),
    proof_file: UploadFile = File(..., alias='proofFile'),
    uid: str = Depends(get_current_user),
):
    sub = await subscription_service.get_user_current_subscription(uid)
    if not sub:
        raise HTTPException(status_code=404, detail='Subscription not found')

    upload = await payment_service.save_payment_proof(proof_file, str(sub.id))
    if not upload.success:
        raise HTTPException(status_code=500, detail='Failed to upload file')

    data = payment_schema.PaymentHistoryCreate(
        subscriptionId=str(sub.id),
        period=period,
        amount=amount,
        status=payment_schema.PaymentStatus.EM_ANALISE,
        paymentDate=datetime.utcnow(),
        receiptUrl=upload.public_url,
    )
    record = await payment_service.add_payment_record(data)
    return record.to_response()


@router.get('/latest-invoice')
async def get_latest_invoice(uid: str = Depends(get_current_user)):
    sub = await subscription_service.get_user_current_subscription(uid)
    if not sub:
        raise HTTPException(status_code=404, detail='Subscription not found')
    payment = await payment_service.get_latest_payment(str(sub.id))
    if not payment:
        raise HTTPException(status_code=404, detail='No payments found')
    blob = payment_service.generate_invoice_blob(payment)
    return Response(content=blob, media_type='application/octet-stream')


@router.get('/invoice/{payment_id}')
async def download_invoice(payment_id: str):
    payment = await payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found')
    blob = payment_service.generate_invoice_blob(payment)
    return Response(content=blob, media_type='application/octet-stream')
