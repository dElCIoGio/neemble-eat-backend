from app.models.user import UserModel
from app.schema.user import UserRestaurantMembership, UserDocument

user_model = UserModel()


async def add_staff_member(
        user_id: str,
        restaurant_id: str,
        role_id: str
) -> UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    # Check if already assigned to this restaurant
    for membership in user.memberships:
        if membership.restaurant_id == restaurant_id:
            raise Exception("User already belongs to this restaurant")

    user.memberships.append(UserRestaurantMembership(
        restaurant_id=restaurant_id,
        role_id=role_id
    ))
    await user_model.update(user_id, {"memberships": user.memberships})
    return user


async def remove_staff_member(
        user_id: str,
        restaurant_id: str
) -> UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    user.memberships = [
        m for m in user.memberships
        if m.restaurant_id != restaurant_id
    ]
    await user_model.update(user_id, {"memberships": user.memberships})
    return user


async def update_staff_role(
        user_id: str,
        restaurant_id: str,
        new_role_id: str
) -> UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    updated = False
    for membership in user.memberships:
        if membership.restaurant_id == restaurant_id:
            membership.role_id = new_role_id
            updated = True

    if not updated:
        raise Exception("User is not a staff member of this restaurant")

    await user_model.update(user_id, {"memberships": user.memberships})
    return user


async def list_staff(
        restaurant_id: str,
        role_filter: str = None
) -> list[UserDocument]:
    users = await user_model.get_by_fields({"isActive": True})

    def belongs_to_restaurant(user: UserDocument) -> bool:
        return any(
            m.restaurant_id == restaurant_id and (role_filter is None or m.role_id == role_filter)
            for m in user.memberships
        )

    return [user for user in users if belongs_to_restaurant(user)]


async def get_staff(
        user_id: str
) -> UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")
    return user


async def deactivate_staff(
        user_id: str
) -> UserDocument:
    return await user_model.update(user_id, {"isActive": False})


async def reactivate_staff(
        user_id: str
) -> UserDocument:
    return await user_model.update(user_id, {"isActive": True})
