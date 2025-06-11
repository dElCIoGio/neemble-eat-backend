from app.models.order import OrderModel
from app.schema import order as order_schema
from app.services import table_session as table_session_service

order_model = OrderModel()


async def place_order(data: dict) -> order_schema.OrderDocument:
    """Create a new order and attach it to the related table session."""
    order = await order_model.create(data)
    session_id = data.get("sessionId")
    if session_id:
        await table_session_service.add_order_to_session(session_id, str(order.id))
    return order


async def get_order(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.get(order_id)


async def update_order_prep_status(order_id: str, status: order_schema.OrderPrepStatus) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"prepStatus": status})


async def mark_order_delivered(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"isDelivered": True})


async def cancel_order(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"prepStatus": "CANCELLED", "isDelivered": False})


async def list_orders_for_session(session_id: str) -> list[order_schema.OrderDocument]:
    filters = {"sessionId": session_id}
    return await order_model.get_by_fields(filters)


async def list_orders_by_prep_status(status: order_schema.OrderPrepStatus) -> list[order_schema.OrderDocument]:
    filters = {"prepStatus": status}
    return await order_model.get_by_fields(filters)


async def list_orders_for_restaurant(restaurant_id: str) -> list[order_schema.OrderDocument]:
    filters = {"restaurantId": restaurant_id}
    return await order_model.get_by_fields(filters)


async def update_order(order_id: str, data: order_schema.OrderUpdate) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_order(order_id: str) -> bool:
    return await order_model.delete(order_id)
