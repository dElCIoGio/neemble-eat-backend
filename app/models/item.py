from app.db.crud import MongoCrud
from app.schema import item as item_schema


class ItemModel(MongoCrud[item_schema.ItemDocument]):

    model = item_schema.ItemDocument