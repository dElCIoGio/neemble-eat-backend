"""
AI-Powered Restaurant Performance Insights for Neemble Eat
Production-ready class-based implementation with caching, configuration, and extensibility
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
import json
import re
import hashlib
from abc import ABC, abstractmethod

import pandas as pd
from pydantic import BaseModel, Field, validator
from beanie import Document
import openai

from app.core.config import Settings
from app.utils.time import now_in_luanda

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class AnalysisType(Enum):
    """Types of analysis available"""
    PERFORMANCE = "performance"
    SENTIMENT = "sentiment"
    OCCUPANCY = "occupancy"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"


class InsightPriority(Enum):
    """Priority levels for insights"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DataQuality(Enum):
    """Data quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters"""
    min_orders_for_trends: int = 10
    min_reviews_for_sentiment: int = 5
    confidence_threshold: float = 0.6
    cache_ttl_minutes: int = 30
    max_recommendations: int = 5
    max_risk_areas: int = 5
    max_opportunities: int = 5
    include_debug_info: bool = False


@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: str = "openai"  # openai, anthropic, azure, mock
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout_seconds: int = 30
    enable_fallback: bool = True


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RestaurantSettings(BaseModel):
    """Restaurant configuration settings"""
    opening_hours: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    max_capacity: Optional[int] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None  # "$", "$$", "$$$", "$$$$"

    @validator('price_range')
    def validate_price_range(cls, v):
        if v and v not in ["$", "$$", "$$$", "$$$$"]:
            raise ValueError("Price range must be $, $$, $$$, or $$$$")
        return v


class RestaurantDocument(Document):
    """Beanie document for restaurant data"""
    name: str
    address: str
    is_active: bool = True
    settings: RestaurantSettings = Field(default_factory=RestaurantSettings)
    order_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_analysis: Optional[datetime] = None

    class Settings:
        name = "restaurants"


class OrderData(BaseModel):
    """Historical order data structure"""
    order_id: str
    revenue: float = Field(gt=0)
    timestamp: datetime
    items: List[str]
    table_number: Optional[int] = None
    customer_count: Optional[int] = Field(ge=1, default=1)
    order_type: Optional[str] = "dine_in"  # dine_in, takeout, delivery


class TableOccupancy(BaseModel):
    """Daily table occupancy data"""
    date: datetime
    hour: int = Field(ge=0, le=23)
    occupied_tables: int = Field(ge=0)
    total_tables: int = Field(gt=0)
    occupancy_rate: float = Field(ge=0, le=1)

    @validator('occupancy_rate', always=True)
    def calculate_occupancy_rate(cls, v, values):
        if 'occupied_tables' in values and 'total_tables' in values:
            return round(values['occupied_tables'] / values['total_tables'], 3)
        return v


class CustomerReview(BaseModel):
    """Customer review data"""
    review_id: str
    text: str
    rating: Optional[int] = Field(ge=1, le=5, default=None)
    timestamp: datetime
    verified: bool = False
    source: str = "internal"  # internal, google, yelp, etc.


class InsightItem(BaseModel):
    """Individual insight item with metadata"""
    content: str
    priority: InsightPriority
    category: str
    confidence: float = Field(ge=0, le=1)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)


class InsightsOutput(BaseModel):
    """AI-generated restaurant insights output"""
    summary: str
    top_recommendations: List[InsightItem]
    risk_areas: List[InsightItem]
    growth_opportunities: List[InsightItem]
    data_quality: DataQuality
    confidence_score: float = Field(ge=0, le=1, default=0.8)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cache_key: Optional[str] = None


# ============================================================================
# ABSTRACT BASE CLASSES
# ============================================================================

class DataProcessor(ABC):
    """Abstract base class for data processors"""

    @abstractmethod
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process input data and return analysis results"""
        pass

    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """Validate input data quality"""
        pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate_insights(self, prompt: str, config: LLMConfig) -> Dict[str, Any]:
        """Generate insights using LLM"""
        pass


# ============================================================================
# DATA PROCESSORS
# ============================================================================

class TimeSeriesProcessor(DataProcessor):
    """Processes time-based order and revenue data"""

    def validate_data(self, data: List[OrderData]) -> bool:
        return bool(data) and len(data) >= 3

    async def process(self, data: List[OrderData]) -> Dict[str, Any]:
        """Extract comprehensive time-based trends"""
        if not self.validate_data(data):
            return {"error": "Insufficient order data for analysis"}

        try:
            df = pd.DataFrame([
                {
                    'timestamp': order.timestamp,
                    'revenue': order.revenue,
                    'hour': order.timestamp.hour,
                    'day_of_week': order.timestamp.strftime('%A'),
                    'date': order.timestamp.date(),
                    'items_count': len(order.items),
                    'customer_count': order.customer_count or 1,
                    'order_type': order.order_type
                }
                for order in data
            ])

            # Advanced time analysis
            hourly_stats = df.groupby('hour').agg({
                'revenue': ['sum', 'count', 'mean'],
                'customer_count': 'mean'
            }).round(2)

            daily_stats = df.groupby('day_of_week').agg({
                'revenue': ['sum', 'count', 'mean'],
                'customer_count': 'mean'
            }).round(2)

            # Revenue velocity (recent vs historical)
            recent_cutoff = now_in_luanda() - timedelta(days=14)
            recent_df = df[df['timestamp'] >= recent_cutoff]
            historical_df = df[df['timestamp'] < recent_cutoff]

            # Order type analysis
            order_type_analysis = df.groupby('order_type')['revenue'].agg(['sum', 'count', 'mean']).round(2)

            return {
                'total_orders': len(df),
                'total_revenue': round(df['revenue'].sum(), 2),
                'avg_order_value': round(df['revenue'].mean(), 2),
                'avg_customer_count': round(df['customer_count'].mean(), 1),
                'peak_hours': hourly_stats['revenue']['sum'].nlargest(3).index.tolist(),
                'slow_hours': hourly_stats['revenue']['sum'].nsmallest(3).index.tolist(),
                'best_days': daily_stats['revenue']['sum'].nlargest(3).index.tolist(),
                'worst_days': daily_stats['revenue']['sum'].nsmallest(2).index.tolist(),
                'revenue_velocity': 'increasing' if len(recent_df) > 0 and recent_df['revenue'].mean() > historical_df[
                    'revenue'].mean() else 'stable',
                'order_type_breakdown': order_type_analysis.to_dict() if not order_type_analysis.empty else {},
                'data_span_days': (df['timestamp'].max() - df['timestamp'].min()).days,
                'consistency_score': round(1 - (df['revenue'].std() / df['revenue'].mean()), 2) if df[
                                                                                                       'revenue'].mean() > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error in time series processing: {e}")
            return {"error": f"Time series analysis failed: {str(e)}"}


class OccupancyProcessor(DataProcessor):
    """Processes table occupancy and capacity utilization data"""

    def validate_data(self, data: List[TableOccupancy]) -> bool:
        return bool(data) and len(data) >= 5

    async def process(self, data: List[TableOccupancy]) -> Dict[str, Any]:
        """Analyze occupancy patterns and efficiency"""
        if not self.validate_data(data):
            return {"error": "Insufficient occupancy data"}

        try:
            df = pd.DataFrame([
                {
                    'date': occ.date.date(),
                    'hour': occ.hour,
                    'occupancy_rate': occ.occupancy_rate,
                    'occupied_tables': occ.occupied_tables,
                    'total_tables': occ.total_tables,
                    'day_of_week': occ.date.strftime('%A')
                }
                for occ in data
            ])

            # Advanced occupancy analysis
            hourly_occupancy = df.groupby('hour')['occupancy_rate'].agg(['mean', 'max', 'std']).round(3)
            daily_occupancy = df.groupby('day_of_week')['occupancy_rate'].mean().round(3)

            # Efficiency metrics
            avg_occupancy = df['occupancy_rate'].mean()
            peak_utilization = df['occupancy_rate'].max()
            occupancy_volatility = df['occupancy_rate'].std()

            # Capacity optimization opportunities
            underutilized_hours = hourly_occupancy[hourly_occupancy['mean'] < 0.5].index.tolist()
            over_capacity_hours = hourly_occupancy[hourly_occupancy['mean'] > 0.9].index.tolist()

            return {
                'avg_occupancy_rate': round(avg_occupancy, 3),
                'peak_occupancy_rate': round(peak_utilization, 3),
                'occupancy_volatility': round(occupancy_volatility, 3),
                'peak_hours': hourly_occupancy['mean'].nlargest(3).index.tolist(),
                'low_hours': hourly_occupancy['mean'].nsmallest(3).index.tolist(),
                'underutilized_hours': underutilized_hours,
                'over_capacity_hours': over_capacity_hours,
                'best_days': daily_occupancy.nlargest(3).index.tolist(),
                'utilization_efficiency': self._calculate_efficiency_grade(avg_occupancy),
                'capacity_optimization_score': round(1 - occupancy_volatility, 2),
                'revenue_potential': self._estimate_revenue_potential(df)
            }

        except Exception as e:
            logger.error(f"Error in occupancy processing: {e}")
            return {"error": f"Occupancy analysis failed: {str(e)}"}

    def _calculate_efficiency_grade(self, avg_occupancy: float) -> str:
        """Calculate efficiency grade based on occupancy"""
        if avg_occupancy >= 0.8:
            return "excellent"
        elif avg_occupancy >= 0.6:
            return "good"
        elif avg_occupancy >= 0.4:
            return "fair"
        else:
            return "poor"

    def _estimate_revenue_potential(self, df: pd.DataFrame) -> Dict[str, float]:
        """Estimate revenue potential from occupancy optimization"""
        current_utilization = df['occupancy_rate'].mean()
        optimal_utilization = 0.85  # Target occupancy rate

        if current_utilization < optimal_utilization:
            potential_increase = (optimal_utilization - current_utilization) / current_utilization
            return {
                'current_utilization': round(current_utilization, 3),
                'optimal_utilization': optimal_utilization,
                'potential_increase_percent': round(potential_increase * 100, 1)
            }

        return {'current_utilization': round(current_utilization, 3), 'status': 'optimized'}


class SentimentProcessor(DataProcessor):
    """Processes customer reviews and feedback"""

    def validate_data(self, data: List[CustomerReview]) -> bool:
        return bool(data) and len(data) >= 3

    async def process(self, data: List[CustomerReview]) -> Dict[str, Any]:
        """Advanced sentiment analysis with theme extraction"""
        if not self.validate_data(data):
            return {"error": "Insufficient review data"}

        try:
            # Enhanced keyword dictionaries
            sentiment_keywords = {
                'positive': ['excellent', 'amazing', 'fantastic', 'wonderful', 'great', 'perfect',
                             'delicious', 'outstanding', 'love', 'best', 'incredible', 'awesome'],
                'negative': ['terrible', 'awful', 'horrible', 'disgusting', 'worst', 'hate',
                             'bad', 'poor', 'slow', 'rude', 'cold', 'disappointing', 'overpriced']
            }

            theme_keywords = {
                'food_quality': ['food', 'meal', 'dish', 'taste', 'flavor', 'delicious', 'fresh', 'quality'],
                'service': ['service', 'staff', 'waiter', 'waitress', 'server', 'friendly', 'attentive'],
                'atmosphere': ['atmosphere', 'ambiance', 'decor', 'music', 'vibe', 'environment'],
                'pricing': ['price', 'expensive', 'cheap', 'value', 'cost', 'worth', 'affordable'],
                'speed': ['fast', 'slow', 'quick', 'wait', 'time', 'prompt', 'delay'],
                'cleanliness': ['clean', 'dirty', 'hygiene', 'sanitary', 'tidy', 'mess']
            }

            sentiments = []
            themes = defaultdict(list)
            ratings_data = []

            for review in data:
                text_lower = review.text.lower()

                # Advanced sentiment scoring
                positive_score = sum(2 if word in text_lower else 0 for word in sentiment_keywords['positive'])
                negative_score = sum(2 if word in text_lower else 0 for word in sentiment_keywords['negative'])

                # Consider ratings if available
                if review.rating:
                    ratings_data.append(review.rating)
                    if review.rating >= 4:
                        positive_score += 3
                    elif review.rating <= 2:
                        negative_score += 3

                # Determine sentiment
                if positive_score > negative_score + 1:
                    sentiment = 'positive'
                elif negative_score > positive_score + 1:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'

                sentiments.append(sentiment)

                # Extract themes with sentiment context
                for theme, keywords in theme_keywords.items():
                    theme_mentions = sum(1 for word in keywords if word in text_lower)
                    if theme_mentions > 0:
                        themes[theme].append({
                            'sentiment': sentiment,
                            'mentions': theme_mentions,
                            'review_id': review.review_id
                        })

            # Calculate comprehensive metrics
            sentiment_counts = Counter(sentiments)
            total_reviews = len(data)

            # Theme analysis with sentiment breakdown
            theme_analysis = {}
            for theme, mentions in themes.items():
                theme_sentiments = Counter(mention['sentiment'] for mention in mentions)
                theme_analysis[theme] = {
                    'total_mentions': len(mentions),
                    'positive_ratio': theme_sentiments['positive'] / len(mentions) if mentions else 0,
                    'negative_ratio': theme_sentiments['negative'] / len(mentions) if mentions else 0,
                    'sentiment_score': (theme_sentiments['positive'] - theme_sentiments['negative']) / len(
                        mentions) if mentions else 0
                }

            return {
                'total_reviews': total_reviews,
                'sentiment_distribution': {
                    'positive': sentiment_counts['positive'],
                    'negative': sentiment_counts['negative'],
                    'neutral': sentiment_counts['neutral']
                },
                'sentiment_ratios': {
                    'positive': round(sentiment_counts['positive'] / total_reviews, 3),
                    'negative': round(sentiment_counts['negative'] / total_reviews, 3),
                    'neutral': round(sentiment_counts['neutral'] / total_reviews, 3)
                },
                'overall_sentiment': max(sentiment_counts, key=sentiment_counts.get),
                'sentiment_score': round((sentiment_counts['positive'] - sentiment_counts['negative']) / total_reviews,
                                         3),
                'theme_analysis': theme_analysis,
                'avg_rating': round(sum(ratings_data) / len(ratings_data), 2) if ratings_data else None,
                'rating_distribution': Counter(ratings_data) if ratings_data else None,
                'review_quality': self._assess_review_quality(data)
            }

        except Exception as e:
            logger.error(f"Error in sentiment processing: {e}")
            return {"error": f"Sentiment analysis failed: {str(e)}"}

    def _assess_review_quality(self, reviews: List[CustomerReview]) -> Dict[str, Any]:
        """Assess the quality and reliability of review data"""
        total_reviews = len(reviews)
        verified_count = sum(1 for r in reviews if r.verified)
        avg_length = sum(len(r.text.split()) for r in reviews) / total_reviews

        return {
            'verified_ratio': round(verified_count / total_reviews, 3),
            'avg_review_length': round(avg_length, 1),
            'quality_score': round((verified_count / total_reviews) * 0.6 + min(avg_length / 20, 1) * 0.4, 3)
        }


# ============================================================================
# LLM PROVIDERS
# ============================================================================

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and development"""

    async def generate_insights(self, prompt: str, config: LLMConfig) -> Dict[str, Any]:
        """Generate mock insights based on data patterns"""
        await asyncio.sleep(0.1)  # Simulate API delay

        # Parse key metrics from prompt for intelligent mock responses
        revenue_match = re.search(r'Total Revenue: \$?([\d,]+\.?\d*)', prompt)
        occupancy_match = re.search(r'Average Occupancy Rate: ([\d.]+)', prompt)
        sentiment_match = re.search(r'Overall Sentiment: (\w+)', prompt)

        revenue = float(revenue_match.group(1).replace(',', '')) if revenue_match else 0
        occupancy = float(occupancy_match.group(1)) if occupancy_match else 0
        sentiment = sentiment_match.group(1).lower() if sentiment_match else 'neutral'

        return {
            "summary": self._generate_summary(revenue, occupancy, sentiment),
            "recommendations": self._generate_recommendations(revenue, occupancy, sentiment),
            "risks": self._generate_risks(revenue, occupancy, sentiment),
            "opportunities": self._generate_opportunities(revenue, occupancy, sentiment)
        }

    def _generate_summary(self, revenue: float, occupancy: float, sentiment: str) -> str:
        performance_level = "strong" if revenue > 10000 else "moderate" if revenue > 5000 else "developing"
        occupancy_status = "excellent" if occupancy > 0.8 else "good" if occupancy > 0.6 else "needs improvement"

        return (f"Restaurant demonstrates {performance_level} financial performance with "
                f"{occupancy_status} space utilization and {sentiment} customer sentiment. "
                f"Key focus areas identified for operational optimization and growth.")

    def _generate_recommendations(self, revenue: float, occupancy: float, sentiment: str) -> List[str]:
        recommendations = []

        if occupancy < 0.6:
            recommendations.append("Implement dynamic pricing and promotional campaigns during low-occupancy periods")
        if sentiment == 'negative':
            recommendations.append(
                "Prioritize staff training and service quality improvements based on customer feedback")
        if revenue < 8000:
            recommendations.append("Explore menu optimization and upselling strategies to increase average order value")

        recommendations.extend([
            "Deploy data-driven staff scheduling to match peak demand periods",
            "Consider implementing a customer loyalty program to improve retention"
        ])

        return recommendations[:5]

    def _generate_risks(self, revenue: float, occupancy: float, sentiment: str) -> List[str]:
        risks = []

        if occupancy < 0.4:
            risks.append("Critically low occupancy rates indicate potential revenue sustainability issues")
        if sentiment == 'negative':
            risks.append("Declining customer satisfaction may impact long-term reputation and retention")
        if revenue < 3000:
            risks.append("Current revenue levels may not support operational sustainability")

        return risks

    def _generate_opportunities(self, revenue: float, occupancy: float, sentiment: str) -> List[str]:
        opportunities = [
            "Optimize table turnover rates during peak hours to maximize revenue potential",
            "Develop targeted marketing campaigns for underperforming time periods",
            "Implement technology solutions for improved operational efficiency"
        ]

        if occupancy > 0.8:
            opportunities.append("Consider expansion or extended hours given high demand utilization")
        if sentiment == 'positive':
            opportunities.append("Leverage positive customer sentiment for referral and review programs")

        return opportunities


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for production use"""

    async def generate_insights(self, prompt: str, config: LLMConfig) -> Dict[str, Any]:
        """Generate insights using OpenAI API"""
        try:
            if not config.api_key:
                settings = Settings()
                config.api_key = settings.OPENAI_API_KEY

            print(f"API Key: {config.api_key!r}")

            openai.api_key = config.api_key

            client = openai.AsyncOpenAI(api_key=config.api_key)

            response = await client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert restaurant business consultant providing data-driven insights. Always respond with valid JSON containing summary, recommendations, risks, and opportunities keys. Provide your answers in Portuguese (from Portugal)"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                timeout=config.timeout_seconds
            )

            content = response.choices[0].message.content.strip()

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing
                return {
                    "summary": content,
                    "recommendations": [],
                    "risks": [],
                    "opportunities": []
                }

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            if config.enable_fallback:
                mock_provider = MockLLMProvider()
                return await mock_provider.generate_insights(prompt, config)
            raise


# ============================================================================
# MAIN INSIGHTS ANALYZER CLASS
# ============================================================================

class RestaurantInsightsAnalyzer:
    """
    Comprehensive restaurant performance insights analyzer

    Features:
    - Multi-source data processing
    - Configurable analysis parameters
    - Caching for performance
    - Multiple LLM provider support
    - Extensible processor architecture
    """

    def __init__(
            self,
            analysis_config: Optional[AnalysisConfig] = None,
            llm_config: Optional[LLMConfig] = None
    ):
        self.analysis_config = analysis_config or AnalysisConfig()
        self.llm_config = llm_config or LLMConfig()

        # Initialize processors
        self.processors = {
            AnalysisType.PERFORMANCE: TimeSeriesProcessor(),
            AnalysisType.OCCUPANCY: OccupancyProcessor(),
            AnalysisType.SENTIMENT: SentimentProcessor()
        }

        # Initialize LLM provider
        self.llm_provider = self._initialize_llm_provider()

        # Cache for storing recent analyses
        self._cache: Dict[str, Tuple[InsightsOutput, datetime]] = {}

        logger.info(f"RestaurantInsightsAnalyzer initialized with {self.llm_config.provider} provider")

    def _initialize_llm_provider(self) -> LLMProvider:
        """Initialize the appropriate LLM provider"""
        if self.llm_config.provider.lower() == "openai":
            return OpenAIProvider()
        elif self.llm_config.provider.lower() == "mock":
            return MockLLMProvider()
        else:
            logger.warning(f"Unknown LLM provider: {self.llm_config.provider}, falling back to mock")
            return MockLLMProvider()

    def _generate_cache_key(
            self,
            restaurant: RestaurantDocument,
            order_data: Optional[List[OrderData]],
            table_occupancy: Optional[List[TableOccupancy]],
            customer_reviews: Optional[List[CustomerReview]]
    ) -> str:
        """Generate cache key for the analysis"""
        key_components = [
            str(restaurant.id) if hasattr(restaurant, 'id') else restaurant.name,
            str(len(order_data or [])),
            str(len(table_occupancy or [])),
            str(len(customer_reviews or [])),
            str(self.analysis_config.__dict__),
            str(self.llm_config.model)
        ]
        return hashlib.md5("|".join(key_components).encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[InsightsOutput]:
        """Check if valid cached result exists"""
        if cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            age_minutes = (datetime.utcnow() - cached_time).total_seconds() / 60

            if age_minutes < self.analysis_config.cache_ttl_minutes:
                logger.info(f"Using cached result (age: {age_minutes:.1f} minutes)")
                return cached_result
            else:
                # Remove expired cache entry
                del self._cache[cache_key]

        return None

    def _store_cache(self, cache_key: str, result: InsightsOutput) -> None:
        """Store result in cache"""
        self._cache[cache_key] = (result, datetime.utcnow())
        result.cache_key = cache_key

    async def _process_data_sources(
            self,
            order_data: Optional[List[OrderData]],
            table_occupancy: Optional[List[TableOccupancy]],
            customer_reviews: Optional[List[CustomerReview]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Process all data sources concurrently"""

        tasks = []

        # Process time series data
        if order_data:
            tasks.append(self.processors[AnalysisType.PERFORMANCE].process(order_data))
        else:
            tasks.append(asyncio.create_task(asyncio.coroutine(lambda: {"error": "No order data"})()))

        # Process occupancy data
        if table_occupancy:
            tasks.append(self.processors[AnalysisType.OCCUPANCY].process(table_occupancy))
        else:
            tasks.append(asyncio.create_task(asyncio.coroutine(lambda: {"error": "No occupancy data"})()))

        # Process sentiment data
        if customer_reviews:
            tasks.append(self.processors[AnalysisType.SENTIMENT].process(customer_reviews))
        else:
            tasks.append(asyncio.create_task(asyncio.coroutine(lambda: {"error": "No review data"})()))

        return await asyncio.gather(*tasks)

    def _assess_data_quality(
            self,
            trends_data: Dict[str, Any],
            occupancy_data: Dict[str, Any],
            sentiment_data: Dict[str, Any]
    ) -> Tuple[DataQuality, float]:
        """Assess overall data quality and confidence"""
        quality_score = 0.0
        data_sources = 0

        # Evaluate each data source
        if not trends_data.get('error'):
            quality_score += 0.4
            data_sources += 1
            # Bonus for comprehensive order data
            if trends_data.get('total_orders', 0) > self.analysis_config.min_orders_for_trends:
                quality_score += 0.1

        if not occupancy_data.get('error'):
            quality_score += 0.3
            data_sources += 1

        if not sentiment_data.get('error'):
            quality_score += 0.3
            data_sources += 1
            # Bonus for review quality
            if sentiment_data.get('review_quality', {}).get('quality_score', 0) > 0.7:
                quality_score += 0.1

        # Determine quality grade
        if quality_score >= 0.8:
            quality = DataQuality.EXCELLENT
        elif quality_score >= 0.6:
            quality = DataQuality.GOOD
        elif quality_score >= 0.4:
            quality = DataQuality.FAIR
        else:
            quality = DataQuality.POOR

        confidence = min(quality_score, 1.0)

        return quality, confidence