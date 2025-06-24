from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

from app.models.restaurant import RestaurantModel
from app.models.role import RoleModel
from app.models.user import UserModel
from app.utils.auth import get_current_user
from app.schema.restaurant import RestaurantDocument
from app.utils.user import is_member
from app.services import roles as role_service

router = APIRouter()
user_model = UserModel()
role_model = RoleModel()
restaurant_model = RestaurantModel()


@router.get("/exists")
async def user_exist(uid: str = Depends(get_current_user)):
    user = await user_model.get_user_by_firebase_uid(uid)
    return True if user else False


@router.get("/paginate")
async def paginate_users(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await user_model.paginate(filters=filters, limit=limit, cursor=cursor)

        return result
    except Exception as error:
        print(error)


@router.get("/user/{user_id}")
async def get_user(user_id: str):
    user = await user_model.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user.to_response()


@router.get("/restaurant")
async def get_current_restaurant(
        uid: str = Depends(get_current_user)
):
    try:
        user = await user_model.get_user_by_firebase_uid(uid)
        if not user:
            raise HTTPException(
                detail="User not found",
                status_code=404
            )
        if user.current_restaurant_id is None:
            return None
        restaurant = await restaurant_model.get(user.current_restaurant_id)
        return restaurant.to_response()
    except Exception as error:
        print(str(error))


@router.put("/restaurant/{restaurant_id}")
async def change_current_restaurant(
    restaurant_id: str,
    uid: str = Depends(get_current_user)
):
    user = await user_model.get_user_by_firebase_uid(uid)
    if not user:
        raise HTTPException(
            detail="User not found",
            status_code=404
        )
    if is_member(str(user.id), restaurant_id):
        await user_model.update(
            str(user.id),
            {
                "currentRestaurantId": restaurant_id
            }
        )
    return True


@router.get("/restaurants")
async def get_restaurants(uid: str = Depends(get_current_user)):
    try:
        user = await user_model.get_user_by_firebase_uid(uid)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all restaurants where the user has an active membership
        active_restaurants = []
        for membership in user.memberships:
            if membership.is_active:

                # Get restaurant details from the restaurant model
                role = await role_model.get(membership.role_id)
                if role:
                    restaurant = await restaurant_model.get(role.restaurant_id)
                    if restaurant:
                        active_restaurants.append({
                            "_id": str(restaurant.id),
                            "name": restaurant.name
                        })

        return active_restaurants
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500,
                             detail=str(e))


@router.get("/role")
async def get_current_role(uid: str = Depends(get_current_user)):
    """Get current user's role for their active restaurant."""
    user = await user_model.get_user_by_firebase_uid(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = await role_service.get_user_role_for_current_restaurant(user)
    if role:
        return role.to_response()
    return None

