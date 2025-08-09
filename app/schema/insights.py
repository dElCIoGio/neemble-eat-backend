from typing import List
from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    total_orders: int = Field(alias="totalOrders")
    cancelled_orders: int = Field(alias="cancelledOrders")
    non_cancelled_orders: int = Field(alias="nonCancelledOrders")
    total_revenue: float = Field(alias="totalRevenue")
    peak_hours: List[int] = Field(default_factory=list, alias="peakHours")
    best_days: List[str] = Field(default_factory=list, alias="bestDays")

    model_config = {"populate_by_name": True}


class PerformanceInsightsResponse(BaseModel):
    insight: str = Field(alias="insight")
    metrics: PerformanceMetrics = Field(alias="metrics")
    restaurant: str = Field(alias="restaurant")
    timeframe_days: int = Field(alias="timeframeDays")

    model_config = {"populate_by_name": True}


class OccupancyMetrics(BaseModel):
    avg_occupancy_rate: float = Field(alias="avgOccupancyRate")
    peak_hours: List[int] = Field(default_factory=list, alias="peakHours")
    underutilized_hours: List[int] = Field(default_factory=list, alias="underutilizedHours")

    model_config = {"populate_by_name": True}


class OccupancyInsightsResponse(BaseModel):
    insight: str = Field(alias="insight")
    metrics: OccupancyMetrics = Field(alias="metrics")
    restaurant: str = Field(alias="restaurant")
    timeframe_days: int = Field(alias="timeframeDays")

    model_config = {"populate_by_name": True}


class SentimentDistribution(BaseModel):
    positive: int = Field(alias="positive")
    negative: int = Field(alias="negative")
    neutral: int = Field(alias="neutral")

    model_config = {"populate_by_name": True}


class SentimentMetrics(BaseModel):
    overall_sentiment: str = Field(alias="overallSentiment")
    sentiment_distribution: SentimentDistribution = Field(alias="sentimentDistribution")
    avg_rating: float = Field(alias="avgRating")

    model_config = {"populate_by_name": True}


class SentimentInsightsResponse(BaseModel):
    insight: str = Field(alias="insight")
    metrics: SentimentMetrics = Field(alias="metrics")
    restaurant: str = Field(alias="restaurant")
    timeframe_days: int = Field(alias="timeframeDays")

    model_config = {"populate_by_name": True}


class ItemStat(BaseModel):
    item: str = Field(alias="item")
    orders: int = Field(alias="orders")
    revenue: float = Field(alias="revenue")

    model_config = {"populate_by_name": True}


class ItemMetrics(BaseModel):
    most_ordered: List[ItemStat] = Field(default_factory=list, alias="mostOrdered")
    least_ordered: List[ItemStat] = Field(default_factory=list, alias="leastOrdered")
    top_revenue: List[ItemStat] = Field(default_factory=list, alias="topRevenue")

    model_config = {"populate_by_name": True}


class ItemInsightsResponse(BaseModel):
    insight: str = Field(alias="insight")
    metrics: ItemMetrics = Field(alias="metrics")
    restaurant: str = Field(alias="restaurant")
    timeframe_days: int = Field(alias="timeframeDays")

    model_config = {"populate_by_name": True}
