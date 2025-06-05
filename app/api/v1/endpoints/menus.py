from fastapi import APIRouter, HTTPException

from app.schema import menu as menu_schema
from app.services import menu as menu_service
from app.services import category as category_service
from app.services import item as item_service

router = APIRouter()

@router.post("/")
async def create_menu(data: menu_schema.MenuCreate):
    try:
        menu = await menu_service.create_menu(data)
        return menu.to_response()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@router.delete("/{menu_id}")
async def delete_menu(menu_id: str):
    result = await menu_service.delete_menu(menu_id)
    if not result:
        raise HTTPException(status_code=404, detail="Menu not found")
    return True

@router.put("/{menu_id}")
async def update_menu(menu_id: str, data: menu_schema.MenuUpdate):
    updated = await menu_service.update_menu(menu_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Menu not found")
    return updated.to_response()

@router.put("/{menu_id}/preferences")
async def update_menu_preferences(menu_id: str, preferences: menu_schema.MenuPreferences):
    updated = await menu_service.update_menu(menu_id, menu_schema.MenuUpdate(preferences=preferences))
    if not updated:
        raise HTTPException(status_code=404, detail="Menu not found")
    return updated.to_response()

@router.put("/{menu_id}/status")
async def update_menu_status(menu_id: str, is_active: bool):
    try:
        return await menu_service.update_menu_status(menu_id, is_active)
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))

@router.get("/{menu_id}")
async def get_menu(menu_id: str):
    menu = await menu_service.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu.to_response()

@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_menus(restaurant_id: str):
    menus = await menu_service.list_menus(restaurant_id)
    return [m.to_response() for m in menus]

@router.get("/{menu_id}/categories")
async def list_menu_categories(menu_id: str):
    categories = await category_service.list_categories_for_menu(menu_id)
    return [c.to_response() for c in categories]

@router.get("/{menu_id}/items")
async def list_menu_items(menu_id: str):
    items = await item_service.list_items_by_menu(menu_id)
    return [i.to_response() for i in items]
