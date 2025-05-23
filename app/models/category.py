from app.db.crud import MongoCrud
from app.schema import category as category_schema


class CategoryModel(MongoCrud[category_schema.CategoryDocument]):

    model = category_schema.CategoryDocument