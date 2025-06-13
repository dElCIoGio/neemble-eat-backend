from datetime import datetime, timedelta

from beanie.operators import And, Eq, GTE

from app.models.order import OrderModel
from app.schema import order as order_schema
from app.schema.order import OrderDocument
from app.services import table_session as table_session_service
from app.utils.time import now_in_luanda

order_model = OrderModel()


async def place_order(data: dict) -> order_schema.OrderDocument:
    """Create a new order and attach it to the related table session.

    If the provided ``sessionId`` is missing or refers to a session that is not
    active, a new session is created and linked to the table automatically.
    """
    session_id = data.get("sessionId")
    restaurant_id = data.get("restaurantId")
    table_number = data.get("tableNumber")

    # Ensure there is an active session
    if not session_id and restaurant_id and table_number is not None:
        session = await table_session_service.get_active_session_for_restaurant_table(
            restaurant_id,
            table_number,
            create_if_missing=True,
        )
        if session:
            session_id = str(session.id)
            data["sessionId"] = session_id

    order = await order_model.create(data)

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


async def list_recent_orders_for_restaurant(
    restaurant_id: str, hours: int = 24
) -> list[order_schema.OrderDocument]:
    """List orders placed within the last ``hours`` for a restaurant."""
    cutoff = now_in_luanda() - timedelta(hours=hours)
    return await OrderDocument.find(
        And(
            Eq(OrderDocument.restaurant_id, restaurant_id),
            GTE(OrderDocument.order_time, cutoff),
        )
    ).sort("-order_time").to_list()


async def update_order(order_id: str, data: order_schema.OrderUpdate) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_order(order_id: str) -> bool:
    return await order_model.delete(order_id)
