from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Body, Query

from app.schema import invoice as invoice_schema
from app.services import invoice as invoice_service
from app.services.invoice import invoice_model

router = APIRouter()




@router.get("/{invoice_id}/data")
async def get_invoice_data(invoice_id: str):
    try:
        data = await invoice_service.get_invoice_data(invoice_id)
        if not data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return data
    except Exception as error:
        print(error)
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/")
async def create_invoice(data: invoice_schema.InvoiceCreate):
    invoice = await invoice_model.create(data.model_dump(by_alias=True))
    return invoice.to_response()


@router.post("/generate/{session_id}")
async def generate_invoice(session_id: str):
    try:
        invoice = await invoice_service.generate_invoice_for_session(session_id)
        return invoice.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/paginate")
async def paginate_invoices(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: datetime = Query(..., alias="fromDate"),
    to_date: datetime = Query(..., alias="toDate")
):
    try:
        filters: Dict[str, Any] = {
            "restaurantId": restaurant_id,
            "createdAt": {
                "$gte": from_date,
                "$lt": to_date
            }
        }
        result = await invoice_model.paginate(filters=filters, limit=limit, cursor=cursor)
        return result
    except Exception as error:
        print(error)


@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_invoices(restaurant_id: str):
    invoices = await invoice_service.list_invoices_for_restaurant(restaurant_id)
    return [i.to_response() for i in invoices]


@router.get("/restaurant/{restaurant_id}/status/{status}")
async def list_restaurant_invoices_by_status(
    restaurant_id: str, status: invoice_schema.InvoiceStatus
):
    filters = {"restaurantId": restaurant_id, "status": status}
    invoices = await invoice_model.get_by_fields(filters)
    return [i.to_response() for i in invoices]


@router.get("/session/{session_id}")
async def get_invoice_by_session(session_id: str):
    invoice = await invoice_service.get_invoice_by_session(session_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice.to_response()


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    invoice = await invoice_model.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice.to_response()


@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, data: invoice_schema.InvoiceUpdate = Body(...)):
    updated = await invoice_model.update(
        invoice_id, data.model_dump(exclude_none=True, by_alias=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return updated.to_response()


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str):
    deleted = await invoice_model.delete(invoice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return True


@router.post("/{invoice_id}/pay")
async def pay_invoice(invoice_id: str):
    invoice = await invoice_service.mark_invoice_paid(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice.to_response()


@router.post("/{invoice_id}/cancel")
async def cancel_invoice(invoice_id: str):
    invoice = await invoice_service.cancel_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice.to_response()


@router.get("/")
async def list_invoices():
    invoices = await invoice_model.get_all()
    return [i.to_response() for i in invoices]



