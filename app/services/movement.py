from datetime import datetime
from typing import List, Optional

from beanie.operators import And, GTE, LTE

from app.models.movement import MovementModel
from app.schema import movement as movement_schema

movement_model = MovementModel()


async def create_movement(data: movement_schema.MovementCreate) -> movement_schema.MovementDocument:
    payload = data.model_dump(by_alias=True)
    return await movement_model.create(payload)


async def list_movements_for_restaurant(
    restaurant_id: str,
    product_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[movement_schema.MovementDocument]:
    filters = {"restaurantId": restaurant_id}
    if product_id:
        filters["productId"] = product_id
    query = movement_schema.MovementDocument.find(filters)
    if start or end:
        date_filter = {}
        if start:
            date_filter["$gte"] = start
        if end:
            date_filter["$lte"] = end
        query = query.find({"date": date_filter})
    return await query.sort("-date").to_list()
