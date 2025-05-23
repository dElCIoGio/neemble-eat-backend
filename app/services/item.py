from app.models.item import ItemModel

item_model = ItemModel()

async def create_item(data: dict):
    return await item_model.create(data)

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

