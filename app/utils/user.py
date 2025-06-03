from app.models.role import RoleModel
from app.schema import user as user_schema
from app.schema.role import Permissions

from app.models.restaurant import RestaurantModel
from app.models.user import UserModel

user_model = UserModel()
restaurant_model = RestaurantModel()
role_model = RoleModel()


async def can_user(user: user_schema.UserDocument, restaurant_id: str, section: str, permission: Permissions) -> bool:

    membership = next((m for m in user.memberships if m.restaurant_id == restaurant_id), None)
    if not membership:
        return False  # User not a member of this restaurant

    role = await role_model.get(membership.role_id)  # Fetch from database
    for sec_perm in role.permissions:
        if sec_perm.section == section and permission in sec_perm.permissions:
            return True
    return False

async def is_member(user_id: str, restaurant_id: str):
    user = await user_model.get(user_id)
    roles_ids = list(map(lambda membership: membership.role_id, user.memberships))
    roles = await role_model.get_many(roles_ids)
    for role in roles:
        if role.restaurant_id == restaurant_id:
            return True
    return False

