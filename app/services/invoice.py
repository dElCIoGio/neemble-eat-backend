from app.models.invoice import InvoiceModel
from app.models.table_session import TableSessionModel
from app.schema.invoice import InvoiceStatus
from app.schema.order import OrderDocument
from datetime import datetime

from app.utils.time import now_in_luanda
from app.schema.invoice_data import InvoiceData, InvoiceItem
from app.services import restaurant as restaurant_service
from app.services import table as table_service
from app.services.order import order_model

session_model = TableSessionModel()
invoice_model = InvoiceModel()

async def generate_invoice_for_session(session_id: str):
    session = await session_model.get(session_id)
    if not session:
        raise Exception("Session not found")

    # if session.status != "closed":
    #     raise Exception("Session must be closed before generating invoice")

    orders = await OrderDocument.find(OrderDocument.session_id == session_id).to_list()

    if orders is None:
        raise Exception("No orders found for this session")

    total = sum(order.total for order in orders if order)

    invoice_data = {
        "restaurantId": session.restaurant_id,
        "sessionId": str(session.id),
        "orders": [str(order.id) for order in orders],
        "total": total,
        "generatedTime": now_in_luanda(),
        "status": "pending",
        "isActive": True
    }

    invoice = await invoice_model.create(invoice_data)

    await session_model.update(str(session.id), {
        "invoiceId": str(invoice.id)
    })

    return invoice

async def get_invoice_by_session(session_id: str):
    filters = {"sessionId": session_id}
    invoices = await invoice_model.get_many(filters)

    if invoices:
        return invoices[0]
    return None

async def mark_invoice_paid(invoice_id: str):
    return await invoice_model.update(invoice_id, {"status": InvoiceStatus.PAID})

async def cancel_invoice(invoice_id: str):
    return await invoice_model.update(invoice_id, {"status": "cancelled", "isActive": False})

async def list_invoices_for_restaurant(restaurant_id: str):
    filters = {"restaurantId": restaurant_id, "isActive": True}
    return await invoice_model.get_many(filters)


async def get_invoice_data(invoice_id: str) -> InvoiceData | None:
    """Return an ``InvoiceData`` structure for the given invoice id."""

    invoice = await invoice_model.get(invoice_id)
    if not invoice:
        return None

    restaurant = await restaurant_service.get_restaurant(invoice.restaurant_id)
    session = await session_model.get(invoice.session_id)

    table_number = 0
    if session:
        table = await table_service.get_table(session.table_id)
        if table:
            table_number = table.number

    orders = []
    if invoice.orders:
        orders = await order_model.get_many(invoice.orders)

    items = [
        InvoiceItem(
            id=str(o.id),
            name=o.ordered_item_name or "",
            unitPrice=o.unit_price,
            quantity=o.quantity,
            total=o.total,
        )
        for o in orders
    ]

    return InvoiceData(
        restaurantName=restaurant.name if restaurant else "",
        restaurantAddress=restaurant.address if restaurant else "",
        restaurantPhoneNumber=restaurant.phone_number if restaurant else "",
        tableNumber=table_number,
        invoiceNumber=str(invoice.id),
        invoiceDate=invoice.generated_time.isoformat(),
        items=items,
        tax=invoice.tax,
        discount=invoice.discount,
        total=invoice.total or 0.0,
    )
