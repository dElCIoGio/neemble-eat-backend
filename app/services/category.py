from app.models.category import CategoryModel
from app.schema import category as category_schema

category_model = CategoryModel()

async def create_category(data: category_schema.CategoryCreate):
    return await category_model.create(data.model_dump(by_alias=False))

async def update_category(category_id: str, data: category_schema.CategoryUpdate):
    return await category_model.update(category_id, data)

async def delete_category(category_id: str):
    return await category_model.delete(category_id)

async def list_categories_for_restaurant(restaurant_id: str):
    filters = {"restaurantId": restaurant_id, "isActive": True}
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
