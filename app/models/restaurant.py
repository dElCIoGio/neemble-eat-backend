from app.db.crud import MongoCrud
from app.schema import restaurant as restaurant_schema


class RestaurantModel(MongoCrud[restaurant_schema.RestaurantDocument]):

    model = restaurant_schema.RestaurantDocument