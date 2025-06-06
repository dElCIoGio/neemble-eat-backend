from typing import Optional, List

from app.models.table import TableModel
from app.models.restaurant import RestaurantModel
from app.schema import table as table_schema
from app.services import table_session as session_service


table_model = TableModel()
restaurant_model = RestaurantModel()


async def create_table(data: table_schema.TableCreate) -> table_schema.TableDocument:
    payload = data.model_dump(by_alias=False)
    table = await table_model.create(payload)
    restaurant = await restaurant_model.get(data.restaurant_id)
    if restaurant:
        table_ids = restaurant.table_ids or []
        table_ids.append(str(table.id))
        await restaurant_model.update(str(restaurant.id), {"tableIds": table_ids})
    session = await session_service.create_session_for_table(str(table.id), data.restaurant_id)
    return await table_model.update(str(table.id), {"currentSessionId": str(session.id)})


async def get_table(table_id: str) -> Optional[table_schema.TableDocument]:
    return await table_model.get(table_id)


async def list_tables_for_restaurant(restaurant_id: str) -> List[table_schema.TableDocument]:
    return await table_model.get_by_fields({"restaurantId": restaurant_id})


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
    return await table_model.update(table_id, {"currentSessionId": session_id})
