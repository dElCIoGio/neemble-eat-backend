
from app.models.role import RoleModel
from app.schema.role import RoleDocument, SectionPermission, Permissions, RoleCreate

role_model = RoleModel()


def get_default_roles(restaurant_id: str) -> dict[str, RoleCreate]:
    default_roles: dict[str, RoleCreate] = {
        "manager": RoleCreate(
            name="manager",
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
            description="Manages food orders in the kitchen",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
            ]
        ),
        "waiter": RoleCreate(
            name="waiter",
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
            description="Prepares and serves drinks",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(section="orders", permissions=Permissions(canView=True, canEdit=True, canDelete=False)),
            ]
        ),
        "accountant": RoleCreate(
            name="accountant",
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

        print("New role created:", role.name)

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


