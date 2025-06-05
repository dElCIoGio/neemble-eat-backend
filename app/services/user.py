from app.models.user import UserModel
from app.schema import user as user_schema


user_model = UserModel()


async def create_user(user_data: dict, firebase_uid: str):
    # user_data["firebaseUUID"] = firebase_uid
    user_data = user_schema.UserBase(**user_data, firebaseUUID=firebase_uid)
    print(user_data)

    user_dict = user_data.model_dump(by_alias=True)
    return await user_model.create(user_dict)
