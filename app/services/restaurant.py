from fastapi import HTTPException

from app.models.menu import MenuModel

from app.models.restaurant import RestaurantModel
from app.schema import restaurant as restaurant_schema
from app.utils.slug import generate_unique_slug
from app.services import item as item_service


restaurant_model = RestaurantModel()
menu_model = MenuModel()

async def create_restaurant(data: restaurant_schema.RestaurantCreate):
    try:
        payload = data.model_dump(by_alias=False)
        payload["slug"] = await generate_unique_slug(payload["name"], restaurant_schema.RestaurantDocument)
        return await restaurant_model.create(payload)
    except Exception as error:
        print(error)
        raise HTTPException(detail=str(error), status_code=500)

async def update_restaurant(restaurant_id: str, data: restaurant_schema.RestaurantUpdate):
    return await restaurant_model.update(restaurant_id, data)

async def delete_restaurant(restaurant_id: str):
    return await restaurant_model.delete(restaurant_id)

async def get_restaurants():
    return await restaurant_model.get_all()

async def get_active_restaurants():
    return await restaurant_model.get_by_fields({
        "isActive": True
    })

async def deactivate_restaurant(restaurant_id: str):
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise Exception("Restaurant not found")
    return await restaurant_model.update(restaurant_id, {"isActive": False})

async def get_restaurant(restaurant_id: str):
    return await restaurant_model.get(restaurant_id)

async def get_by_slug(slug: str):
    return await restaurant_model.get_by_slug(slug)

async def get_current_menu(restaurant_id: str):
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if not restaurant.current_menu_id:
        return None

    menu = await menu_model.get(restaurant.current_menu_id)
    return menu

async def change_current_menu(restaurant_id: str, menu_id: str) -> bool:
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if menu_id not in restaurant.menu_ids:
        raise HTTPException(status_code=400, detail="Menu does not belong to restaurant")

    await restaurant_model.update(restaurant_id, {"currentMenuId": menu_id})
    return True


async def list_current_menu_items_by_slug(slug: str):
    """Return all available items in the restaurant's current menu using the restaurant slug."""
    restaurant = await restaurant_model.get_by_slug(slug)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if not restaurant.current_menu_id:
        return []

    items = await item_service.list_items_by_menu(restaurant.current_menu_id)
    return items


async def update_opening_hours(
    restaurant_id: str, opening_hours: restaurant_schema.OpeningHours
) -> restaurant_schema.RestaurantDocument:
    """Update a restaurant's opening hours settings."""
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    update_data = {
        "settings.openingHours": opening_hours.model_dump(by_alias=True)
    }

    updated = await restaurant_model.update(restaurant_id, update_data)
    return updated


async def update_automatic_stock_adjustments(
    restaurant_id: str, enable: bool
) -> restaurant_schema.RestaurantDocument:
    """Toggle automatic stock adjustments for a restaurant."""
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    update_data = {"settings.automaticStockAdjustments": enable}

    updated = await restaurant_model.update(restaurant_id, update_data)
    return updated


