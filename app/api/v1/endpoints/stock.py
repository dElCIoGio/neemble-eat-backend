from fastapi import APIRouter, HTTPException, Body

from app.schema import stock_item as stock_schema
from app.services import stock_item as stock_service

router = APIRouter()


@router.get("/restaurant/{restaurant_id}")
async def list_stock_items(restaurant_id: str):
    items = await stock_service.list_stock_items_for_restaurant(restaurant_id)
    return [i.to_response() for i in items]


@router.post("/restaurant/{restaurant_id}")
async def create_stock_item(restaurant_id: str, data: stock_schema.StockItemCreate):
    if data.restaurant_id != restaurant_id:
        raise HTTPException(status_code=400, detail="Mismatched restaurant id")
    item = await stock_service.create_stock_item(data)
    return item.to_response()


@router.get("/{item_id}")
async def get_stock_item(item_id: str):
    item = await stock_service.get_stock_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_response()


@router.put("/{item_id}")
async def update_stock_item(item_id: str, data: stock_schema.StockItemUpdate):
    updated = await stock_service.update_stock_item(item_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.delete("/{item_id}")
async def delete_stock_item(item_id: str):
    deleted = await stock_service.delete_stock_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return True


@router.post("/{item_id}/add")
async def add_stock(item_id: str, quantity: float = Body(...), reason: str = Body("", embed=True)):
    updated = await stock_service.add_stock(item_id, quantity, reason)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.post("/{item_id}/remove")
async def remove_stock(item_id: str, quantity: float = Body(...), reason: str = Body("", embed=True)):
    updated = await stock_service.remove_stock(item_id, quantity, reason)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.get("/categories")
async def list_categories():
    return await stock_service.list_categories()


@router.delete("/categories/{name}")
async def delete_category(name: str):
    count = await stock_service.delete_category(name)
    return {"deleted": count}


@router.get("/stats")
async def get_stats(restaurant_id: str):
    return await stock_service.get_stats(restaurant_id)


@router.get("/auto-reorder")
async def list_auto_reorder_items(restaurant_id: str):
    items = await stock_service.list_auto_reorder_items(restaurant_id)
    return [i.to_response() for i in items]
