from app.db.crud import MongoCrud
from app.schema import role as role_schema


class RoleModel(MongoCrud[role_schema.RoleDocument]):

    def __init__(self):
        super().__init__(role_schema.RoleDocument)