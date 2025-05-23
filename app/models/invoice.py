from app.db.crud import MongoCrud
from app.schema import invoice as invoice_schema


class InvoiceModel(MongoCrud[invoice_schema.InvoiceDocument]):

    model = invoice_schema.InvoiceDocument