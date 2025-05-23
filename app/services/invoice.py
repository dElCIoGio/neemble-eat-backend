from app.models.invoice import InvoiceModel
from app.schema.order import OrderDocument
from app.schema.table_session import TableSessionDocument
from datetime import datetime

invoice_model = InvoiceModel()

async def generate_invoice_for_session(session_id: str):
    session = await TableSessionDocument.get(session_id)
    if not session:
        raise Exception("Session not found")

    if session.status != "closed":
        raise Exception("Session must be closed before generating invoice")

    orders = await OrderDocument.find(OrderDocument.session_id == session_id).to_list()

    if not orders:
        raise Exception("No orders found for this session")

    total = sum(order.total for order in orders if order.is_active)

    invoice_data = {
        "restaurantId": session.restaurant_id,
        "sessionId": str(session.id),
        "orders": [str(order.id) for order in orders],
        "total": total,
        "generatedTime": datetime.now(),
        "status": "pending",
        "isActive": True
    }

    invoice = await invoice_model.create(invoice_data)

    session.invoice_id = str(invoice.id)
    await session.save()

    return invoice

async def get_invoice_by_session(session_id: str):
    filters = {"sessionId": session_id}
    invoices = await invoice_model.get_many(filters)

    if invoices:
        return invoices[0]
    return None

async def mark_invoice_paid(invoice_id: str):
    return await invoice_model.update(invoice_id, {"status": "paid"})

async def cancel_invoice(invoice_id: str):
    return await invoice_model.update(invoice_id, {"status": "cancelled", "isActive": False})

async def list_invoices_for_restaurant(restaurant_id: str):
    filters = {"restaurantId": restaurant_id, "isActive": True}
    return await invoice_model.get_many(filters)
