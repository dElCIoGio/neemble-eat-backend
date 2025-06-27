
from app.models.role import RoleModel
from app.schema.role import RoleDocument, SectionPermission, Permissions, RoleCreate, RoleUpdate
from app.models.user import UserModel
from app.schema import user as user_schema

role_model = RoleModel()
user_model = UserModel()


def get_default_roles(restaurant_id: str) -> dict[str, RoleCreate]:
    default_roles: dict[str, RoleCreate] = {
        "manager": RoleCreate(
            name="manager",
            level=0,
            description="Full access to restaurant operations",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="menu", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="tables", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="invoices", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="staff", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="analytics", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
            ]
        ),
        "chef": RoleCreate(
            name="chef",
            level=1,
            description="Manages food orders in the kitchen",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
            ]
        ),
        "waiter": RoleCreate(
            name="waiter",
            level=2,
            description="Handles tables and takes orders",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
                SectionPermission(section="tables", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
                SectionPermission(section="invoices", permissions=Permissions(canView=True, canEdit=False, canDelete=False)),
            ]
        ),
        "bartender": RoleCreate(
            name="bartender",
            level=2,
            description="Prepares and serves drinks",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
            ]
        ),
        "accountant": RoleCreate(
            name="accountant",
            level=1,
            description="Manages invoices and analytics",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="invoices", permissions=Permissions(canView=True, canEdit=True, canDelete=True)),
                SectionPermission(section="analytics", permissions=Permissions(canView=True, canEdit=False, canDelete=False)),
            ]
        )
    }

    return default_roles



async def create_default_roles_for_restaurant(restaurant_id: str) -> list[RoleDocument]:
    default_roles = get_default_roles(restaurant_id)

    roles_names, roles_objects = zip(*default_roles.items())

    roles = []

    for role_create in roles_objects:

        role = await create_role(role_create)

        roles.append(role)

    return roles


async def create_role(data: RoleCreate) -> RoleDocument:
    return await role_model.create(data.model_dump(by_alias=True))

async def update_role(role_id: str, data: RoleUpdate) -> RoleDocument:
    update_data = data.model_dump(
        by_alias=True,  # keep camelCase if you use aliases in Mongo
        exclude_none=True,  # drop explicit nulls
        exclude_unset=True  # drop fields the client omitted
    )
    return await role_model.update(role_id, update_data)


async def deactivate_role(role_id: str) -> RoleDocument:
    return await role_model.update(role_id, {"isActive": False})


async def get_role(role_id: str) -> RoleDocument:
    return await role_model.get(role_id)

async def list_roles(restaurant_id: str) -> list[RoleDocument]:
    filters = {
        "restaurantId": restaurant_id,
    }
    return await role_model.get_by_fields(filters)



async def _get_or_create_no_role(restaurant_id: str) -> RoleDocument:
    existing = await role_model.get_by_fields({
        "restaurantId": restaurant_id,
        "name": "no_role"
    })
    if existing:
        return existing[0]
    return await create_role(RoleCreate(
        name="no_role",
        description="Fallback role with no permissions",
        restaurantId=restaurant_id,
        permissions=[]
    ))


async def delete_role(role_id: str, user_id: str) -> bool:
    user = await user_model.get(user_id)
    if not user:
        raise Exception("User not found")
    if any(m.role_id == role_id for m in user.memberships):
        raise Exception("Cannot delete a role you are assigned to")

    role = await role_model.get(role_id)
    if not role:
        return False

    no_role = await _get_or_create_no_role(role.restaurant_id)

    affected_users = await user_model.get_by_fields({
        "memberships": {"$elemMatch": {"roleId": role_id}}
    })

    for u in affected_users:
        updated = False
        for membership in u.memberships:
            if membership.role_id == role_id:
                membership.role_id = str(no_role.id)
                updated = True
        if updated:
            await user_model.update(str(u.id), {"memberships": u.memberships})

    await role_model.delete(role_id)
    return True

async def get_user_role_for_current_restaurant(user: user_schema.UserDocument) -> RoleDocument | None:
    """Return the user's role for their current restaurant."""
    if not user.current_restaurant_id:
        return None
    for membership in user.memberships:
        if membership.is_active:
            role = await role_model.get(membership.role_id)
            if role and role.restaurant_id == user.current_restaurant_id:
                return role
    return None
