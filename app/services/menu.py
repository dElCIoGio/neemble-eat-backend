from app.models.menu import MenuModel
from app.models.category import CategoryModel
from app.models.restaurant import RestaurantModel
from app.schema import menu as menu_schema
from app.utils.slug import generate_unique_slug


menu_model = MenuModel()
category_model = CategoryModel()
restaurant_model = RestaurantModel()

async def create_menu(data: menu_schema.MenuCreate):
    payload = data.model_dump(by_alias=False)
    payload["slug"] = await generate_unique_slug(payload["name"], menu_schema.MenuDocument)
    menu = await menu_model.create(payload)

    restaurant = await restaurant_model.get(data.restaurant_id)
    if restaurant:
        menu_ids = restaurant.menu_ids or []
        menu_ids.append(str(menu.id))
        await restaurant_model.update(str(restaurant.id), {"menuIds": menu_ids})

    return menu

async def update_menu(menu_id: str, data: menu_schema.MenuUpdate):
    return await menu_model.update(menu_id, data)

async def delete_menu(menu_id: str):
    menu = await menu_model.get(menu_id)
    if not menu:
        return False

    # Remove categories linked to this menu
    categories = await category_model.get_by_fields({"menuId": menu_id})
    for category in categories:
        await category_model.delete(str(category.id))

    # Remove menu id from restaurant
    restaurant = await restaurant_model.get(menu.restaurant_id)
    if restaurant and menu_id in restaurant.menu_ids:
        new_ids = [mid for mid in restaurant.menu_ids if mid != menu_id]
        update_data = {"menuIds": new_ids}
        if restaurant.current_menu_id == menu_id:
            update_data["currentMenuId"] = None
        await restaurant_model.update(str(restaurant.id), update_data)

    return await menu_model.delete(menu_id)

async def deactivate_menu(menu_id: str):
    menu = await menu_model.get(menu_id)
    if not menu:
        raise Exception("Menu not found")
    return await menu_model.update(menu_id, {"isActive": False})

async def update_menu_status(menu_id: str, is_active: bool):
    menu = await menu_model.get(menu_id)
    if not menu:
        raise Exception("Menu not found")
    return await menu_model.update(menu_id, {"isActive": is_active})

async def get_menu(menu_id: str):
    return await menu_model.get(menu_id)

async def get_menu_by_slug(slug: str):
    return await menu_model.get_by_slug(slug)

async def list_menus(restaurant_id: str):
    filters = {"restaurantId": restaurant_id, "isActive": True}
    return await menu_model.get_by_fields(filters)


async def add_category_to_menu(menu_id: str, category_id: str):
    menu = await menu_model.get(menu_id)
    if not menu:
        raise Exception("Menu not found")

    if category_id not in menu.category_ids:
        menu.category_ids.append(category_id)
        await menu_model.update(menu_id, {"categoryIds": menu.category_ids})

    return menu

async def remove_category_from_menu(menu_id: str, category_id: str):
    menu = await menu_model.get(menu_id)
    if not menu:
        raise Exception("Menu not found")

    if category_id in menu.category_ids:
        menu.category_ids.remove(category_id)
        await menu_model.update(menu_id, {"categoryIds": menu.category_ids})

    return menu
