from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.services.reports import paginate_sales_reports

router = APIRouter()


@router.get("/sales/paginate")
async def sales_report_paginate(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: datetime = Query(..., alias="fromDate"),
    to_date: datetime = Query(..., alias="toDate"),
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    """Paginate sales reports for a restaurant within a date range."""
    return await paginate_sales_reports(
        restaurant_id=restaurant_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        cursor=cursor,
    )
