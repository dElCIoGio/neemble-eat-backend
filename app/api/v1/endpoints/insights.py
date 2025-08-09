from collections import defaultdict
from datetime import datetime, timedelta
import json
import re
from typing import List, Union

from fastapi import APIRouter

from app.schema.order import OrderPrepStatus
from app.services.ai import (
    OrderData,
    TableOccupancy,
    CustomerReview,
    RestaurantInsightsAnalyzer,
    InsightsOutput,
    InsightItem,
    InsightPriority,
    AnalysisType,
    LLMConfig,
)
from app.schema.insights import (
    PerformanceMetrics,
    PerformanceInsightsResponse,
    OccupancyMetrics,
    OccupancyInsightsResponse,
    SentimentDistribution,
    SentimentMetrics,
    SentimentInsightsResponse,
    ItemStat,
    ItemMetrics,
    ItemInsightsResponse,
)
from app.models.order import OrderModel
from app.services import table as table_service
from app.services import restaurant as restaurant_service
from app.services.table_session import session_model
from app.utils.time import now_in_luanda, to_luanda_timezone
from app.utils.format import format_number
from app.core.dependencies import get_settings

router = APIRouter()

settings = get_settings()
analyzer = RestaurantInsightsAnalyzer(
    llm_config=LLMConfig(api_key=settings.OPENAI_API_KEY)
)
order_model = OrderModel()


async def _get_order_data(restaurant_id: str, days: int) -> List[OrderData]:
    cutoff = to_luanda_timezone(now_in_luanda()) - timedelta(days=days)
    orders = await order_model.get_by_fields({
        "restaurantId": restaurant_id,
        "createdAt": {
            "$gte": cutoff,
        },
    })
    data: List[OrderData] = [
        OrderData(
            order_id=str(o.id),
            revenue=0 if o.prep_status == "cancelled" else o.total,
            timestamp=to_luanda_timezone(o.order_time),
            items=[o.ordered_item_name] if getattr(o, "ordered_item_name", None) else [o.item_id],
            table_number=o.table_number,
            status=o.prep_status,
        ) for o in orders
    ]

    return data


async def _get_occupancy_data(restaurant_id: str, days: int) -> List[TableOccupancy]:
    tables = await table_service.list_tables_for_restaurant(restaurant_id)
    total_tables = len(tables)
    if total_tables == 0:
        return []

    cutoff = now_in_luanda() - timedelta(days=days)
    sessions = await session_model.get_by_fields({
        "restaurantId": restaurant_id,
        "startTime": {"$gte": cutoff},
    })
    now = to_luanda_timezone(now_in_luanda())
    occ_map: dict[datetime.date, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    try:
        for s in sessions:
            if not s.start_time:
                continue

            start_dt = to_luanda_timezone(s.start_time)
            if start_dt is None:
                continue

            start = start_dt.replace(minute=0, second=0, microsecond=0)
            end_dt = to_luanda_timezone(s.end_time) or now
            end = end_dt.replace(minute=0, second=0, microsecond=0)
            current = start
            while current <= end:
                occ_map[current.date()][current.hour] += 1
                current += timedelta(hours=1)
    except Exception as e:
        print(e)


    data: List[TableOccupancy] = []
    for date, hours in occ_map.items():
        for hour, occupied in hours.items():
            data.append(
                TableOccupancy(
                    date=datetime.combine(date, datetime.min.time()),
                    hour=hour,
                    occupied_tables=occupied,
                    total_tables=total_tables,
                    occupancy_rate=1
                )
            )
    return data


async def _get_review_data(restaurant_id: str, days: int) -> List[CustomerReview]:
    cutoff = now_in_luanda() - timedelta(days=days)
    sessions = await session_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "review": {"$ne": None},
            "startTime": {"$gte": cutoff},
        }
    )
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


@router.get("/performance/{restaurant_id}", response_model=PerformanceInsightsResponse)
async def performance_insights(restaurant_id: str, days: int = 1):
    restaurant = await restaurant_service.get_restaurant(restaurant_id)
    data = await _get_order_data(restaurant_id, days)
    metrics_data = await analyzer.processors[AnalysisType.PERFORMANCE].process(data)
    if "error" in metrics_data:
        return metrics_data
    metrics = PerformanceMetrics(**metrics_data)
    timeframe = "último dia" if days == 1 else f"últimos {days} dias"
    prompt = (
        f"Restaurante: {restaurant.name}\n"
        f"Período analisado: {timeframe}\n"
        "Moeda: Kwanza (Kz)\n"
        f"Total Orders: {metrics.total_orders}\n"
        f"Cancelled Orders: {metrics.cancelled_orders}\n"
        f"Non-cancelled Orders: {metrics.non_cancelled_orders}\n"
        f"Total Revenue (Kz): {format_number(metrics.total_revenue)}\n"
        f"Peak Hours: {', '.join(map(str, metrics.peak_hours)) or 'none'}\n"
        f"Best Days: {', '.join(metrics.best_days) or 'none'}\n"
        "Forneça uma análise detalhada em português de Portugal sobre o desempenho de vendas do restaurante, incluindo o máximo de informações possível."
    )
    llm_result = await analyzer.llm_provider.generate_insights(
        prompt, analyzer.llm_config
    )
    opinion = llm_result.get("summary", "Nenhum insight disponível.")
    return PerformanceInsightsResponse(
        insight=opinion,
        metrics=metrics,
        restaurant=restaurant.name,
        timeframe_days=days,
    )
@router.get("/occupancy/{restaurant_id}", response_model=OccupancyInsightsResponse)
async def occupancy_insights(restaurant_id: str, days: int = 1):
    try:
        restaurant = await restaurant_service.get_restaurant(restaurant_id)
        data = await _get_occupancy_data(restaurant_id, days)
        metrics_data = await analyzer.processors[AnalysisType.OCCUPANCY].process(data)
        if "error" in metrics_data:
            return metrics_data
        metrics = OccupancyMetrics(**metrics_data)
        timeframe = "último dia" if days == 1 else f"últimos {days} dias"
        prompt = (
            f"Restaurante: {restaurant.name}\n"
            f"Período analisado: {timeframe}\n"
            "Moeda: Kwanza (Kz)\n"
            f"Average Occupancy Rate: {metrics.avg_occupancy_rate:.2f}\n"
            f"Peak Hours: {', '.join(map(str, metrics.peak_hours)) or 'none'}\n"
            f"Underutilized Hours: {', '.join(map(str, metrics.underutilized_hours)) or 'none'}\n"
            "Forneça uma análise detalhada em português de Portugal sobre a ocupação das mesas e sugestões para melhorá-la, incluindo o máximo de informações possível."
        )
        llm_result = await analyzer.llm_provider.generate_insights(
            prompt, analyzer.llm_config
        )
        opinion = llm_result.get("summary", "Nenhum insight disponível.")
        return OccupancyInsightsResponse(
            insight=opinion,
            metrics=metrics,
            restaurant=restaurant.name,
            timeframe_days=days,
        )
    except Exception as e:
        print(e)
@router.get("/sentiment/{restaurant_id}", response_model=SentimentInsightsResponse)
async def sentiment_insights(restaurant_id: str, days: int = 1):
    restaurant = await restaurant_service.get_restaurant(restaurant_id)
    data = await _get_review_data(restaurant_id, days)
    metrics_data = await analyzer.processors[AnalysisType.SENTIMENT].process(data)
    if "error" in metrics_data:
        return metrics_data
    dist = SentimentDistribution(**metrics_data.get("sentiment_distribution", {}))
    metrics = SentimentMetrics(
        overall_sentiment=metrics_data.get("overall_sentiment", "neutral"),
        sentiment_distribution=dist,
        avg_rating=metrics_data.get("avg_rating"),
    )
    timeframe = "último dia" if days == 1 else f"últimos {days} dias"
    prompt = (
        f"Restaurante: {restaurant.name}\n"
        f"Período analisado: {timeframe}\n"
        "Moeda: Kwanza (Kz)\n"
        f"Overall Sentiment: {metrics.overall_sentiment}\n"
        f"Positive Reviews: {dist.positive}\n"
        f"Negative Reviews: {dist.negative}\n"
        f"Neutral Reviews: {dist.neutral}\n"
        f"Average Rating: {metrics.avg_rating}\n"
        "Forneça uma análise detalhada em português de Portugal sobre o sentimento dos clientes com sugestões para melhoria, incluindo o máximo de informações possível."
    )
    llm_result = await analyzer.llm_provider.generate_insights(
        prompt, analyzer.llm_config
    )
    opinion = llm_result.get("summary", "Nenhum insight disponível.")
    return SentimentInsightsResponse(
        insight=opinion,
        metrics=metrics,
        restaurant=restaurant.name,
        timeframe_days=days,
    )
@router.get("/items/{restaurant_id}", response_model=ItemInsightsResponse)
async def items_insights(restaurant_id: str, days: int = 1):
    """Return insight on most/least ordered items and revenue generated."""
    restaurant = await restaurant_service.get_restaurant(restaurant_id)
    cutoff = to_luanda_timezone(now_in_luanda()) - timedelta(days=days)
    orders = await order_model.get_by_fields(
        {
            "restaurantId": restaurant_id,
            "createdAt": {"$gte": cutoff},
            "prepStatus": {"$ne": OrderPrepStatus.CANCELLED.value},
        }
    )

    stats: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "revenue": 0.0})
    for o in orders:
        name = getattr(o, "ordered_item_name", None) or getattr(o, "item_id", "unknown")
        revenue = 0 if o.prep_status == "cancelled" else o.total
        qty = getattr(o, "quantity", 1)
        stats[name]["count"] += qty
        stats[name]["revenue"] += revenue

    if not stats:
        return ItemInsightsResponse(
            insight="Nenhum dado disponível.",
            metrics=ItemMetrics(),
            restaurant=restaurant.name,
            timeframe_days=days,
        )

    most_ordered = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)
    least_ordered = sorted(stats.items(), key=lambda x: x[1]["count"])
    top_revenue = sorted(stats.items(), key=lambda x: x[1]["revenue"], reverse=True)

    metrics = ItemMetrics(
        most_ordered=[
            ItemStat(item=name, orders=data["count"], revenue=data["revenue"])
            for name, data in most_ordered[:5]
        ],
        least_ordered=[
            ItemStat(item=name, orders=data["count"], revenue=data["revenue"])
            for name, data in least_ordered[:5]
        ],
        top_revenue=[
            ItemStat(item=name, orders=data["count"], revenue=data["revenue"])
            for name, data in top_revenue[:5]
        ],
    )

    summary_parts = []
    if metrics.most_ordered:
        top = metrics.most_ordered[0]
        summary_parts.append(
            f"O item mais pedido foi {top.item} com {top.orders} pedidos gerando {format_number(top.revenue)} Kz."
        )
    if metrics.top_revenue:
        top_rev = metrics.top_revenue[0]
        if not (metrics.most_ordered and top_rev.item == metrics.most_ordered[0].item):
            summary_parts.append(
                f"O item com maior receita foi {top_rev.item} com {format_number(top_rev.revenue)} Kz a partir de {top_rev.orders} pedidos."
            )
    if metrics.least_ordered:
        low = metrics.least_ordered[0]
        summary_parts.append(
            f"O item menos pedido foi {low.item} com {low.orders} pedidos gerando {format_number(low.revenue)} Kz."
        )

    insight = " ".join(summary_parts) if summary_parts else "Nenhum dado disponível."

    return ItemInsightsResponse(
        insight=insight,
        metrics=metrics,
        restaurant=restaurant.name,
        timeframe_days=days,
    )
@router.get("/full/{restaurant_id}", response_model=InsightsOutput)
async def generate_full_insights(restaurant_id: str, days: int = 1):
    try:
        restaurant = await restaurant_service.get_restaurant(restaurant_id)
        orders = await _get_order_data(restaurant_id, days)
        occupancy = await _get_occupancy_data(restaurant_id, days)
        reviews = await _get_review_data(restaurant_id, days)

        cache_key = analyzer._generate_cache_key(restaurant, orders, occupancy, reviews)
        cached = analyzer._check_cache(cache_key)
        if cached:
            return cached

        trends, occ, sentiment = await analyzer._process_data_sources(orders, occupancy, reviews)
        quality, confidence = analyzer._assess_data_quality(trends, occ, sentiment)

        timeframe = "último dia" if days == 1 else f"últimos {days} dias"
        prompt = (
            f"Restaurante: {restaurant.name}\n"
            f"Período analisado: {timeframe}\n"
            "Moeda: Kwanza (Kz)\n"
            f"Orders: {trends}\n"
            f"Occupancy: {occ}\n"
            f"Reviews: {sentiment}\n"
            "Escreva todas as conclusões em português de Portugal e forneça o máximo de detalhes possível sobre o desempenho do restaurante, incluindo recomendações, riscos e oportunidades."
        )
        llm_result = await analyzer.llm_provider.generate_insights(
            prompt, analyzer.llm_config
        )

        def to_items(items: Union[str, List[str]], category: str) -> List[InsightItem]:
            if isinstance(items, str):
                try:
                    parsed_items = json.loads(items)
                    if isinstance(parsed_items, str):
                        parsed_items = [parsed_items]
                except json.JSONDecodeError:
                    parsed_items = [
                        i.strip(" -•")
                        for i in re.split(r"[\n\r]+", items)
                        if i.strip()
                    ]
            else:
                parsed_items = items

            return [
                InsightItem(
                    content=i,
                    priority=InsightPriority.MEDIUM,
                    category=category,
                    confidence=confidence,
                )
                for i in parsed_items
            ]

        summary = llm_result.get("summary", "Nenhum insight disponível.")

        output = InsightsOutput(
            summary=summary,
            top_recommendations=to_items(
                llm_result.get("recommendations", []), "recommendation"
            ),
            risk_areas=to_items(llm_result.get("risks", []), "risk"),
            growth_opportunities=to_items(
                llm_result.get("opportunities", []), "opportunity"
            ),
            data_quality=quality,
            confidence_score=confidence,
            analysis_metadata={
                "orders": trends,
                "occupancy": occ,
                "reviews": sentiment,
                "restaurant": restaurant.name,
                "timeframeDays": days,
            },
        )
        analyzer._store_cache(cache_key, output)
        return output
    except Exception as e:
        print(e)
