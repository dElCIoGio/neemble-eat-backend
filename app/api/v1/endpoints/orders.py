from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Body, Query

from app.schema import order as order_schema
from app.services import order as order_service
from app.services.order import order_model

router = APIRouter()


@router.post("/")
async def create_order(order_data: order_schema.OrderCreate = Body(..., alias="orderData"), session_id: str = Body(..., alias="sessionId")):
    """Create a new order and append it to the related session."""
    try:
        payload = order_data.model_dump(by_alias=True)
        if session_id:
            payload["sessionId"] = session_id
        order = await order_service.place_order(payload)
        return order.to_response()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/bulk")
async def create_orders(
    orders_data: list[order_schema.OrderCreate] = Body(..., alias="ordersData"),
    session_id: str | None = Body(None, alias="sessionId"),
):
    """Create multiple orders sequentially."""
    try:
        payloads = [data.model_dump(by_alias=True) for data in orders_data]
        orders = await order_service.place_orders(payloads, session_id)
        return [o.to_response() for o in orders]
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/paginate")
async def paginate_orders(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await order_model.paginate(filters=filters, limit=limit, cursor=cursor)

        orders = result.items

        return result
    except Exception as error:
        print(error)


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
async def update_order_status(order_id: str, status: order_schema.OrderPrepStatus = Body(...)):
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


@router.get("/sessions/{session_id}")
async def list_session_orders(session_id: str):
    orders = await order_service.list_orders_for_session(session_id)
    return [o.to_response() for o in orders]


@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_orders(restaurant_id: str):
    orders = await order_service.list_orders_for_restaurant(restaurant_id)
    return [o.to_response() for o in orders]


@router.get("/restaurant/{restaurant_id}/recent")
async def list_recent_restaurant_orders(
    restaurant_id: str, hours: int = 24
):
    """Return orders from the last ``hours`` for the given restaurant."""
    orders = await order_service.list_recent_orders_for_restaurant(
        restaurant_id, hours
    )
    return [o.to_response() for o in orders]


@router.get("/status/{prep_status}")
async def list_orders_by_status(prep_status: order_schema.OrderPrepStatus):
    orders = await order_service.list_orders_by_prep_status(prep_status)
    return [o.to_response() for o in orders]
