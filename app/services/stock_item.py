from datetime import datetime
from typing import List, Optional

from app.models.stock_item import StockItemModel
from app.models.movement import MovementModel
from app.schema import stock_item as stock_schema
from app.schema import movement as movement_schema
from app.utils.time import now_in_luanda

stock_item_model = StockItemModel()

async def create_stock_item(data: stock_schema.StockItemCreate) -> stock_schema.StockItemDocument:
    payload = data.model_dump(by_alias=True)
    new_stock_item = await stock_item_model.create(payload)
    return new_stock_item


async def get_stock_item(item_id: str) -> Optional[stock_schema.StockItemDocument]:
    return await stock_item_model.get(item_id)


async def list_stock_items_for_restaurant(restaurant_id: str) -> List[stock_schema.StockItemDocument]:
    return await stock_item_model.get_by_fields({"restaurantId": restaurant_id})


async def update_stock_item(item_id: str, data: stock_schema.StockItemUpdate) -> Optional[stock_schema.StockItemDocument]:
    return await stock_item_model.update(item_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_stock_item(item_id: str) -> bool:
    deleted = await stock_item_model.delete(item_id)
    return deleted


async def add_stock(item_id: str, quantity: float, reason: str = "", user: str = "system") -> Optional[stock_schema.StockItemDocument]:
    item = await stock_item_model.get(item_id)
    if not item:
        return None
    new_quantity = item.current_quantity + quantity
    updated = await stock_item_model.update(item_id, {"currentQuantity": new_quantity, "lastEntry": now_in_luanda().isoformat()})
    return updated


async def remove_stock(item_id: str, quantity: float, reason: str = "", user: str = "system") -> Optional[stock_schema.StockItemDocument]:
    item = await stock_item_model.get(item_id)
    if not item:
        return None
    new_quantity = item.current_quantity - quantity
    if new_quantity < 0:
        new_quantity = 0
    updated = await stock_item_model.update(item_id, {"currentQuantity": new_quantity})
    return updated


async def list_categories() -> List[str]:
    coll = stock_schema.StockItemDocument.get_motor_collection()
    return await coll.distinct("category")


async def delete_category(name: str) -> int:
    coll = stock_schema.StockItemDocument.get_motor_collection()
    result = await coll.delete_many({"category": name})
    return result.deleted_count


async def get_stats(restaurant_id: str) -> dict:
    items = await stock_item_model.get_by_fields({"restaurantId": restaurant_id})
    total_items = len(items)
    low_stock = len([i for i in items if i.status == stock_schema.StockStatus.BAIXO])
    critical_stock = len([i for i in items if i.status == stock_schema.StockStatus.CRITICO])
    total_value = sum((i.current_quantity * (i.cost or 0.0)) for i in items)
    return {
        "totalItems": total_items,
        "lowStock": low_stock,
        "criticalStock": critical_stock,
        "totalValue": total_value,
    }


async def list_auto_reorder_items(restaurant_id: str) -> List[stock_schema.StockItemDocument]:
    filters = {
        "restaurantId": restaurant_id,
        "autoReorder": True,
        "reorderPoint": {"$ne": None},
        "currentQuantity": {"$lte": {"$ifNull": ["$reorderPoint", 0]}}
    }
    return await stock_item_model.get_by_fields(filters)
