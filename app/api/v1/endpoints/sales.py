from datetime import datetime

from fastapi import APIRouter, HTTPException, Body

from app.services import sale as sale_service

router = APIRouter()


@router.get("/")
async def list_sales():
    sales = await sale_service.list_sales()
    return [s.to_response() for s in sales]


@router.post("/restaurant/{restaurant_id}")
async def register_sale(restaurant_id: str, recipe_id: str = Body(..., alias="recipeId"), quantity: int = Body(...)):
    sale = await sale_service.create_sale(recipe_id, quantity)
    if not sale:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return sale.to_response()


@router.get("/restaurant/{restaurant_id}/day/{day}")
async def sales_for_day(restaurant_id: str, day: datetime):
    """Return sales for a restaurant on a given day."""
    try:
        sales = await sale_service.list_sales_for_day(restaurant_id, day)
        return [s.to_response() for s in sales]
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

