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

async def get_active_session_for_table(table_id: str):
    filters = {
        "tableId": table_id,
        "status": "active"
    }
    sessions = await session_model.get_by_fields(filters, limit=1)

    if sessions:
        return sessions[0]
    return None


async def get_active_session_for_restaurant_table(restaurant_id: str, table_number: int):
    """Return the active session given restaurant id and table number."""
    from app.services import table as table_service  # Imported here to avoid circular imports

    table = await table_service.get_table_by_restaurant_and_number(restaurant_id, table_number)
    if not table:
        return None
    return await get_active_session_for_table(str(table.id))

async def close_table_session(session_id: str, cancelled: bool = False) -> TableSessionDocument:
    """Close or cancel a session and create the next one."""
    session = await session_model.get(session_id)
    if not session:
        raise Exception("Session not found")

    if session.status != TableSessionStatus.ACTIVE:
        raise Exception("Session is not active")

    orders: List[OrderDocument] = await OrderDocument.find(OrderDocument.session_id == session_id).to_list()

    if cancelled:
        if any(o.prep_status != "cancelled" for o in orders):
            raise Exception("All orders must be cancelled to cancel session")
        new_status = TableSessionStatus.CANCELLED
    else:
        new_status = TableSessionStatus.CLOSED

    await session_model.update(session_id, {
        "status": new_status,
        "endTime": datetime.now()
    })

    if not cancelled and any(o.prep_status != "cancelled" for o in orders):
        await invoice_service.generate_invoice_for_session(session_id)

    new_session = await create_session_for_table(session.table_id, session.restaurant_id)
    return new_session

async def list_sessions_for_table(table_id: str):
    filters = {"tableId": table_id}
    return await session_model.get_by_fields(filters)


async def delete_session(session_id: str) -> bool:
    return await session_model.delete(session_id)
