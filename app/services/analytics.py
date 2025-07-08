from datetime import datetime, timedelta
from typing import Dict, List
from starlette.exceptions import HTTPException

from app.models.invoice import InvoiceModel
from app.models.order import OrderModel
from app.models.table_session import TableSessionModel
from app.schema.analytics import (
    ItemOrderQuantity,
    SalesSummary,
    InvoiceCount,
    OrderCount,
    CancelledCount,
    AverageSessionDuration,
    ActiveSessionCount,
    TotalOrdersCount,
)
from app.schema.invoice import InvoiceDocument, InvoiceStatus
from app.utils.time import now_in_luanda


order_model = OrderModel()
invoice_model = InvoiceModel()
session_model = TableSessionModel()

async def get_sales_summary(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> SalesSummary:
    """Return aggregated sales metrics for a date range.

    Metrics include total sales, invoice counts and revenue per table. It
    also calculates the growth for the same duration immediately preceding
    the provided range.
    """
    def _compute_metrics(inv_list: List[InvoiceDocument]):
        total_sales = sum(inv.total or 0.0 for inv in inv_list)
        invoice_count = len(inv_list)
        average_invoice = (
            total_sales / invoice_count if invoice_count > 0 else 0.0
        )
        distinct_tables = len(set(inv.session_id for inv in inv_list))
        revenue_per_table = (
            total_sales / distinct_tables if distinct_tables > 0 else 0.0
        )
        return (
            round(total_sales, 2),
            invoice_count,
            round(average_invoice, 2),
            distinct_tables,
            round(revenue_per_table, 2),
        )

    def _growth(current: float, previous: float) -> float | None:
        if previous == 0:
            return None
        return round(((current - previous) / previous) * 100, 2)

    # current period invoices
    filters = {
        "restaurantId": restaurant_id,
        "createdAt": {"$gte": from_date, "$lte": to_date},
    }
    invoices = await invoice_model.get_by_fields(filters)

    current_metrics = _compute_metrics(invoices or [])

    # previous period invoices
    period_delta = to_date - from_date
    prev_from = from_date - period_delta
    prev_to = prev_from + period_delta
    prev_filters = {
        "restaurantId": restaurant_id,
        "createdAt": {"$gte": prev_from, "$lte": prev_to},
    }
    previous_invoices = await invoice_model.get_by_fields(prev_filters)
    previous_metrics = _compute_metrics(previous_invoices or [])

    growths = [
        _growth(curr, prev)
        for curr, prev in zip(current_metrics, previous_metrics)
    ]

    return SalesSummary(
        total_sales=current_metrics[0],
        invoice_count=current_metrics[1],
        average_invoice=current_metrics[2],
        distinct_tables=current_metrics[3],
        revenue_per_table=current_metrics[4],
        total_sales_growth=growths[0],
        invoice_count_growth=growths[1],
        average_invoice_growth=growths[2],
        distinct_tables_growth=growths[3],
        revenue_per_table_growth=growths[4],
    )


async def count_invoices(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
    status_filter: str,
) -> InvoiceCount:
    """Count invoices for a restaurant in a specific period."""

    filters = {
        "restaurantId": restaurant_id,
        "createdAt": {"$gte": from_date, "$lte": to_date},
        "status": InvoiceStatus.PAID,
    }

    invoices = await invoice_model.get_by_fields(filters)
    count = len(invoices)

    return InvoiceCount(invoice_count=count)


async def count_orders(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
) -> OrderCount:
    """Count all orders within a date range for a restaurant."""

    try:
        filters = {
            "restaurantId": restaurant_id,
            "createdAt": {"$gte": from_date, "$lte": to_date},
        }
        documents = await order_model.get_by_fields(filters)

        count = len(documents)
        return OrderCount(order_count=count)

    except Exception as e:
        raise HTTPException(detail=str(e), status_code=400)




async def get_top_items(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
    top_n: int = 5
) -> List[ItemOrderQuantity]:

    """Return the most frequently ordered items within a period."""

    # 1. Filter orders
    orders = await order_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "createdAt": {"$gte": from_date, "$lte": to_date},
            "prepStatus": {
                "$in": ["queued", "in_progress", "ready", "delivered"]
            },
        }
    )

    if not orders:
        return []

    # 2. Count by item_id
    counter: Dict[str, ItemOrderQuantity] = {}

    for order in orders:
        key = order.item_id
        if key not in counter:
            item = ItemOrderQuantity(
                item_id=key,
                item_name=getattr(order, "ordered_item_name", None),
                quantity=0,
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

    """Count the number of cancelled orders in the period."""

    documents = await order_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "prepStatus": "cancelled",
            "createdAt": {"$gte": from_date, "$lte": to_date},
        }
    )
    count = len(documents)

    return CancelledCount(cancelled_count=count)


async def count_cancelled_sessions(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> CancelledCount:
    """Count the number of cancelled sessions in the period."""

    documents = await session_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "status": "cancelled",
            "startTime": {"$gte": from_date},
            "endTime": {"$lte": to_date},
        }
    )
    count = len(documents)

    return CancelledCount(cancelled_count=count)


async def average_session_duration(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime
) -> AverageSessionDuration:

    """Compute the average duration of closed sessions for a period."""

    sessions = await session_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "status": "closed",
            "startTime": {"$gte": from_date},
            "endTime": {"$lte": to_date},
        }
    )

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
    """Return the number of active sessions with at least one order."""

    sessions = await session_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "status": "active",
            "orders": {"$ne": []},
        }
    )
    count = len(sessions)
    return ActiveSessionCount(active_sessions=count)



async def last_seven_days_order_count(
        restaurant_id: str,
):
    """Return the number of orders for each of the last seven days.

    The count is based on the ``createdAt`` field so that orders are grouped
    strictly by the day they were placed. ``createdAt`` was previously used
    which could include documents created on a different day from when the
    order was placed. Using ``createdAt`` ensures each day's window is
    correctly respected.
    """

    days: List[TotalOrdersCount] = []

    try:
        now = now_in_luanda()

        for i in range(7):
            day = now - timedelta(days=i + 1)

            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=0)
            weekday = day_start.strftime("%A")

            documents = await order_model.get_by_fields(
                {
                    "restaurantId": restaurant_id,
                    "createdAt": {"$gte": day_start, "$lte": day_end},
                },
                limit=0,
            )

            count = len(documents)

            data = TotalOrdersCount(
                day=weekday,
                sales=count,
                date=str(day_start.isoformat())
            )

            days.append(data)

        return days
    except Exception as error:
        print(error)
