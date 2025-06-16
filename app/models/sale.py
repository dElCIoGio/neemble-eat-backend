from app.db.crud import MongoCrud
from app.schema import sale as sale_schema


class SaleModel(MongoCrud[sale_schema.SaleDocument]):
    def __init__(self):
        super().__init__(sale_schema.SaleDocument)
