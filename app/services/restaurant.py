from fastapi import HTTPException

from app.models.restaurant import RestaurantModel
from app.schema import restaurant as restaurant_schema


restaurant_model = RestaurantModel()

async def create_restaurant(data: restaurant_schema.RestaurantCreate):
    try:
        return await restaurant_model.create(data.model_dump(by_alias=False))
    except Exception as error:
        print(error)
        raise HTTPException(detail=str(error), status_code=500)

async def update_restaurant(restaurant_id: str, data: restaurant_schema.RestaurantUpdate):
    return await restaurant_model.update(restaurant_id, data)

async def delete_restaurant(restaurant_id: str):
    return await restaurant_model.delete(restaurant_id)

async def get_restaurants():
    return await restaurant_model.get_all()

async def get_active_restaurants():
    return await restaurant_model.get_by_fields({
        "isActive": True
    })

async def deactivate_restaurant(restaurant_id: str):
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise Exception("Restaurant not found")
    return await restaurant_model.update(restaurant_id, {"isActive": False})

async def get_restaurant(restaurant_id: str):
    return await restaurant_model.get(restaurant_id)


