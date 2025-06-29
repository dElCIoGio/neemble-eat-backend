from app.models.user import UserModel
from app.schema import user as user_schema


user_model = UserModel()


async def create_user(user_data: dict, firebase_uid: str):
    # user_data["firebaseUUID"] = firebase_uid
    user_data = user_schema.UserBase(**user_data, firebaseUUID=firebase_uid)
    user_dict = user_data.model_dump(by_alias=True)
    return await user_model.create(user_dict)


async def update_user(user_id: str, data: user_schema.UserUpdate):
    """Update a user by id applying only provided fields."""
    update_data = data.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude_unset=True,
    )
    return await user_model.update(user_id, update_data)


async def update_user_preferences(user_id: str, preferences: user_schema.UserPreferences):
    """Update only the preferences section of a user."""
    pref_dict = preferences.model_dump(by_alias=True)
    return await user_model.update(user_id, {"preferences": pref_dict})
