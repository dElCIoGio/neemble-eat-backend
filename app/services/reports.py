from datetime import datetime
from typing import List, Optional

from app.schema.reports import SalesReport, SalesReportPagination
from app.schema.invoice import InvoiceDocument, InvoiceStatus


async def _aggregate_sales(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
) -> List[SalesReport]:
    """Return aggregated sales for each day in the range."""
    coll = InvoiceDocument.get_motor_collection()
    pipeline = [
        {
            "$match": {
                "restaurantId": restaurant_id,
                "createdAt": {"$gte": from_date, "$lte": to_date},
                "status": InvoiceStatus.PAID.value,
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "grossSales": {"$sum": {"$ifNull": ["$total", 0]}},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    docs = await coll.aggregate(pipeline).to_list(None)
    reports = [
        SalesReport(
            date=datetime.fromisoformat(doc["_id"]),
            grossSales=round(doc.get("grossSales", 0.0), 2),
            orders=doc.get("orders", 0),
        )
        for doc in docs
    ]
    return reports


async def paginate_sales_reports(
    restaurant_id: str,
    from_date: datetime,
    to_date: datetime,
    limit: int = 10,
    cursor: Optional[str] = None,
) -> SalesReportPagination:
    """Paginate ``SalesReport`` entries for a date range."""
    reports = await _aggregate_sales(restaurant_id, from_date, to_date)
    skip = int(cursor) if cursor else 0
    items = reports[skip : skip + limit]
    has_more = skip + limit < len(reports)
    next_cursor = str(skip + limit) if has_more else None
    return SalesReportPagination(
        items=items,
        nextCursor=next_cursor,
        totalCount=len(reports),
        hasMore=has_more,
    )
