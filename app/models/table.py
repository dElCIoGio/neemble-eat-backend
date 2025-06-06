from app.db.crud import MongoCrud
from app.schema import table as table_schema

class TableModel(MongoCrud[table_schema.TableDocument]):
    def __init__(self):
        super().__init__(table_schema.TableDocument)
