from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query

from app.schema import movement as movement_schema
from app.services import movement as movement_service
from app.services.movement import movement_model

router = APIRouter()


@router.get("/paginate")
async def paginate_movements(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
    restaurant_id: str = Query(..., alias="restaurantId")
):
    try:
        filters: Dict[str, Any] = {
            "restaurantId": restaurant_id
        }

        result = await movement_service.movement_model.paginate(filters=filters, limit=limit, cursor=cursor)

        return result
    except Exception as error:
        print(error)

@router.get("/restaurant/{restaurant_id}")
async def list_movements(
    restaurant_id: str,
    product_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    movements = await movement_service.list_movements_for_restaurant(
        restaurant_id, product_id=product_id, start=start, end=end
    )
    return [m.to_response() for m in movements]


@router.post("/restaurant/{restaurant_id}")
async def create_movement(restaurant_id: str, data: movement_schema.MovementCreate):
    if data.restaurant_id != restaurant_id:
        raise HTTPException(status_code=400, detail="Mismatched restaurant id")
    movement = await movement_service.create_movement(data)
    return movement.to_response()
