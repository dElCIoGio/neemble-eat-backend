from datetime import datetime

from beanie import init_beanie
from firebase_admin.firestore import client
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.client_session import ClientSession
from app.schema import invoice as invoice_schema
from app.schema import order as order_schema
from app.schema import table_session as table_session_schema
from app.core.dependencies import get_mongo


async def generate_invoice_for_session(session_id: str) -> invoice_schema.InvoiceDocument:
    mongo = get_mongo()
    client = mongo.get_client()
    db_session: ClientSession = await client.start_session()

    async with db_session.start_transaction():
        # 1. Find the TableSession
        session = await table_session_schema.TableSessionDocument.get(session_id, session=db_session)
        if not session:
            raise Exception("Session not found")

        if session.status != table_session_schema.TableSessionStatus.CLOSED:
            raise Exception("Session must be CLOSED to generate invoice")

        # 2. Find all Orders for this session
        orders = await order_schema.OrderDocument.find(order_schema.OrderDocument.session_id == session_id, session=db_session).to_list()
        if not orders:
            raise Exception("No orders found for session")

        # 3. Calculate total
        total = sum(order.total for order in orders if order.is_active)

        # 4. Create invoice_schema.Invoice
        invoice = invoice_schema.InvoiceDocument(
            restaurant_id=session.restaurant_id,
            session_id=session.id,
            orders=[str(order.id) for order in orders],
            total=total,
            status=invoice_schema.InvoiceStatus.PENDING,
            generated_time=datetime.now(),
            is_active=True
        )
        await invoice.insert(session=db_session)

        # 5. Link invoice_schema.Invoice ID to Session
        session.invoice_id = str(invoice.id)
        await session.save(session=db_session)

    return invoice
