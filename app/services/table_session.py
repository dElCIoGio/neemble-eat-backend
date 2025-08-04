import json
from datetime import datetime
from typing import List, Any

from beanie.odm.operators.find.comparison import In, Eq, GTE, LTE, NE
from beanie.odm.operators.find.logical import Or, And

from app.models.table import TableModel
from app.models.table_session import TableSessionModel
from app.schema.table_session import TableSessionStatus, TableSessionDocument
from app.schema.order import OrderDocument
from app.services import invoice as invoice_service
from app.services.order import order_model
from app.services.websocket_manager import get_websocket_manger
from app.utils.time import now_in_luanda

session_model = TableSessionModel()
table_model = TableModel()


async def start_session(data: dict) -> TableSessionDocument:
    return await session_model.create(data)


async def create_session_for_table(
    table_id: str, restaurant_id: str
) -> TableSessionDocument:
    """Create a new ACTIVE session for a table and link it."""
    from app.services import (
        table as table_service,
    )  # Imported here to avoid circular imports

    payload = {
        "tableId": table_id,
        "restaurantId": restaurant_id,
        "status": TableSessionStatus.ACTIVE,
        "orders": [],
        "startTime": now_in_luanda(),
    }
    session = await start_session(payload)
    await table_service.update_table_session(table_id, str(session.id))
    return session


async def get_active_session_for_table(
    table_id: str, *, create_if_missing: bool = False, restaurant_id: str | None = None
) -> TableSessionDocument | None:
    """Return the active session for a table.

    If ``create_if_missing`` is True and no active session exists, a new one will
    be created and linked to the table.
    """

    filters = {"tableId": table_id, "status": {
        "$in": [
            TableSessionStatus.ACTIVE.value,
            TableSessionStatus.NEED_BILL.value]
    }}
    sessions = await session_model.get_by_fields(filters, limit=1)

    if sessions:
        return sessions[0]

    if create_if_missing:
        if restaurant_id is None:
            from app.services import table as table_service  # avoid circular import

            table = await table_service.get_table(table_id)
            if not table:
                return None
            restaurant_id = table.restaurant_id

        return await create_session_for_table(table_id, restaurant_id)

    return None


async def get_active_session_for_restaurant_table(
    restaurant_id: str, table_number: int, create_if_missing: bool = True
) -> TableSessionDocument | None:
    """Return the active session for a restaurant table.

    When ``create_if_missing`` is True, a new active session will be created if
    none exists.
    """
    from app.services import (
        table as table_service,
    )  # Imported here to avoid circular imports

    table = await table_service.get_table_by_restaurant_and_number(
        restaurant_id, table_number
    )
    if not table:
        return None

    return await get_active_session_for_table(
        str(table.id),
        create_if_missing=create_if_missing,
        restaurant_id=restaurant_id,
    )


async def add_order_to_session(
    session_id: str, order_id: str
) -> TableSessionDocument | None:
    """Append an order ID to a table session's order list."""
    session = await session_model.get(session_id)
    if not session:
        return None

    if order_id not in session.orders:
        session.orders.append(order_id)
        session = await session_model.update(session_id, {"orders": session.orders})

    websocket_manager = get_websocket_manger()
    restaurant_id = session.restaurant_id

    order = await order_model.get(order_id)
    order_data = order.model_dump()

    json_data = json.dumps(order_data)

    await websocket_manager.broadcast(json_data, f"{restaurant_id}/order")
    await websocket_manager.broadcast(json_data, f"{restaurant_id}/session_order")

    return session


async def close_table_session(
    session_id: str, cancelled: bool = True
) -> TableSessionDocument:
    """Close or cancel a session and create the next one."""
    try:
        session = await session_model.get(session_id)

        print("Session:", session)

        if not session:
            raise Exception("Session not found")

        if session.status != TableSessionStatus.ACTIVE.value and session.status != TableSessionStatus.NEED_BILL.value:
            raise Exception("Session is not active")

        orders = await order_model.get_by_fields({"sessionId": session_id})

        if cancelled:
            if any(o.prep_status != TableSessionStatus.CANCELLED.value for o in orders):
                raise Exception("All orders must be cancelled to cancel session")
            new_status = TableSessionStatus.CANCELLED.value
        else:
            new_status = TableSessionStatus.CLOSED.value

        await session_model.update(
            session_id, {"status": new_status, "endTime": now_in_luanda()}
        )

        if not cancelled and any(o.prep_status != TableSessionStatus.CANCELLED.value for o in orders):
            await invoice_service.generate_invoice_for_session(session_id)

        new_session = await create_session_for_table(
            session.table_id, session.restaurant_id
        )

        restaurant_id = session.restaurant_id
        websocket_manager = get_websocket_manger()

        json_data = json.dumps([order.to_response().model_dump() for order in orders])
        await websocket_manager.broadcast(json_data, f"{restaurant_id}/billed")

        json_data = json.dumps(new_session.to_response().model_dump())
        await websocket_manager.broadcast(json_data, f"{restaurant_id}/closed_session")

        return new_session
    except Exception as error:
        print(error)


async def mark_session_paid(session_id: str) -> TableSessionDocument | None:
    """Create a paid invoice for the session and start a new one."""
    session = await session_model.get(session_id)
    if not session:
        return None

    invoice = await invoice_service.generate_invoice_for_session(session_id)
    await invoice_service.mark_invoice_paid(str(invoice.id))

    await session_model.update(
        session_id,
        {"status": TableSessionStatus.PAID, "endTime": now_in_luanda()},
    )

    new_session = await create_session_for_table(
        session.table_id, session.restaurant_id
    )

    await table_model.update(
        session.table_id,
        {
            "currentSessionId": str(new_session.id)
        }
    )

    websocket_manager = get_websocket_manger()
    orders = await order_model.get_many(session.orders)
    json_data = json.dumps(
        [order.to_response().model_dump(by_alias=True) for order in orders]
    )
    await websocket_manager.broadcast(json_data, f"{str(session.restaurant_id)}/billed")

    json_data = json.dumps(new_session.to_response().model_dump(by_alias=True))
    await websocket_manager.broadcast(json_data, f"{session.restaurant_id}/closed_session")

    return new_session


async def mark_session_needs_bill(session_id: str) -> TableSessionDocument | None:
    """Mark the session status as needing the bill."""
    session = await session_model.get(session_id)
    if not session:
        return None

    return await session_model.update(
        session_id,
        {"status": TableSessionStatus.NEED_BILL.value},
    )


async def cancel_session_checkout(session_id: str) -> TableSessionDocument | None:
    """Revert session status from ``needs bill`` back to ``active``."""
    session = await session_model.get(session_id)
    if not session:
        return None
    return await session_model.update(
        session_id,
        {"status": TableSessionStatus.ACTIVE.value},
    )


async def mark_session_needs_assistance(session_id: str) -> TableSessionDocument | None:
    """Mark that the session has requested assistance."""
    session = await session_model.get(session_id)
    if not session:
        return None
    return await session_model.update(session_id, {"needsAssistance": True})


async def cancel_session_assistance(session_id: str) -> TableSessionDocument | None:
    """Clear the assistance request for a session."""
    session = await session_model.get(session_id)
    if not session:
        return None
    return await session_model.update(session_id, {"needsAssistance": False})


async def list_sessions_for_table(table_id: str):
    filters = {"tableId": table_id}
    return await session_model.get_by_fields(filters)


async def list_today_sessions_with_orders_for_table(table_id: str) -> List[TableSessionDocument]:
    """Return today's sessions for a table that have at least one order."""
    now = now_in_luanda()
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return await TableSessionDocument.find(
        And(
            Eq(TableSessionDocument.table_id, table_id),
            GTE(TableSessionDocument.start_time, start_day),
            LTE(TableSessionDocument.start_time, now),
            NE(TableSessionDocument.orders, []),
        )
    ).sort("start_time").to_list()


async def list_active_sessions_for_restaurant(
    restaurant_id: str,
) -> List[TableSessionDocument]:
    """Return active sessions that are currently referenced by a table."""
    # Fetch all tables for the restaurant to get their current session ids
    tables = await table_model.get_by_fields({"restaurantId": restaurant_id})
    session_ids = [t.current_session_id for t in tables if t.current_session_id]

    if not session_ids:
        return []

    # Retrieve sessions by ids and ensure they are still marked as active
    sessions = await session_model.get_many(session_ids)
    return [s for s in sessions if s.status == TableSessionStatus.ACTIVE or s.status == TableSessionStatus.NEED_BILL]


async def delete_session(session_id: str) -> bool:
    return await session_model.delete(session_id)


async def delete_unlinked_sessions_for_restaurant(restaurant_id: str) -> int:
    """Delete sessions for a restaurant that are not linked to any table."""
    tables = await table_model.get_by_fields({"restaurantId": restaurant_id})
    linked_ids = {t.current_session_id for t in tables if t.current_session_id}

    coll = TableSessionDocument.get_motor_collection()
    query: dict[str, Any] = {"restaurantId": restaurant_id}
    if linked_ids:
        from bson import ObjectId
        object_ids = [ObjectId(sid) for sid in linked_ids]
        query["_id"] = {"$nin": object_ids}

    result = await coll.delete_many(query)
    return result.deleted_count


async def calculate_session_time_length(session_id: str) -> float:
    """Return the length of a session in minutes based on its orders."""
    session = await session_model.get(session_id)
    if not session:
        return 0.0

    orders = (
        await OrderDocument.find(OrderDocument.session_id == session_id)
        .sort("order_time")
        .to_list()
    )

    if not orders:
        return 0.0

    first_order_time = orders[0].order_time
    end_time = session.end_time or now_in_luanda()

    duration_seconds = (end_time - first_order_time).total_seconds()
    return duration_seconds / 60.0
