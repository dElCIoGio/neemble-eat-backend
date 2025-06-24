from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import EmailStr

from app.schema import invitation as invitation_schema
from app.models.invitation import InvitationModel
from app.services import invitation as invitation_service

router = APIRouter()
invitation_model = InvitationModel()


@router.post("/", response_model=invitation_schema.Invitation)
async def create_invitation(data: invitation_schema.InvitationCreate):
    try:
        invitation = await invitation_service.create_invitation(data)
        return invitation.to_response()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{invitation_id}")
async def delete_invitation(invitation_id: str):
    deleted = await invitation_service.delete_invitation(invitation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return True


@router.get("/{email}/email", response_model=List[invitation_schema.Invitation])
async def get_user_invitations(email: EmailStr):
    documents = await invitation_model.get_by_fields({"email": email})
    invitations = [inv.to_response() for inv in documents]
    return invitations


@router.get(
    "/restaurant/{restaurant_id}", response_model=List[invitation_schema.Invitation]
)
async def list_restaurant_invitations(restaurant_id: str):
    invitations = await invitation_service.list_restaurant_invitations(restaurant_id)
    return [inv.to_response() for inv in invitations]


@router.get("/{invitation_id}")
async def get_invitation(invitation_id: str):
    invitation = await invitation_model.get(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found"
        )
    return invitation.to_response()
