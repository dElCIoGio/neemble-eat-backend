from fastapi import APIRouter, HTTPException

from app.schema import menu as menu_schema
from app.schema.menu import MenuDocument
from app.services import menu as menu_service
from app.services import category as category_service
from app.services import item as item_service
from app.services.menu import menu_model
from app.utils.slug import generate_unique_slug

router = APIRouter()

@router.post("/")
async def create_menu(data: menu_schema.MenuCreate):
    try:
        menu = await menu_service.create_menu(data)
        slug = await generate_unique_slug(name=menu.name, model=menu_schema.MenuDocument)
        menu = await menu_model.update(menu.id, {"slug": slug})
        return menu.to_response()
    except Exception as error:
        if menu:
            await menu_model.delete(menu.id)
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


@router.get("/slug/{slug}")
async def get_menu_by_slug(slug: str):
    menu = await menu_service.get_menu_by_slug(slug)
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

@router.get("/items/slug/{menu_slug}")
async def list_menu_items_by_slug(menu_slug: str):
    try:
        menu = await menu_model.get_by_slug(menu_slug)
        if not menu:
            raise HTTPException(
                detail="The menu was not found",
                status_code=400
            )
        items = await item_service.list_items_by_menu(menu.id)
        return [i.to_response() for i in items]
    except Exception as error:
        print(error)
        raise HTTPException(
            detail=str(error),
            status_code=400
        )


@router.post("/copy/{menu_slug}")
async def copy_menu(menu_slug: str, restaurant_id: str):
    """Create a copy of a menu, its categories and items."""
    try:
        menu = await menu_service.copy_menu_by_slug(menu_slug, restaurant_id)
        return menu.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
