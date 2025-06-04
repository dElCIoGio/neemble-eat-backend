from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai import (
    OrderData,
    TableOccupancy,
    CustomerReview,
    RestaurantInsightsAnalyzer,
    InsightsOutput,
    InsightItem,
    InsightPriority,
    AnalysisType,
    RestaurantDocument,
)

router = APIRouter()

analyzer = RestaurantInsightsAnalyzer()


class FullInsightsRequest(BaseModel):
    restaurant: RestaurantDocument
    orders: Optional[List[OrderData]] = None
    occupancy: Optional[List[TableOccupancy]] = None
    reviews: Optional[List[CustomerReview]] = None


@router.post("/performance")
async def performance_insights(data: List[OrderData]):
    return await analyzer.processors[AnalysisType.PERFORMANCE].process(data)


@router.post("/occupancy")
async def occupancy_insights(data: List[TableOccupancy]):
    return await analyzer.processors[AnalysisType.OCCUPANCY].process(data)


@router.post("/sentiment")
async def sentiment_insights(data: List[CustomerReview]):
    return await analyzer.processors[AnalysisType.SENTIMENT].process(data)


@router.post("/full", response_model=InsightsOutput)
async def generate_full_insights(req: FullInsightsRequest):
    trends, occ, sentiment = await analyzer._process_data_sources(
        req.orders, req.occupancy, req.reviews
    )
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

    return InsightsOutput(
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
