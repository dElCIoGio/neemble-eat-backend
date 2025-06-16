from app.db.crud import MongoCrud
from app.schema import stock_item as stock_item_schema


class StockItemModel(MongoCrud[stock_item_schema.StockItemDocument]):
    def __init__(self):
        super().__init__(stock_item_schema.StockItemDocument)
