from typing import List

from fastapi import APIRouter, Depends
from app.services.restaurant import (
    create_restaurant,
    deactivate_restaurant,
    get_restaurant,
    update_restaurant,
    delete_restaurant,
    get_restaurants, get_active_restaurants,
)
from app.schema import restaurant as restaurant_schema
from app.utils.auth import (
    get_current_user,  # returns the logged user without checking if they are admin
    admin_required  # returns the logged user and checks if they are admin
)

router = APIRouter()


@router.post("/", response_model_by_alias=True)
async def create_new_restaurant(data: restaurant_schema.RestaurantCreate, user = Depends(get_current_user)):
    new_restaurant_document = await create_restaurant(data)
    return new_restaurant_document.to_response()


@router.put("/{restaurant_id}/deactivate", dependencies=[Depends(admin_required)])
async def deactivate_existing_restaurant(restaurant_id: str):

    return await deactivate_restaurant(restaurant_id)


@router.get("/{restaurant_id}", dependencies=[Depends(admin_required)])
async def get_single_restaurant(restaurant_id: str):
    return await get_restaurant(restaurant_id)


@router.put("/{restaurant_id}")
async def update_existing_restaurant(restaurant_id: str, data: restaurant_schema.RestaurantUpdate):
    return await update_restaurant(restaurant_id, data)


@router.delete("/{restaurant_id}", dependencies=[Depends(admin_required)])
async def delete_existing_restaurant(restaurant_id: str):
    return await delete_restaurant(restaurant_id)


@router.get("/", response_model_by_alias=True)
async def list_all_restaurants(admin = Depends(admin_required)):
    documents: List[restaurant_schema.RestaurantDocument] = await get_restaurants()
    restaurants = list(map(lambda restaurant: restaurant.to_response, documents))
    return restaurants


@router.get("/active", response_model_by_alias=True)
async def get_active_restaurant(admin = Depends(admin_required)):
    documents = await get_active_restaurants()
    restaurants = list(map(lambda restaurant: restaurant.to_response, documents))
    return restaurants
