from app.models.invitation import InvitationModel
from app.schema import invitation as invitation_schema

invitation_model = InvitationModel()


async def create_invitation(data: invitation_schema.InvitationCreate):
    return await invitation_model.create(data.model_dump(by_alias=False))


async def update_invitation(
    invitation_id: str, data: invitation_schema.InvitationUpdate
):
    return await invitation_model.update(invitation_id, data)


async def delete_invitation(invitation_id: str):
    return await invitation_model.delete(invitation_id)


async def get_invitations():
    return await invitation_model.get_all()


async def list_restaurant_invitations(restaurant_id: str):
    filters = {"restaurantId": restaurant_id}
    return await invitation_model.get_by_fields(filters)
