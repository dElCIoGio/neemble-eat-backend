from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter

from app.services.ai import (
    OrderData,
    TableOccupancy,
    CustomerReview,
    RestaurantInsightsAnalyzer,
    InsightsOutput,
    InsightItem,
    InsightPriority,
    AnalysisType,
)
from app.services import order as order_service
from app.services import table as table_service
from app.services import restaurant as restaurant_service
from app.services.table_session import session_model
from app.utils.time import now_in_luanda


router = APIRouter()

analyzer = RestaurantInsightsAnalyzer()


async def _get_order_data(restaurant_id: str) -> List[OrderData]:
    orders = await order_service.list_orders_for_restaurant(restaurant_id)
    data: List[OrderData] = []
    for o in orders:
        items = [o.ordered_item_name] if getattr(o, "ordered_item_name", None) else [o.item_id]
        data.append(
            OrderData(
                order_id=str(o.id),
                revenue=o.total or 0,
                timestamp=o.order_time,
                items=items,
                table_number=o.table_number,
            )
        )
    return data


async def _get_occupancy_data(restaurant_id: str) -> List[TableOccupancy]:
    tables = await table_service.list_tables_for_restaurant(restaurant_id)
    total_tables = len(tables)
    if total_tables == 0:
        return []

    sessions = await session_model.get_by_fields({"restaurantId": restaurant_id})
    now = now_in_luanda()
    occ_map: dict[datetime.date, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    for s in sessions:
        start = s.start_time.replace(minute=0, second=0, microsecond=0)
        end = (s.end_time or now).replace(minute=0, second=0, microsecond=0)
        current = start
        while current <= end:
            occ_map[current.date()][current.hour] += 1
            current += timedelta(hours=1)

    data: List[TableOccupancy] = []
    for date, hours in occ_map.items():
        for hour, occupied in hours.items():
            data.append(
                TableOccupancy(
                    date=datetime.combine(date, datetime.min.time()),
                    hour=hour,
                    occupied_tables=occupied,
                    total_tables=total_tables,
                )
            )
    return data


async def _get_review_data(restaurant_id: str) -> List[CustomerReview]:
    sessions = await session_model.get_by_fields({"restaurantId": restaurant_id, "review": {"$ne": None}})
    reviews: List[CustomerReview] = []
    for s in sessions:
        if s.review:
            reviews.append(
                CustomerReview(
                    review_id=str(s.id),
                    text=s.review.comment or "",
                    rating=s.review.stars,
                    timestamp=s.end_time or s.start_time,
                    verified=True,
                    source="internal",
                )
            )
    return reviews


@router.get("/performance/{restaurant_id}")
async def performance_insights(restaurant_id: str):
    data = await _get_order_data(restaurant_id)
    metrics = await analyzer.processors[AnalysisType.PERFORMANCE].process(data)
    if "error" in metrics:
        return metrics
    total_orders = metrics.get("total_orders", 0)
    revenue = metrics.get("total_revenue", 0)
    peak_hours = ", ".join(map(str, metrics.get("peak_hours", []))) or "none identified"
    best_days = ", ".join(metrics.get("best_days", [])) or "no standout days"

    if total_orders == 0:
        opinion = "No orders were found for this restaurant, so performance cannot be assessed."
    else:
        performance = (
            "strong" if revenue > 10000 else "steady" if revenue > 5000 else "developing"
        )
        opinion = (
            f"The restaurant handled {total_orders} orders generating ${revenue:.2f}, "
            f"showing {performance} sales performance. Peak activity occurs around {peak_hours}, "
            f"with best results on {best_days}. Consider reinforcing popular periods and exploring promotions during quieter times."
        )
    return {"insight": opinion}


@router.get("/occupancy/{restaurant_id}")
async def occupancy_insights(restaurant_id: str):
    data = await _get_occupancy_data(restaurant_id)
    metrics = await analyzer.processors[AnalysisType.OCCUPANCY].process(data)
    if "error" in metrics:
        return metrics
    avg_rate = metrics.get("avg_occupancy_rate", 0)
    peak_hours = ", ".join(map(str, metrics.get("peak_hours", []))) or "none identified"
    low_hours = ", ".join(map(str, metrics.get("underutilized_hours", []))) or "none"

    if avg_rate == 0:
        opinion = "No table occupancy data available to evaluate utilization."
    else:
        utilization = (
            "excellent" if avg_rate >= 0.8 else "good" if avg_rate >= 0.6 else "needs improvement"
        )
        opinion = (
            f"Average occupancy sits at {avg_rate:.0%}, indicating {utilization} space usage. "
            f"Tables are busiest around {peak_hours}, while {low_hours} remain underused. "
            f"Balancing these periods could improve overall efficiency."
        )
    return {"insight": opinion}


@router.get("/sentiment/{restaurant_id}")
async def sentiment_insights(restaurant_id: str):
    data = await _get_review_data(restaurant_id)
    metrics = await analyzer.processors[AnalysisType.SENTIMENT].process(data)
    if "error" in metrics:
        return metrics
    dist = metrics.get("sentiment_distribution", {})
    total = sum(dist.values())
    if total == 0:
        opinion = "No customer reviews were found to assess sentiment."
    else:
        overall = metrics.get("overall_sentiment", "neutral")
        avg_rating = metrics.get("avg_rating")
        opinion = (
            f"Customer sentiment is predominantly {overall} with {dist.get('positive', 0)} positive and "
            f"{dist.get('negative', 0)} negative mentions out of {total} reviews. "
            f"The average rating is {avg_rating}. Addressing recurring issues in negative feedback could enhance guest satisfaction."
        )
    return {"insight": opinion}


@router.get("/full/{restaurant_id}", response_model=InsightsOutput)
async def generate_full_insights(restaurant_id: str):
    restaurant = await restaurant_service.get_restaurant(restaurant_id)
    orders = await _get_order_data(restaurant_id)
    occupancy = await _get_occupancy_data(restaurant_id)
    reviews = await _get_review_data(restaurant_id)

    cache_key = analyzer._generate_cache_key(restaurant, orders, occupancy, reviews)
    cached = analyzer._check_cache(cache_key)
    if cached:
        return cached

    trends, occ, sentiment = await analyzer._process_data_sources(orders, occupancy, reviews)
    quality, confidence = analyzer._assess_data_quality(trends, occ, sentiment)

    prompt = (
        f"Orders: {trends}\n"
        f"Occupancy: {occ}\n"
        f"Reviews: {sentiment}"
    )
    llm_result = await analyzer.llm_provider.generate_insights(
        prompt, analyzer.llm_config
    )

    def to_items(items: List[str], category: str) -> List[InsightItem]:
        return [
            InsightItem(
                content=i,
                priority=InsightPriority.MEDIUM,
                category=category,
                confidence=confidence,
            )
            for i in items
        ]

    output = InsightsOutput(
        summary=llm_result.get("summary", ""),
        top_recommendations=to_items(
            llm_result.get("recommendations", []), "recommendation"
        ),
        risk_areas=to_items(llm_result.get("risks", []), "risk"),
        growth_opportunities=to_items(
            llm_result.get("opportunities", []), "opportunity"
        ),
        data_quality=quality,
        confidence_score=confidence,
    )
    analyzer._store_cache(cache_key, output)
    return output

