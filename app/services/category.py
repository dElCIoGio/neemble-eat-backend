from app.models.category import CategoryModel
from app.schema import category as category_schema
from app.utils.slug import generate_unique_slug

category_model = CategoryModel()

async def create_category(data: category_schema.CategoryCreate):
    payload = data.model_dump(by_alias=False)
    payload["slug"] = await generate_unique_slug(payload["name"], category_schema.CategoryDocument)
    return await category_model.create(payload)

async def update_category(category_id: str, data: category_schema.CategoryUpdate):
    return await category_model.update(category_id, data)

async def delete_category(category_id: str):
    return await category_model.delete(category_id)

async def get_category(category_id: str):
    """Retrieve a category by its id."""
    return await category_model.get(category_id)

async def list_categories_for_menu(menu_id: str):
    """List all active categories that belong to a menu."""
    filters = {"menuId": menu_id}
    result = await category_model.get_by_fields(filters)
    return result

async def update_category_availability(category_id: str, is_active: bool):
    """Switch the availability flag of a category."""
    return await category_model.update(category_id, {"isActive": is_active})

async def list_categories_for_restaurant(restaurant_id: str):
    filters = {"restaurantId": restaurant_id}
    return await category_model.get_by_fields(filters)

async def add_item_to_category(category_id: str, item_id: str):
    category = await category_model.get(category_id)
    if not category:
        raise Exception("Category not found")

    if item_id not in category.item_ids:
        category.item_ids.append(item_id)
        await category_model.update(category_id, {"itemIds": category.item_ids})

    return category

async def remove_item_from_category(category_id: str, item_id: str):
    category = await category_model.get(category_id)
    if not category:
        raise Exception("Category not found")

    if item_id in category.item_ids:
        category.item_ids.remove(item_id)
        await category_model.update(category_id, {"itemIds": category.item_ids})

    return category

async def get_category_by_slug(slug: str):
    return await category_model.get_by_slug(slug)
