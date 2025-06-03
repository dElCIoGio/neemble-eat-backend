from app.db.crud import MongoCrud
from app.schema import invitation as invitation_schema


class InvitationModel(MongoCrud[invitation_schema.InvitationDocument]):

    def __init__(self):
        super().__init__(invitation_schema.InvitationDocument)