from typing import Optional

from pydantic import EmailStr

from app.db.crud import MongoCrud
from app.schema import user as user_schema


class UserModel(MongoCrud[user_schema.UserDocument]):

    def __init__(self):
        super().__init__(user_schema.UserDocument)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[user_schema.UserDocument]:
        result = await self.get_by_fields({"firebaseUUID": firebase_uid})
        return result[0] if len(result) > 0 else None

    async def get_user_by_email(self, email: EmailStr) -> Optional[user_schema.UserDocument]:
        result = await self.get_by_fields({"email": email})
        return result[0] if len(result) > 0 else None
