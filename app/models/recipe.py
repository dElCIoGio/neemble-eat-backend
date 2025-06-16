from app.db.crud import MongoCrud
from app.schema import recipe as recipe_schema


class RecipeModel(MongoCrud[recipe_schema.RecipeDocument]):
    def __init__(self):
        super().__init__(recipe_schema.RecipeDocument)
