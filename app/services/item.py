from app.models.item import ItemModel
from app.utils.slug import generate_unique_slug
from app.schema import item as item_schema

item_model = ItemModel()

async def create_item(data: dict):
    payload = data.copy()
    payload["slug"] = await generate_unique_slug(payload["name"], item_schema.ItemDocument)
    return await item_model.create(payload)

async def update_item(item_id: str, data: dict):
    return await item_model.update(item_id, data)

async def delete_item(item_id: str):
    return await item_model.delete(item_id)

async def list_items_by_category(category_id: str):
    filters = {
        "categoryId": category_id,
        "isAvailable": True
    }
    return await item_model.get_by_fields(filters)

async def get_item_by_slug(slug: str):
    return await item_model.get_by_slug(slug)

