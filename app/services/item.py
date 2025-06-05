from app.models.item import ItemModel
from app.models.category import CategoryModel
from app.utils.slug import generate_unique_slug
from app.schema import item as item_schema

item_model = ItemModel()

async def create_item(data: dict):
    """Create a new item ensuring a unique slug is generated."""
    payload = data.copy()
    payload["slug"] = await generate_unique_slug(payload["name"], item_schema.ItemDocument)
    return await item_model.create(payload)

async def update_item(item_id: str, data: dict):
    """Update an item by id."""
    return await item_model.update(item_id, data)

async def delete_item(item_id: str):
    """Delete an item by id."""
    return await item_model.delete(item_id)

async def list_items_by_category(category_id: str):
    """List all available items for a category."""
    filters = {
        "categoryId": category_id,
        "isAvailable": True
    }
    return await item_model.get_by_fields(filters)

async def get_item_by_slug(slug: str):
    """Retrieve an item by its slug field."""
    return await item_model.get_by_slug(slug)

async def get_item(item_id: str):
    """Retrieve an item by its id."""
    return await item_model.get(item_id)

async def update_item_availability(item_id: str, is_available: bool):
    """Update only the availability flag of an item."""
    return await item_model.update(item_id, {"isAvailable": is_available})


def _serialize_customizations(customizations: list[item_schema.CustomizationRule]):
    """Helper to convert customization rules to dicts with aliases."""
    return [c.model_dump(by_alias=True) for c in customizations]


async def add_customization(item_id: str, customization: item_schema.CustomizationRule):
    """Append a customization rule to an item."""
    item = await item_model.get(item_id)
    if not item:
        return None

    item.customizations.append(customization)
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def update_customization(item_id: str, index: int, customization: item_schema.CustomizationRule):
    """Replace a customization rule at the given index."""
    item = await item_model.get(item_id)
    if not item or index < 0 or index >= len(item.customizations):
        return None

    item.customizations[index] = customization
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def delete_customization(item_id: str, index: int):
    """Remove a customization rule from an item."""
    item = await item_model.get(item_id)
    if not item or index < 0 or index >= len(item.customizations):
        return None

    item.customizations.pop(index)
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def add_customization_option(item_id: str, customization_index: int, option: item_schema.CustomizationOption):
    """Add a customization option to a rule."""
    item = await item_model.get(item_id)
    if not item or customization_index < 0 or customization_index >= len(item.customizations):
        return None

    item.customizations[customization_index].options.append(option)
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def update_customization_option(
        item_id: str,
        customization_index: int,
        option_index: int,
        option: item_schema.CustomizationOption,
):
    """Update a customization option by its index."""
    item = await item_model.get(item_id)
    if (
        not item
        or customization_index < 0
        or customization_index >= len(item.customizations)
        or option_index < 0
        or option_index >= len(item.customizations[customization_index].options)
    ):
        return None

    item.customizations[customization_index].options[option_index] = option
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def delete_customization_option(item_id: str, customization_index: int, option_index: int):
    """Delete a customization option from a rule."""
    item = await item_model.get(item_id)
    if (
        not item
        or customization_index < 0
        or customization_index >= len(item.customizations)
        or option_index < 0
        or option_index >= len(item.customizations[customization_index].options)
    ):
        return None

    item.customizations[customization_index].options.pop(option_index)
    return await item_model.update(item_id, {"customizations": _serialize_customizations(item.customizations)})


async def list_items_by_menu(menu_id: str):
    """List all available items for a specific menu."""
    categories = await CategoryModel().get_by_fields({"menuId": menu_id, "isActive": True})
    all_items: list[item_schema.ItemDocument] = []
    for category in categories:
        items = await item_model.get_by_fields({"categoryId": str(category.id), "isAvailable": True})
        all_items.extend(items)
    return all_items

