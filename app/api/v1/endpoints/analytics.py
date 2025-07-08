from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from app.services.analytics import (
    get_sales_summary,
    count_invoices,
    count_orders,
    get_top_items,
    count_cancelled_orders,
    count_cancelled_sessions,
    average_session_duration,
    active_sessions_count, last_seven_days_order_count
)
from app.utils.time import now_in_luanda

router = APIRouter()


@router.get("/sales-summary")
async def sales_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):

    today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

    if not from_date:
        from_date = today
    if not to_date:
        to_date = today + timedelta(days=1)
    else:
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    summary = await get_sales_summary(restaurant_id, from_date, to_date)

    return summary

@router.get("/invoices")
async def invoices_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    status: str = Query("paid")
):
    try:
        today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

        if not from_date:
            from_date = today
        if not to_date:
            to_date = today + timedelta(days=1)
        else:
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return await count_invoices(restaurant_id, from_date, to_date, status_filter=status)
    except Exception as error:
        print(error)

@router.get("/orders")
async def orders_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

    if not from_date:
        from_date = today
    if not to_date:
        to_date = today + timedelta(days=1)
    else:
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

    return await count_orders(restaurant_id, from_date, to_date)

# Add menu filtering
@router.get("/top-items")
async def top_items_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    top_n: int = Query(5, ge=1, le=20, alias="topN")
):
    try:
        today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

        if not from_date:
            from_date = today
        if not to_date:
            to_date = today + timedelta(days=1)
        else:
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return await get_top_items(restaurant_id, from_date, to_date, top_n=top_n)
    except Exception as error:
        print(error)

@router.get("/cancelled-orders")
async def cancelled_orders_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

    if not from_date:
        from_date = today
    if not to_date:
        to_date = today + timedelta(days=1)
    else:
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)


    return await count_cancelled_orders(restaurant_id, from_date, to_date)


@router.get("/cancelled-sessions")
async def cancelled_sessions_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
):
    today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)

    if not from_date:
        from_date = today
    if not to_date:
        to_date = today + timedelta(days=1)
    else:
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return await count_cancelled_sessions(restaurant_id, from_date, to_date)

@router.get("/session-duration")
async def session_duration_summary(
    restaurant_id: str = Query(..., alias="restaurantId"),
):
    try:
        today = now_in_luanda().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = today
        to_date = today + timedelta(days=1)

        return await average_session_duration(restaurant_id, from_date, to_date)

    except Exception as error:
        print(error)

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