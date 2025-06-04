from typing import List

from fastapi import APIRouter
from pydantic import EmailStr
from app.schema import invitation as invitation_schema
from app.models.invitation import InvitationModel


router = APIRouter()
invitation_model = InvitationModel()


@router.get("/{email}/email", response_model=List[invitation_schema.Invitation])
async def get_user_invitations(email: EmailStr):
    documents = await invitation_model.get_by_fields({
        "email": email
    })
    invitations = list(map(lambda invitation: invitation.to_response, documents))
    return invitations