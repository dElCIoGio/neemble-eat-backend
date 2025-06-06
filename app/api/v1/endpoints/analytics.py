from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from app.services.analytics import (
    get_sales_summary,
    count_invoices,
    count_orders,
    get_top_items,
    count_cancelled_orders,
    average_session_duration,
    active_sessions_count, last_seven_days_order_count
)

router = APIRouter()


@router.get("/sales-summary")
async def sales_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    if not from_date or not to_date:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)

    return await get_sales_summary(restaurant_id, from_date, to_date)

@router.get("/invoices")
async def invoices_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    status: str = Query("paid")
):
    if not from_date or not to_date:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)

    return await count_invoices(restaurant_id, from_date, to_date, status_filter=status)

@router.get("/orders")
async def orders_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    if not from_date or not to_date:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)
    return await count_orders(restaurant_id, from_date, to_date)

# Add menu filtering
@router.get("/top-items")
async def top_items_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    top_n: int = Query(5, ge=1, le=20, alias="topN")
):
    if not from_date or not to_date:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)

    return await get_top_items(restaurant_id, from_date, to_date, top_n=top_n)

@router.get("/cancelled-orders")
async def cancelled_orders_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    if not from_date or not to_date:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)

    return await count_cancelled_orders(restaurant_id, from_date, to_date)

@router.get("/session-duration")
async def session_duration_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    from_date = today
    to_date = today + timedelta(days=1)

    return await average_session_duration(restaurant_id, from_date, to_date)

@router.get("/active-sessions")
async def active_sessions_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
):
    return await active_sessions_count(restaurant_id)


@router.get("/recent-orders")
async def get_last_seven_days_order_count(
    restaurant_id: str = Query(..., alias="restaurantId")
):
    return await last_seven_days_order_count(restaurant_id)