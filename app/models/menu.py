from app.db.crud import MongoCrud
from app.schema import menu as menu_schema


class MenuModel(MongoCrud[menu_schema.MenuDocument]):

    model = menu_schema.MenuDocument