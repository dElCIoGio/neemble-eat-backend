from typing import Optional, List

from app.models.table import TableModel
from app.models.restaurant import RestaurantModel
from app.schema import table as table_schema
from app.schema.order import OrderDocument
from app.services import table_session as session_service
from app.services import order as order_service
from app.schema import order as order_schema


table_model = TableModel()
restaurant_model = RestaurantModel()


async def organize_table_numbers(restaurant_id: str) -> List[table_schema.TableDocument]:
    """Ensure tables for a restaurant have sequential numbers starting at 1."""
    tables = await table_model.get_by_fields({"restaurantId": restaurant_id})
    tables_sorted = sorted(tables, key=lambda t: t.number)

    expected = 1
    for t in tables_sorted:
        if t.number != expected:
            await table_model.update(str(t.id), {"number": expected})
            t.number = expected
        expected += 1

    return tables_sorted


async def create_table(data: table_schema.TableCreate) -> table_schema.TableDocument:
    # Ensure numbers are sequential before creating a new one
    await organize_table_numbers(data.restaurant_id)

    # Prevent duplicate table numbers
    existing = await get_table_by_restaurant_and_number(data.restaurant_id, data.number)
    if existing:
        raise ValueError("Table number already exists")

    payload = data.model_dump(by_alias=False)
    table = await table_model.create(payload)

    restaurant = await restaurant_model.get(data.restaurant_id)
    if restaurant:
        table_ids = restaurant.table_ids or []
        table_ids.append(str(table.id))
        await restaurant_model.update(str(restaurant.id), {"tableIds": table_ids})

    # Reorganize numbers after insertion
    await organize_table_numbers(data.restaurant_id)

    session = await session_service.create_session_for_table(str(table.id), data.restaurant_id)
    return await table_model.update(str(table.id), {"currentSessionId": str(session.id)})


async def get_table(table_id: str) -> Optional[table_schema.TableDocument]:
    return await table_model.get(table_id)


async def list_tables_for_restaurant(restaurant_id: str) -> List[table_schema.TableDocument]:
    tables = await organize_table_numbers(restaurant_id)
    return tables


async def update_table(table_id: str, data: table_schema.TableUpdate) -> Optional[table_schema.TableDocument]:
    return await table_model.update(table_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_table(table_id: str) -> bool:
    table = await table_model.get(table_id)
    if not table:
        return False

    restaurant = await restaurant_model.get(table.restaurant_id)
    if restaurant and table_id in restaurant.table_ids:
        ids = [tid for tid in restaurant.table_ids if tid != table_id]
        await restaurant_model.update(str(restaurant.id), {"tableIds": ids})
    if table.current_session_id:
        await session_service.delete_session(table.current_session_id)

    return await table_model.delete(table_id)


async def update_table_status(table_id: str, is_active: bool) -> Optional[table_schema.TableDocument]:
    return await table_model.update(table_id, {"isActive": is_active})


async def update_table_session(table_id: str, session_id: Optional[str]) -> Optional[table_schema.TableDocument]:
    table = await table_model.get(table_id)
    print("table: ", table)
    print("SESSION ID:", session_id)
    session = await table_model.update(table_id, {"currentSessionId": session_id})
    print("UPDATED SESSION:", session)
    return session


async def get_table_by_restaurant_and_number(restaurant_id: str, number: int) -> Optional[table_schema.TableDocument]:
    """Retrieve a table by restaurant id and table number."""
    await organize_table_numbers(restaurant_id)
    filters = {"restaurantId": restaurant_id, "number": number}
    tables = await table_model.get_by_fields(filters, limit=1)
    if tables:
        return tables[0]
    return None


async def _delete_orders_for_session(session_id: str) -> int:
    """Delete all orders associated with a session."""
    coll = OrderDocument.get_motor_collection()
    result = await coll.delete_many({"sessionId": session_id})
    return result.deleted_count


async def _cancel_orders_for_session(session_id: str) -> int:
    """Cancel all orders for a session."""
    coll = OrderDocument.get_motor_collection()
    update = {
        "$set": {
            "prepStatus": order_schema.OrderPrepStatus.CANCELLED,
            "isDelivered": False,
        }
    }
    result = await coll.update_many({"sessionId": session_id}, update)
    return result.modified_count


async def reset_table(table_id: str) -> Optional[table_schema.TableDocument]:
    """Delete current session and orders for a table and create a new session."""
    table = await table_model.get(table_id)
    if not table:
        return None

    session_id = table.current_session_id
    if session_id:
        await _delete_orders_for_session(session_id)
        await session_service.delete_session(session_id)

    new_session = await session_service.create_session_for_table(
        table_id,
        table.restaurant_id,
    )

    return await table_model.update(table_id, {"currentSessionId": str(new_session.id)})


async def clean_table(table_id: str) -> Optional[table_schema.TableDocument]:
    """Cancel all orders, cancel the session and start a new one."""
    table = await table_model.get(table_id)

    if not table:
        return None

    session_id = table.current_session_id
    if session_id:
        await _cancel_orders_for_session(session_id)
        await session_service.close_table_session(session_id, cancelled=True)
    else:
        await session_service.create_session_for_table(table_id, table.restaurant_id)

    return await table_model.get(table_id)


async def reset_tables_for_restaurant(restaurant_id: str) -> List[table_schema.TableDocument]:
    tables = await list_tables_for_restaurant(restaurant_id)
    results: List[table_schema.TableDocument] = []
    for t in tables:
        updated = await reset_table(str(t.id))
        if updated:
            results.append(updated)
    return results


async def reset_all_tables() -> List[table_schema.TableDocument]:
    tables = await table_model.get_all()
    results: List[table_schema.TableDocument] = []
    for t in tables:
        updated = await reset_table(str(t.id))
        if updated:
            results.append(updated)
    return results
