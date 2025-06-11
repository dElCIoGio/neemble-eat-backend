from fastapi import APIRouter, HTTPException

from app.schema import order as order_schema
from app.services import order as order_service

router = APIRouter()


@router.post("/")
async def create_order(data: order_schema.OrderCreate, session_id: str | None = None):
    """Create a new order and append it to the related session."""
    try:
        payload = data.model_dump(by_alias=True)
        if session_id:
            payload["sessionId"] = session_id
        order = await order_service.place_order(payload)
        return order.to_response()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/{order_id}")
async def get_order(order_id: str):
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_response()


@router.put("/{order_id}")
async def update_order(order_id: str, data: order_schema.OrderUpdate):
    updated = await order_service.update_order(order_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated.to_response()


@router.delete("/{order_id}")
async def delete_order(order_id: str):
    deleted = await order_service.delete_order(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return True


@router.put("/{order_id}/status")
async def update_order_status(order_id: str, status: order_schema.OrderPrepStatus):
    updated = await order_service.update_order_prep_status(order_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated.to_response()


@router.post("/{order_id}/deliver")
async def deliver_order(order_id: str):
    updated = await order_service.mark_order_delivered(order_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated.to_response()


@router.post("/{order_id}/cancel")
async def cancel_order_endpoint(order_id: str):
    updated = await order_service.cancel_order(order_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated.to_response()


@router.get("/session/{session_id}")
async def list_session_orders(session_id: str):
    orders = await order_service.list_orders_for_session(session_id)
    return [o.to_response() for o in orders]


@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_orders(restaurant_id: str):
    orders = await order_service.list_orders_for_restaurant(restaurant_id)
    return [o.to_response() for o in orders]


@router.get("/status/{prep_status}")
async def list_orders_by_status(prep_status: order_schema.OrderPrepStatus):
    orders = await order_service.list_orders_by_prep_status(prep_status)
    return [o.to_response() for o in orders]
