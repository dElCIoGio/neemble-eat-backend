from app.db.crud import MongoCrud
from app.schema import order as order_schema


class OrderModel(MongoCrud[order_schema.OrderDocument]):

    model = order_schema.OrderDocument