from typing import List

from app.models.user import UserModel
from app.models.role import RoleModel
from app.schema import user as user_schema

user_model = UserModel()
role_model = RoleModel()

async def add_membership(user_id: str, role_id: str) -> user_schema.UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    role = await role_model.get(role_id)
    if not role:
        raise Exception("Role not found")

    existing_role_ids = [m.role_id for m in user.memberships]
    roles = await role_model.get_many(existing_role_ids) if existing_role_ids else []
    role_map = {str(r.id): r for r in roles}

    # Check if membership for the same restaurant exists
    for membership in user.memberships:
        m_role = role_map.get(membership.role_id)
        if m_role and m_role.restaurant_id == role.restaurant_id:
            if membership.is_active:
                raise Exception("User already member of this restaurant")
            membership.is_active = True
            membership.role_id = role_id
            await user_model.update(str(user.id), {"memberships": [m.model_dump(by_alias=True) for m in user.memberships]})
            return await user_model.get(user_id)

    user.memberships.append(user_schema.UserRestaurantMembership(roleId=role_id, isActive=True))
    await user_model.update(str(user.id), {"memberships": [m.model_dump(by_alias=True) for m in user.memberships]})
    return await user_model.get(user_id)

async def update_membership_role(user_id: str, restaurant_id: str, new_role_id: str) -> user_schema.UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    new_role = await role_model.get(new_role_id)
    if not new_role or new_role.restaurant_id != restaurant_id:
        raise Exception("Role not found for restaurant")

    existing_role_ids = [m.role_id for m in user.memberships]
    roles = await role_model.get_many(existing_role_ids) if existing_role_ids else []
    role_map = {str(r.id): r for r in roles}

    updated = False
    for membership in user.memberships:
        m_role = role_map.get(membership.role_id)
        if m_role and m_role.restaurant_id == restaurant_id and membership.is_active:
            membership.role_id = new_role_id
            updated = True
    if not updated:
        raise Exception("Membership not found for restaurant")

    await user_model.update(str(user.id), {"memberships": [m.model_dump(by_alias=True) for m in user.memberships]})
    return await user_model.get(user_id)

async def deactivate_membership(user_id: str, restaurant_id: str) -> user_schema.UserDocument:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")

    existing_role_ids = [m.role_id for m in user.memberships]
    roles = await role_model.get_many(existing_role_ids) if existing_role_ids else []
    role_map = {str(r.id): r for r in roles}

    updated = False
    for membership in user.memberships:
        m_role = role_map.get(membership.role_id)
        if m_role and m_role.restaurant_id == restaurant_id and membership.is_active:
            membership.is_active = False
            updated = True
    if not updated:
        raise Exception("Membership not found for restaurant")

    await user_model.update(str(user.id), {"memberships": [m.model_dump(by_alias=True) for m in user.memberships]})
    if user.current_restaurant_id == restaurant_id:
        await user_model.update(str(user.id), {"currentRestaurantId": None})
    return await user_model.get(user_id)

async def list_user_memberships(user_id: str) -> List[user_schema.UserRestaurantMembership]:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")
    return user.memberships
