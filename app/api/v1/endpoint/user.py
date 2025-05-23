from fastapi import APIRouter, Depends, HTTPException

from app.models.user import UserModel
from app.schema import user as user_schema
from app.utils.auth import get_current_user

router = APIRouter()
user_model = UserModel()


@router.get("/exists", response_model=bool)
async def user_exist(user_data: dict = Depends(get_current_user)):
    uid = user_data.get("uid")
    user = await user_model.get_user_by_firebase_uid(uid)
    return True if user else False
