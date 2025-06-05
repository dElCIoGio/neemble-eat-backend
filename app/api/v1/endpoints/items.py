from fastapi import APIRouter, HTTPException

from app.schema import item as item_schema
from app.services import item as item_service
from app.services.item import item_model
from app.utils.slug import generate_unique_slug

router = APIRouter()


@router.post("/")
async def create_item(data: item_schema.ItemCreate):
    try:
        created = await item_service.create_item(data.model_dump(by_alias=True))
        slug = await generate_unique_slug(name=created.name, model=item_schema.ItemDocument)
        item = await item_model.update(created.id, {"slug": slug})
        return item.to_response()
    except Exception as error:
        if item:
            await item_model.delete(item.id)
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/{item_id}")
async def get_item(item_id: str):
    item = await item_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_response()

@router.get("/slug/{item_id}")
async def get_item_by_slug(item_slug: str):
    item = await item_service.get_item_by_slug(item_slug)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_response()


@router.delete("/{item_id}")
async def delete_item(item_id: str):
    is_deleted = await item_service.delete_item(item_id)
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return is_deleted


@router.put("/{item_id}")
async def update_item(item_id: str, data: item_schema.ItemUpdate):
    updated = await item_service.update_item(item_id, data.model_dump(exclude_none=True, by_alias=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.put("/{item_id}/availability")
async def switch_item_availability(item_id: str):
    updated = await item_service.update_item_availability(item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.post("/{item_id}/customizations")
async def add_customization(item_id: str, customization: item_schema.CustomizationRule):
    updated = await item_service.add_customization(item_id, customization)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.put("/{item_id}/customizations/{index}")
async def update_customization(item_id: str, index: int, customization: item_schema.CustomizationRule):
    updated = await item_service.update_customization(item_id, index, customization)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not or customization not found")
    return updated.to_response()


@router.delete("/{item_id}/customizations/{index}")
async def delete_customization(item_id: str, index: int):
    updated = await item_service.delete_customization(item_id, index)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not or customization not found")
    return updated.to_response()


@router.post("/{item_id}/customizations/{c_index}/options")
async def add_customization_option(item_id: str, c_index: int, option: item_schema.CustomizationOption):
    updated = await item_service.add_customization_option(item_id, c_index, option)
    if not updated:
        raise HTTPException(status_code=404, detail="Item or customization not found")
    return updated.to_response()


@router.put("/{item_id}/customizations/{c_index}/options/{o_index}")
async def update_customization_option(
    item_id: str,
    c_index: int,
    o_index: int,
    option: item_schema.CustomizationOption,
):
    updated = await item_service.update_customization_option(item_id, c_index, o_index, option)
    if not updated:
        raise HTTPException(status_code=404, detail="Item or option not found")
    return updated.to_response()


@router.delete("/{item_id}/customizations/{c_index}/options/{o_index}")
async def delete_customization_option(item_id: str, c_index: int, o_index: int):
    updated = await item_service.delete_customization_option(item_id, c_index, o_index)
    if not updated:
        raise HTTPException(status_code=404, detail="Item or option not found")
    return updated.to_response()

