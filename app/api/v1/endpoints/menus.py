from fastapi import APIRouter, HTTPException

from app.schema import menu as menu_schema
from app.services import menu as menu_service

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
