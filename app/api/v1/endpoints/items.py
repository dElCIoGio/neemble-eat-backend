from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import json

from app.utils.images import save_item_image
from app.services import category as category_service

from app.schema import item as item_schema
from app.services import item as item_service
from app.services.item import item_model
from app.utils.slug import generate_unique_slug

router = APIRouter()


@router.post("/")
async def create_item(
    name: str = Form(...),
    price: str = Form(...),
    restaurant_id: str = Form(..., alias="restaurantId"),
    category_id: str = Form(..., alias="categoryId"),
    description: str = Form(""),
    customizations: Optional[str] = Form(None),
    image_file: UploadFile = File(..., alias="imageFile"),
):

    price = float(price)
    item = None
    created = None
    try:
        customization_rules = []
        if customizations:
            data = json.loads(customizations)
            customization_rules = [item_schema.CustomizationRule(**c) for c in data]

        item_data = item_schema.ItemBase(
            name=name,
            price=price,
            restaurantId=restaurant_id,
            categoryId=category_id,
            description=description,
            customizations=customization_rules,
            imageUrl="",
        )

        created = await item_service.create_item(item_data.model_dump(by_alias=True))

        upload = await save_item_image(image_file, restaurant_id, str(created.id))
        if not upload.success:
            await item_model.delete(created.id)
            raise HTTPException(status_code=500, detail="Failed to upload item image")

        slug = await generate_unique_slug(
            name=created.name, model=item_schema.ItemDocument
        )
        item = await item_model.update(
            created.id,
            {"slug": slug, "imageUrl": upload.public_url},
        )

        await category_service.add_item_to_category(category_id, str(created.id))

        return item.to_response()
    except Exception as error:
        if created:
            await item_model.delete(created.id)
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
    updated = await item_service.update_item(
        item_id, data.model_dump(exclude_none=True, by_alias=True)
    )
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
async def update_customization(
    item_id: str, index: int, customization: item_schema.CustomizationRule
):
    updated = await item_service.update_customization(item_id, index, customization)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Item not or customization not found"
        )
    return updated.to_response()


@router.delete("/{item_id}/customizations/{index}")
async def delete_customization(item_id: str, index: int):
    updated = await item_service.delete_customization(item_id, index)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Item not or customization not found"
        )
    return updated.to_response()


@router.post("/{item_id}/customizations/{c_index}/options")
async def add_customization_option(
    item_id: str, c_index: int, option: item_schema.CustomizationOption
):
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
    updated = await item_service.update_customization_option(
        item_id, c_index, o_index, option
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item or option not found")
    return updated.to_response()


@router.delete("/{item_id}/customizations/{c_index}/options/{o_index}")
async def delete_customization_option(item_id: str, c_index: int, o_index: int):
    updated = await item_service.delete_customization_option(item_id, c_index, o_index)
    if not updated:
        raise HTTPException(status_code=404, detail="Item or option not found")
    return updated.to_response()


@router.get("/category/{category_id}")
async def list_active_items(category_id: str):
    """Return all active items that belong to the given category."""
    items = await item_service.list_items_by_category(category_id)
    return [i.to_response() for i in items]
