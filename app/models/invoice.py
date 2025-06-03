from app.db.crud import MongoCrud
from app.schema import invoice as invoice_schema


class InvoiceModel(MongoCrud[invoice_schema.InvoiceDocument]):

    def __init__(self):
        super().__init__(invoice_schema.InvoiceDocument)