# Insights API

These endpoints generate analytical insights for a restaurant using data
already stored in the system. Instead of submitting raw data, provide the
restaurant's identifier and the service will gather orders, table sessions
and reviews automatically. All monetary values are reported in **Kwanza (Kz)**.

Each endpoint accepts an optional query parameter `days` to specify the
timeframe for the analysis (e.g. `?days=7` for the last week). If omitted,
the service analyses data from the previous day.

## Endpoints

### `GET /api/v1/insights/performance/{restaurant_id}`
Returns a narrative analysis of performance trends derived from historical
orders of the specified restaurant.

### `GET /api/v1/insights/occupancy/{restaurant_id}`
Analyzes table sessions to compute occupancy rates and returns a helpful
opinion on table utilization.

### `GET /api/v1/insights/sentiment/{restaurant_id}`
Evaluates customer feedback left in table session reviews and produces an
overall sentiment assessment with guidance.

### `GET /api/v1/insights/full/{restaurant_id}`
Combines order trends, occupancy statistics and review sentiment into a
comprehensive insights report. The response matches the `InsightsOutput`
schema used by the service.

## Example

```http
GET /api/v1/insights/full/64b9...?days=7
```

The response includes a high level summary along with recommendations,
risks, opportunities, a data quality grade and confidence score.

## Response Formats

### Performance
```json
{
  "insight": "string",
  "metrics": {
    "totalOrders": 0,
    "cancelledOrders": 0,
    "nonCancelledOrders": 0,
    "totalRevenue": 0.0,
    "peakHours": [0],
    "bestDays": ["string"]
  },
  "restaurant": "string",
  "timeframeDays": 1
}
```

### Occupancy
```json
{
  "insight": "string",
  "metrics": {
    "avgOccupancyRate": 0.0,
    "peakHours": [0],
    "underutilizedHours": [0]
  },
  "restaurant": "string",
  "timeframeDays": 1
}
```

### Sentiment
```json
{
  "insight": "string",
  "metrics": {
    "overallSentiment": "neutral",
    "sentimentDistribution": {
      "positive": 0,
      "negative": 0,
      "neutral": 0
    },
    "avgRating": 0.0
  },
  "restaurant": "string",
  "timeframeDays": 1
}
```

### Items
```json
{
  "insight": "string",
  "metrics": {
    "mostOrdered": [{"item": "string", "orders": 0, "revenue": 0.0}],
    "leastOrdered": [{"item": "string", "orders": 0, "revenue": 0.0}],
    "topRevenue": [{"item": "string", "orders": 0, "revenue": 0.0}]
  },
  "restaurant": "string",
  "timeframeDays": 1
}
```

### Full
```json
{
  "summary": "string",
  "topRecommendations": [{
    "content": "string",
    "priority": "medium",
    "category": "string",
    "confidence": 0.0,
    "supportingData": {}
  }],
  "riskAreas": [],
  "growthOpportunities": [],
  "dataQuality": "good",
  "confidenceScore": 0.0,
  "analysisMetadata": {
    "orders": {},
    "occupancy": {},
    "reviews": {},
    "restaurant": "string",
    "timeframeDays": 1
  },
  "generatedAt": "2024-01-01T00:00:00",
  "cacheKey": "string"
}
```
