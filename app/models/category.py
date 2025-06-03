from app.db.crud import MongoCrud
from app.schema import category as category_schema


class CategoryModel(MongoCrud[category_schema.CategoryDocument]):

    def __init__(self):
        super().__init__(category_schema.CategoryDocument)