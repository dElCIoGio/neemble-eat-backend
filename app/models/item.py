from app.db.crud import MongoCrud
from app.schema import item as item_schema


class ItemModel(MongoCrud[item_schema.ItemDocument]):
    def __init__(self):
        super().__init__(item_schema.ItemDocument)