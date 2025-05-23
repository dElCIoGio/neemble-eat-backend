from app.models.order import OrderModel

order_model = OrderModel()

async def place_order(data: dict):
    return await order_model.create(data)

async def update_order_prep_status(order_id: str, status: str):
    return await order_model.update(order_id, {"prepStatus": status})

async def mark_order_delivered(order_id: str):
    return await order_model.update(order_id, {"isDelivered": True})

async def cancel_order(order_id: str):
    return await order_model.update(order_id, {"prepStatus": "CANCELLED", "isDelivered": False})

async def list_orders_for_session(session_id: str):
    filters = {"sessionId": session_id}
    return await order_model.get_by_fields(filters)

async def list_orders_by_prep_status(status: str):
    filters = {"prepStatus": status}
    return await order_model.get_by_fields(filters)
