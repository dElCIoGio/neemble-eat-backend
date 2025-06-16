from app.db.crud import MongoCrud
from app.schema import movement as movement_schema


class MovementModel(MongoCrud[movement_schema.MovementDocument]):
    def __init__(self):
        super().__init__(movement_schema.MovementDocument)
