from app.db.crud import MongoCrud
from app.schema import supplier as supplier_schema


class SupplierModel(MongoCrud[supplier_schema.SupplierDocument]):
    def __init__(self):
        super().__init__(supplier_schema.SupplierDocument)
