from fastapi import APIRouter, HTTPException, Depends, Body

from app.services.user import user_model
from app.utils.auth import get_current_user
from app.schema import role as role_schema
from app.services import roles as role_service

router = APIRouter()

@router.post("/")
async def create_role(data: role_schema.RoleCreate):
    try:
        role = await role_service.create_role(data)
        return role.to_response()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{role_id}")
async def get_role(role_id: str):
    role = await role_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role.to_response()

@router.get("/restaurant/{restaurant_id}")
async def list_restaurant_roles(restaurant_id: str):
    roles = await role_service.list_roles(restaurant_id)
    return [r.to_response() for r in roles]

@router.put("/{role_id}")
async def update_role(role_id: str, data: role_schema.RoleUpdate = Body(...)):
    try:
        updated = await role_service.update_role(role_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Role not found")
        return updated.to_response()
    except Exception as error:
        print(error)
        raise HTTPException(status_code=500, detail=str(error))

@router.delete("/{role_id}")
async def deactivate_role(role_id: str):
    updated = await role_service.deactivate_role(role_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    return True


@router.delete("/hard/{role_id}")
async def delete_role(role_id: str, uid: str = Depends(get_current_user)):
    try:
        user = await user_model.get_user_by_firebase_uid(uid)
        deleted = await role_service.delete_role(role_id, str(user.id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Role not found")
        return True
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
