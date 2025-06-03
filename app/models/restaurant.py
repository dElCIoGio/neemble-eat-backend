from app.db.crud import MongoCrud
from app.schema import restaurant as restaurant_schema


class RestaurantModel(MongoCrud[restaurant_schema.RestaurantDocument]):

    def __init__(self):
        super().__init__(restaurant_schema.RestaurantDocument)