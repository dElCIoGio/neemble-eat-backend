from fastapi import APIRouter, HTTPException, Body
from pydantic import constr

from app.schema import category as category_schema
from app.services import category as category_service
from app.services import item as item_service
from app.services.category import category_model
from app.services.menu import menu_model
from app.utils.slug import generate_unique_slug

router = APIRouter()

@router.post("/")
async def create_category(data: category_schema.CategoryCreate):
    try:
        category = await category_service.create_category(data)
        slug = await generate_unique_slug(name=category.name, model=category_schema.CategoryDocument)
        category = await category_model.update(category.id, {"slug": slug})
        return category.to_response()
    except Exception as error:
        if category:
            await category_model.delete(category.id)
        raise HTTPException(status_code=500, detail=str(error))

@router.get("/{category_id}")
async def get_category(category_id: str):
    category = await category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_response()

@router.put("/{category_id}")
async def update_category(category_id: str, data: category_schema.CategoryUpdate = Body(...)):

    try:
        updated = await category_service.update_category(category_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Category not found")
        return updated.to_response()
    except Exception as error:
        print(str(error))
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@router.delete("/{category_id}")
async def delete_category(category_id: str):
    result = await category_service.delete_category(category_id)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return True

@router.put("/availability/{category_id}")
async def switch_category_availability(
        category_id: str,
        is_active: bool = Body(..., embed=True, alias="isActive")):
    updated = await category_service.update_category_availability(category_id, is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated.to_response()

@router.get("/{category_id}/items")
async def list_category_items(category_id: str):
    items = await item_service.list_items_by_category(category_id)
    return [i.to_response() for i in items]

@router.get("/{category_slug}/slug/items")
async def list_category_items_by_slug(category_slug: str):
    category = await category_model.get_by_slug(category_slug)
    if not category:
        raise HTTPException(
            detail="The menu was not found",
            status_code=400
        )
    items = await item_service.list_items_by_category(category.id)
    return [i.to_response() for i in items]

@router.post("/{category_id}/items/{item_id}")
async def add_item(category_id: str, item_id: str):
    try:
        category = await category_service.add_item_to_category(category_id, item_id)
        return category.to_response()
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))

@router.delete("/{category_id}/items/{item_id}")
async def remove_item(category_id: str, item_id: str):
    try:
        category = await category_service.remove_item_from_category(category_id, item_id)
        return category.to_response()
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))

@router.get("/menu/{menu_id}")
async def list_menu_categories(menu_id: str):
    categories = await category_service.list_categories_for_menu(menu_id)
    return [c.to_response() for c in categories]

@router.get("/menu/slug/{menu_slug}")
async def list_menu_categories_by_slug(menu_slug: str):
    try:
        menu = await menu_model.get_by_slug(menu_slug)
        if not menu:
            raise HTTPException(
                detail="The menu was not found",
                status_code=400
            )

        categories = await category_service.list_categories_for_menu(str(menu.id))
        return [c.to_response() for c in categories]
    except Exception as error:
        raise HTTPException(
            detail=str(error),
            status_code=400
        )

@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_categories(restaurant_id: str):
    categories = await category_service.list_categories_for_restaurant(restaurant_id)
    return [c.to_response() for c in categories]

@router.get("/slug/{slug}")
async def get_category_by_slug(slug: str):
    category = await category_service.get_category_by_slug(slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_response()
