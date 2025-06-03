from app.db.crud import MongoCrud
from app.schema import order as order_schema


class OrderModel(MongoCrud[order_schema.OrderDocument]):

    def __init__(self):
        super().__init__(order_schema.OrderDocument)