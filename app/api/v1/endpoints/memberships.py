from fastapi import APIRouter, HTTPException

from app.services import membership as membership_service
from app.schema import membership as membership_schema

router = APIRouter()

@router.post("/")
async def create_membership(data: membership_schema.MembershipCreate):
    try:
        user = await membership_service.add_membership(data.user_id, data.role_id)
        return user.to_response()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/restaurant/{restaurant_id}")
async def update_membership(user_id: str, restaurant_id: str, data: membership_schema.MembershipUpdate):
    try:
        user = await membership_service.update_membership_role(user_id, restaurant_id, data.role_id)
        return user.to_response()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/restaurant/{restaurant_id}/deactivate")
async def deactivate_membership(user_id: str, restaurant_id: str):
    try:
        user = await membership_service.deactivate_membership(user_id, restaurant_id)
        return user.to_response()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
async def list_user_memberships(user_id: str):
    try:
        memberships = await membership_service.list_user_memberships(user_id)
        return [m.model_dump(by_alias=True) for m in memberships]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/restaurant/{restaurant_id}")
async def get_membership(user_id: str, restaurant_id: str):
    try:
        membership = await membership_service.get_membership(user_id, restaurant_id)
        return membership.model_dump(by_alias=True)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}/restaurant/{restaurant_id}/activate")
async def activate_membership(user_id: str, restaurant_id: str):
    try:
        user = await membership_service.activate_membership(user_id, restaurant_id)
        return user.to_response()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
