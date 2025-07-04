from fastapi import APIRouter, HTTPException, Body, Depends

from app.utils.auth import get_current_user
from app.models.user import UserModel

from app.schema import stock_item as stock_schema
from app.services import stock_item as stock_service

router = APIRouter()
user_model = UserModel()


@router.get("/restaurant/{restaurant_id}")
async def list_stock_items(restaurant_id: str):
    items = await stock_service.list_stock_items_for_restaurant(restaurant_id)
    return [i.to_response() for i in items]


@router.post("/restaurant/{restaurant_id}")
async def create_stock_item(
    restaurant_id: str,
    data: stock_schema.StockItemCreate,
    firebase_uid: str = Depends(get_current_user),
):
    try:
        if data.restaurant_id != restaurant_id:
            raise HTTPException(status_code=400, detail="Mismatched restaurant id")
        user = await user_model.get_user_by_firebase_uid(firebase_uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        item = await stock_service.create_stock_item(
            data,
            user=f"{user.first_name} {user.last_name}",
        )
        return item.to_response()
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/{item_id}")
async def get_stock_item(item_id: str):
    item = await stock_service.get_stock_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_response()


@router.put("/{item_id}")
async def update_stock_item(
    item_id: str,
    data: stock_schema.StockItemUpdate,
    firebase_uid: str = Depends(get_current_user),
):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await stock_service.update_stock_item(
        item_id,
        data,
        user=f"{user.first_name} {user.last_name}",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.delete("/{item_id}")
async def delete_stock_item(
    item_id: str,
    firebase_uid: str = Depends(get_current_user),
):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    deleted = await stock_service.delete_stock_item(
        item_id,
        user=f"{user.first_name} {user.last_name}",
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return True


@router.post("/{item_id}/add")
async def add_stock(
    item_id: str,
    quantity: float = Body(...),
    reason: str = Body("", embed=True),
    firebase_uid: str = Depends(get_current_user),
):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        updated = await stock_service.add_stock(
            item_id,
            quantity,
            reason,
            user=f"{user.first_name} {user.last_name}",
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Item not found")
        return updated.to_response()
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


@router.post("/{item_id}/remove")
async def remove_stock(
    item_id: str,
    quantity: float = Body(...),
    reason: str = Body("", embed=True),
    firebase_uid: str = Depends(get_current_user),
):
    user = await user_model.get_user_by_firebase_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await stock_service.remove_stock(
        item_id,
        quantity,
        reason,
        user=f"{user.first_name} {user.last_name}",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated.to_response()


@router.get("/categories")
async def list_categories():
    return await stock_service.list_categories()


@router.delete("/categories/{name}")
async def delete_category(name: str):
    count = await stock_service.delete_category(name)
    return {"deleted": count}


@router.get("/stats")
async def get_stats(restaurant_id: str):
    return await stock_service.get_stats(restaurant_id)


@router.get("/auto-reorder")
async def list_auto_reorder_items(restaurant_id: str):
    items = await stock_service.list_auto_reorder_items(restaurant_id)
    return [i.to_response() for i in items]
