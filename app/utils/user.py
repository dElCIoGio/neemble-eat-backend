from app.models.role import RoleModel
from app.schema import user as user_schema
from app.schema.role import Permissions



async def can_user(user: user_schema.UserDocument, restaurant_id: str, section: str, permission: Permissions) -> bool:

    role_model = RoleModel()

    membership = next((m for m in user.memberships if m.restaurant_id == restaurant_id), None)
    if not membership:
        return False  # User not a member of this restaurant

    role = await role_model.get(membership.role_id)  # Fetch from database
    for sec_perm in role.permissions:
        if sec_perm.section == section and permission in sec_perm.permissions:
            return True
    return False