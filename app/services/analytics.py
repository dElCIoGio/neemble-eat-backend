from datetime import datetime, timedelta
from typing import Dict, List
from beanie.operators import And, GTE, LTE, Eq, Or
from starlette.exceptions import HTTPException

from app.models.invoice import InvoiceModel
from app.schema.analytics import ItemOrderQuantity, SalesSummary, InvoiceCount, OrderCount, CancelledCount, \
    AverageSessionDuration, ActiveSessionCount, TotalOrdersCount
from app.schema.invoice import InvoiceDocument
from app.schema.order import OrderDocument
from app.schema.table_session import TableSessionDocument
from app.utils.time import now_in_luanda

invoice_model = InvoiceModel()

async def get_sales_summary(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> SalesSummary:


    # 1. Find all PAID invoices in the date range
    filters = {
        "restaurantId": restaurant_id,
        # "status": "paid",
        "createdAt": {"$gte": from_date,}
    }
    invoices = await invoice_model.get_by_fields(filters)


    if invoices is None or invoices is []:
        return SalesSummary(
            total_sales=0.0,
            invoice_count=0,
            average_invoice=0.0,
            distinct_tables=0,
            revenue_per_table=0.0
        )

    # 2. Calculate values
    total_sales = sum(invoice.total or 0.0 for invoice in invoices)
    invoice_count = len(invoices)
    average_invoice = total_sales / invoice_count if invoice_count > 0 else 0.0
    distinct_tables = len(set(inv.session_id for inv in invoices))
    revenue_per_table = total_sales / distinct_tables if distinct_tables > 0 else 0.0

    summary = SalesSummary(
        total_sales=round(total_sales, 2),
        invoice_count=invoice_count,
        average_invoice=round(average_invoice, 2),
        distinct_tables=distinct_tables,
        revenue_per_table=round(revenue_per_table, 2)
    )

    return summary


async def count_invoices(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
) -> InvoiceCount:

    count = await InvoiceDocument.find(
        And(
            Eq(InvoiceDocument.restaurant_id, restaurant_id),
            GTE(InvoiceDocument.created_at, from_date),
            # LTE(InvoiceDocument.created_at, to_date)
        )
    ).count()

    filters = {
        "restaurantId": restaurant_id,
        # "status": "paid",
        "createdAt": {"$gte": from_date}
    }
    invoices = await invoice_model.get_by_fields(filters)
    count = len(invoices)


    return InvoiceCount(invoice_count=count)


async def count_orders(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> OrderCount:

    try:

        count = await OrderDocument.find(
            And(
                Eq(OrderDocument.restaurant_id, restaurant_id),
                GTE(OrderDocument.order_time, from_date),
                # LTE(OrderDocument.order_time, to_date)
            )
        ).count()

        return OrderCount(order_count=count)

    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=400
        )




async def get_top_items(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
    top_n: int = 5
) -> List[ItemOrderQuantity]:

    # 1. Filter orders
    orders = await OrderDocument.find(
        And(
            Eq(OrderDocument.restaurant_id, restaurant_id),
            GTE(OrderDocument.order_time, from_date),
            # LTE(OrderDocument.order_time, to_date),
            Or(
                Eq(OrderDocument.prep_status, "queued"),
                Eq(OrderDocument.prep_status, "in_progress"),
                Eq(OrderDocument.prep_status, "ready"),
                Eq(OrderDocument.prep_status, "delivered")
            )
        )
    ).to_list()

    if not orders:
        return []

    # 2. Count by item_id
    counter: Dict[str, ItemOrderQuantity] = {}

    for order in orders:
        key = order.item_id
        if key not in counter:
            if order.ordered_item_name:
                item = ItemOrderQuantity(
                    item_id=key,
                    item_name=order.ordered_item_name if hasattr(order, "ordered_item_name") else None,
                    quantity=0
                )
                counter[key] = item
        counter[key].quantity += order.quantity

    # 3. Sort and return top N
    sorted_items = sorted(counter.values(), key=lambda x: x.quantity, reverse=True)
    return sorted_items[:top_n]


async def count_cancelled_orders(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> CancelledCount:

    count = await OrderDocument.find(
        And(
            Eq(OrderDocument.restaurant_id, restaurant_id),
            Eq(OrderDocument.prep_status, "cancelled"),
            GTE(OrderDocument.order_time, from_date),
            # LTE(OrderDocument.order_time, to_date)
        )
    ).count()

    return CancelledCount(cancelled_count=count)


async def average_session_duration(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> AverageSessionDuration:

    sessions = await TableSessionDocument.find(
        And(
            Eq(TableSessionDocument.restaurant_id, restaurant_id),
            Eq(TableSessionDocument.status, "closed"),
            GTE(TableSessionDocument.start_time, from_date),
            # LTE(TableSessionDocument.end_time, to_date)
        )
    ).to_list()

    if not sessions:
        return AverageSessionDuration(average_duration_minutes=0.0)

    durations = [
        (s.end_time - s.start_time).total_seconds() / 60.0
        for s in sessions
        if s.end_time and s.start_time
    ]

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return AverageSessionDuration(average_duration_minutes=round(avg_duration, 2))


async def active_sessions_count(
        restaurant_id: str
) -> ActiveSessionCount:
    sessions = await TableSessionDocument.find(
        And(
            Eq(TableSessionDocument.restaurant_id, restaurant_id),
            Eq(TableSessionDocument.status, "active")
        )
    ).to_list()
    sessions = [session for session in sessions if len(session.orders) > 0]
    count = len(sessions)
    return ActiveSessionCount(active_sessions=count)


async def last_seven_days_order_count(
        restaurant_id: str
):
    days = []

    try:
        for i in range(7):
            day = now_in_luanda() - timedelta(days=i + 1)
            day_midnight = day.replace(hour=0, minute=0, second=0, microsecond=0)
            weekday = day_midnight.strftime("%A")

            count = await OrderDocument.find(
                And(
                    Eq(OrderDocument.restaurant_id, restaurant_id),
                    GTE(OrderDocument.order_time, day_midnight),
                )
            ).count()

            data = TotalOrdersCount(
                day=weekday,
                sales=count,
                date=str(day_midnight.isoformat())
            )

            days.append(data)

        return days
    except Exception as error:
        print(error)
