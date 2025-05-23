
from app.models.role import RoleModel
from app.schema.role import RoleDocument, SectionPermission, Permissions, RoleCreate

role_model = RoleModel()


def get_default_roles(restaurant_id: str) -> dict[str, RoleCreate]:
    default_roles: dict[str, RoleCreate] = {
        "manager": RoleCreate(
            name="manager",
            description="Full access to restaurant operations",
            restaurant_id=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="menu", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="tables", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="invoices", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="staff", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="analytics", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
            ]
        ),
        "chef": RoleCreate(
            name="chef",
            description="Manages food orders in the kitchen",
            restaurant_id=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(can_view=True, can_edit=True, can_delete=False)),
            ]
        ),
        "waiter": RoleCreate(
            name="waiter",
            description="Handles tables and takes orders",
            restaurant_id=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(can_view=True, can_edit=True, can_delete=False)),
                SectionPermission(section="tables", permissions=Permissions(can_view=True, can_edit=True, can_delete=False)),
                SectionPermission(section="invoices", permissions=Permissions(can_view=True, can_edit=False, can_delete=False)),
            ]
        ),
        "bartender": RoleCreate(
            name="bartender",
            description="Prepares and serves drinks",
            restaurant_id=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(can_view=True, can_edit=True, can_delete=False)),
            ]
        ),
        "accountant": RoleCreate(
            name="accountant",
            description="Manages invoices and analytics",
            restaurant_id=restaurant_id,
            permissions=[
                SectionPermission(section="invoices", permissions=Permissions(can_view=True, can_edit=True, can_delete=True)),
                SectionPermission(section="analytics", permissions=Permissions(can_view=True, can_edit=False, can_delete=False)),
            ]
        )
    }

    return default_roles



async def create_default_roles_for_restaurant(restaurant_id: str) -> list[RoleDocument]:
    default_roles = get_default_roles(restaurant_id)

    roles = []

    for role_create in default_roles.values():

        role = await create_role(role_create)
        roles.append(role)

    return roles


async def create_role(data: RoleCreate) -> RoleDocument:
    return await role_model.create(data.model_dump(by_alias=True))

async def update_role(role_id: str, data: dict) -> RoleDocument:
    return await role_model.update(role_id, data)


async def deactivate_role(role_id: str) -> RoleDocument:
    return await role_model.update(role_id, {"isActive": False})


async def get_role(role_id: str) -> RoleDocument:
    return await role_model.get(role_id)


async def list_roles(restaurant_id: str) -> list[RoleDocument]:
    filters = {
        "restaurantId": restaurant_id,
        "isActive": True
    }
    return await role_model.get_by_fields(filters)


