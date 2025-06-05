
from fastapi import HTTPException

from app.models.menu import MenuModel
from app.models.category import CategoryModel
from app.models.restaurant import RestaurantModel
from app.models.item import ItemModel
from app.schema import menu as menu_schema
from app.schema import category as category_schema
from app.schema import item as item_schema
from app.utils.slug import generate_unique_slug
from app.services import category as category_service
from app.services import item as item_service


menu_model = MenuModel()
category_model = CategoryModel()
restaurant_model = RestaurantModel()
item_model = ItemModel()

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
    try:
        menu = await menu_model.get(menu_id)

        print("MENU:", menu)
        if not menu:
            return False
        print("checkpoint 1")
        # Remove categories linked to this menu
        categories = await category_model.get_by_fields({"menuId": menu_id})
        for category in categories:
            await category_model.delete(str(category.id))
        print("checkpoint 2")
        # Remove menu id from restaurant
        restaurant = await restaurant_model.get(menu.restaurant_id)
        if restaurant and menu_id in restaurant.menu_ids:
            new_ids = [mid for mid in restaurant.menu_ids if mid != menu_id]
            update_data = {"menuIds": new_ids}
            if restaurant.current_menu_id == menu_id:
                update_data["currentMenuId"] = None
            await restaurant_model.update(str(restaurant.id), update_data)
        print("checkpoint 3")
        return await menu_model.delete(menu_id)
    except Exception as error:
        print(error)
        raise HTTPException(
            detail=str(error),
            status_code=400
        )

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


async def copy_menu_by_slug(menu_slug: str, restaurant_id: str) -> menu_schema.MenuDocument:
    """Duplicate a menu, its categories and items using the menu slug."""
    original_menu = await menu_model.get_by_slug(menu_slug)
    if not original_menu:
        raise Exception("Menu not found")

    # Create the new menu
    new_menu_data = menu_schema.MenuCreate(
        restaurant_id=restaurant_id,
        name=original_menu.name,
        description=original_menu.description,
        is_active=original_menu.is_active,
        preferences=original_menu.preferences,
    )
    new_menu = await create_menu(new_menu_data)

    new_slug = await generate_unique_slug(new_menu.name, menu_schema.MenuDocument)
    new_menu = await menu_model.update(str(new_menu.id), {
        "slug": new_slug,
        "position": original_menu.position,
    })

    # Duplicate categories
    categories = await category_model.get_by_fields({"menuId": str(original_menu.id)})
    for category in categories:
        cat_data = category_schema.CategoryCreate(
            name=category.name,
            restaurant_id=restaurant_id,
            description=category.description,
            menu_id=str(new_menu.id),
        )
        new_cat = await category_service.create_category(cat_data)
        cat_slug = await generate_unique_slug(new_cat.name, category_schema.CategoryDocument)
        await category_model.update(str(new_cat.id), {
            "slug": cat_slug,
            "position": category.position,
            "isActive": category.is_active,
            "tags": category.tags,
        })
        await add_category_to_menu(str(new_menu.id), str(new_cat.id))

        # Duplicate items within the category
        items = await item_model.get_by_fields({"categoryId": str(category.id)})
        for item in items:
            item_payload = {
                "name": item.name,
                "price": item.price,
                "restaurantId": restaurant_id,
                "categoryId": str(new_cat.id),
                "description": item.description,
                "customizations": [c.model_dump(by_alias=True) for c in item.customizations],
                "imageUrl": item.image_url,
                "isAvailable": item.is_available,
            }
            new_item = await item_service.create_item(item_payload)
            item_slug = await generate_unique_slug(new_item.name, item_schema.ItemDocument)
            await item_model.update(str(new_item.id), {"slug": item_slug})
            await category_service.add_item_to_category(str(new_cat.id), str(new_item.id))

    return new_menu
