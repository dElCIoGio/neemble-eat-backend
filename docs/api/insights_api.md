# Insights API

These endpoints generate analytical insights for a restaurant using data
already stored in the system. Instead of submitting raw data, provide the
restaurant's identifier and the service will gather orders, table sessions
and reviews automatically.

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
GET /api/v1/insights/full/64b9...
```

The response includes a high level summary along with recommendations,
risks, opportunities, a data quality grade and confidence score.

