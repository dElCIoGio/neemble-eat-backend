from app.db.crud import MongoCrud
from app.schema import menu as menu_schema


class MenuModel(MongoCrud[menu_schema.MenuDocument]):

    def __init__(self):
        super().__init__(menu_schema.MenuDocument)