from fastapi import APIRouter, HTTPException

from app.schema import category as category_schema
from app.services import category as category_service
from app.services import item as item_service

router = APIRouter()

@router.post("/")
async def create_category(data: category_schema.CategoryCreate):
    try:
        created = await category_service.create_category(data)
        return created.to_response()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@router.get("/{category_id}")
async def get_category(category_id: str):
    category = await category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_response()

@router.put("/{category_id}")
async def update_category(category_id: str, data: category_schema.CategoryUpdate):
    updated = await category_service.update_category(category_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated.to_response()

@router.delete("/{category_id}")
async def delete_category(category_id: str):
    result = await category_service.delete_category(category_id)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return True

@router.put("/{category_id}/availability")
async def switch_category_availability(category_id: str, is_active: bool):
    updated = await category_service.update_category_availability(category_id, is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated.to_response()

@router.get("/{category_id}/items")
async def list_category_items(category_id: str):
    items = await item_service.list_items_by_category(category_id)
    return [i.to_response() for i in items]

@router.post("/{category_id}/items/{item_id}")
async def add_item(category_id: str, item_id: str):
    try:
        category = await category_service.add_item_to_category(category_id, item_id)
        return category.to_response()
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))

@router.delete("/{category_id}/items/{item_id}")
async def remove_item(category_id: str, item_id: str):
    try:
        category = await category_service.remove_item_from_category(category_id, item_id)
        return category.to_response()
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))

@router.get("/menu/{menu_id}")
async def list_menu_categories(menu_id: str):
    categories = await category_service.list_categories_for_menu(menu_id)
    return [c.to_response() for c in categories]

@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_categories(restaurant_id: str):
    categories = await category_service.list_categories_for_restaurant(restaurant_id)
    return [c.to_response() for c in categories]

@router.get("/slug/{slug}")
async def get_category_by_slug(slug: str):
    category = await category_service.get_category_by_slug(slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_response()
