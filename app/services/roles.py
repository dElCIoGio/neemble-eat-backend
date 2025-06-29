from app.models.role import RoleModel
from app.schema.role import (
    RoleDocument,
    SectionPermission,
    Permissions,
    RoleCreate,
    RoleUpdate,
    Sections,
)
from app.models.user import UserModel
from app.schema import user as user_schema

role_model = RoleModel()
user_model = UserModel()


def get_default_roles(restaurant_id: str) -> dict[str, RoleCreate]:
    default_roles: dict[str, RoleCreate] = {
        "gerente": RoleCreate(
            name="gerente",
            level=0,
            description="Acesso total às operações do restaurante",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(
                    section=Sections.ORDERS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.MENUS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.TABLES.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.INVOICES.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.USERS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.PERFORMANCE_INSIGHTS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
            ],
        ),
        "cozinheiro": RoleCreate(
            name="cozinheiro",
            level=1,
            description="Gerencia pedidos de comida na cozinha",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(
                    section=Sections.ORDERS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.KITCHEN_VIEW.value,
                    permissions=Permissions(
                        can_view=True, can_edit=False, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.ORDER_QUEUE.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
            ],
        ),
        "garcom": RoleCreate(
            name="garçom",
            level=2,
            description="Atende mesas e recebe pedidos",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(
                    section=Sections.ORDERS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.TABLES.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.INVOICES.value,
                    permissions=Permissions(
                        can_view=True, can_edit=False, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.ORDER_QUEUE.value,
                    permissions=Permissions(
                        can_view=True, can_edit=False, can_delete=False
                    ),
                ),
            ],
        ),
        "barman": RoleCreate(
            name="barman",
            level=2,
            description="Prepara e serve bebidas",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(
                    section=Sections.ORDERS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.BAR_VIEW.value,
                    permissions=Permissions(
                        can_view=True, can_edit=False, can_delete=False
                    ),
                ),
            ],
        ),
        "contador": RoleCreate(
            name="contador",
            level=1,
            description="Gerencia faturas e análises",
            restaurantId=restaurant_id,
            permissions=[
                SectionPermission(
                    section=Sections.INVOICES.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=True
                    ),
                ),
                SectionPermission(
                    section=Sections.PERFORMANCE_INSIGHTS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=False, can_delete=False
                    ),
                ),
                SectionPermission(
                    section=Sections.PAYMENTS.value,
                    permissions=Permissions(
                        can_view=True, can_edit=True, can_delete=False
                    ),
                ),
            ],
        ),
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
        exclude_unset=True,  # drop fields the client omitted
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
    existing = await role_model.get_by_fields(
        {"restaurantId": restaurant_id, "name": "no_role"}
    )
    if existing:
        return existing[0]
    return await create_role(
        RoleCreate(
            name="no_role",
            description="Fallback role with no permissions",
            restaurantId=restaurant_id,
            permissions=[],
        )
    )


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

    affected_users = await user_model.get_by_fields(
        {"memberships": {"$elemMatch": {"roleId": role_id}}}
    )

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


async def get_user_role_for_current_restaurant(
    user: user_schema.UserDocument,
) -> RoleDocument | None:
    """Return the user's role for their current restaurant."""
    if not user.current_restaurant_id:
        return None
    for membership in user.memberships:
        if membership.is_active:
            role = await role_model.get(membership.role_id)
            if role and role.restaurant_id == user.current_restaurant_id:
                return role
    return None
