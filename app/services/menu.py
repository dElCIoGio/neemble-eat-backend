from app.models.menu import MenuModel
from app.schema import menu as menu_schema
from app.utils.slug import generate_unique_slug


menu_model = MenuModel()

async def create_menu(data: menu_schema.MenuCreate):
    payload = data.model_dump(by_alias=False)
    payload["slug"] = await generate_unique_slug(payload["name"], menu_schema.MenuDocument)
    return await menu_model.create(payload)

async def update_menu(menu_id: str, data: menu_schema.MenuUpdate):
    return await menu_model.update(menu_id, data)

async def delete_menu(menu_id: str):
    return await menu_model.delete(menu_id)

async def deactivate_menu(menu_id: str):
    menu = await menu_model.get(menu_id)
    if not menu:
        raise Exception("Menu not found")
    return await menu_model.update(menu_id, {"isActive": False})

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