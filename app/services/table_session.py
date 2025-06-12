from datetime import datetime
from typing import List

from app.models.table_session import TableSessionModel
from app.schema.table_session import TableSessionStatus, TableSessionDocument
from app.schema.order import OrderDocument
from app.services import invoice as invoice_service

session_model = TableSessionModel()


async def start_session(data: dict) -> TableSessionDocument:
    return await session_model.create(data)


async def create_session_for_table(table_id: str, restaurant_id: str) -> TableSessionDocument:
    """Create a new ACTIVE session for a table and link it."""
    from app.services import table as table_service  # Imported here to avoid circular imports

    payload = {
        "tableId": table_id,
        "restaurantId": restaurant_id,
        "status": TableSessionStatus.ACTIVE,
        "orders": [],
        "startTime": datetime.now(),
    }
    session = await start_session(payload)
    await table_service.update_table_session(table_id, str(session.id))
    return session

async def get_active_session_for_table(
    table_id: str,
    *,
    create_if_missing: bool = False,
    restaurant_id: str | None = None
) -> TableSessionDocument | None:
    """Return the active session for a table.

    If ``create_if_missing`` is True and no active session exists, a new one will
    be created and linked to the table.
    """
    filters = {"tableId": table_id, "status": "active"}
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
    restaurant_id: str,
    table_number: int,
    create_if_missing: bool = True
) -> TableSessionDocument | None:
    """Return the active session for a restaurant table.

    When ``create_if_missing`` is True, a new active session will be created if
    none exists.
    """
    from app.services import table as table_service  # Imported here to avoid circular imports

    table = await table_service.get_table_by_restaurant_and_number(restaurant_id, table_number)
    if not table:
        return None

    return await get_active_session_for_table(
        str(table.id),
        create_if_missing=create_if_missing,
        restaurant_id=restaurant_id,
    )


async def add_order_to_session(session_id: str, order_id: str) -> TableSessionDocument | None:
    """Append an order ID to a table session's order list."""
    session = await session_model.get(session_id)
    if not session:
        return None

    if order_id not in session.orders:
        session.orders.append(order_id)
        return await session_model.update(session_id, {"orders": session.orders})

    return session

async def close_table_session(session_id: str, cancelled: bool = False) -> TableSessionDocument:
    """Close or cancel a session and create the next one."""
    try:
        session = await session_model.get(session_id)

        print("SESSION TO BE CLOSED:", session)

        if not session:
            raise Exception("Session not found")

        if session.status != TableSessionStatus.ACTIVE:
            raise Exception("Session is not active")

        orders: List[OrderDocument] = await OrderDocument.find(OrderDocument.session_id == session_id).to_list()

        print("ORDERS:", orders)

        if cancelled:
            print("CHECKING IF IT IS BEING CANCELLED")
            if any(o.prep_status != "cancelled" for o in orders):
                raise Exception("All orders must be cancelled to cancel session")
            new_status = TableSessionStatus.CANCELLED
        else:
            new_status = TableSessionStatus.CLOSED

        print("checkpiont")

        await session_model.update(session_id, {
            "status": new_status,
            "endTime": datetime.now()
        })

        print("UPDATED SESSION")

        if not cancelled and any(o.prep_status != "cancelled" for o in orders):
            await invoice_service.generate_invoice_for_session(session_id)

        print("checkpiont 2")


        new_session = await create_session_for_table(session.table_id, session.restaurant_id)

        print("checkpiont 3")
        print("NEW SESSION:", new_session)


        return new_session
    except Exception as error:
        print(error)

async def list_sessions_for_table(table_id: str):
    filters = {"tableId": table_id}
    return await session_model.get_by_fields(filters)


async def delete_session(session_id: str) -> bool:
    return await session_model.delete(session_id)
