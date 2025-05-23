from app.db.crud import MongoCrud
from app.schema import invitation as invitation_schema


class InvitationModel(MongoCrud[invitation_schema.InvitationDocument]):

    model = invitation_schema.InvitationDocument