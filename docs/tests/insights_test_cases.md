# Insights Module - Test Cases and Requirements

This document outlines the basic requirements and an extensive list of test cases for the insights module. The AI insights functionality is exposed through FastAPI endpoints defined in `app/api/v1/endpoints/insights.py` and the underlying processing logic in `app/services/ai.py`.

## Basic Requirements

1. **Data Processing**
   - Performance, occupancy and sentiment analyses must validate data volume (e.g. minimum numbers of orders or reviews) before processing.
   - Support processing of orders, table occupancy and customer reviews, either individually or combined for full insights.
2. **Full Insights Generation**
   - Combine results from all processors, assess data quality, and generate a summary with recommendations, risk areas and growth opportunities using an LLM provider.
   - Cache analysis results using a hash of input parameters to avoid repeated computation.
3. **LLM Providers and Fallback**
   - Use the configured LLM provider (OpenAI or mock). On failure or when configured as `mock`, results should still be generated without raising errors.
4. **Authentication and Error Handling**
   - All endpoints require authentication via middleware. Invalid payloads should return HTTP 422 and data processing errors should return a JSON error field.

## Test Cases

### 1. Performance Insights Endpoint `/api/v1/insights/performance`
- **TC1.1** Valid list of `OrderData` objects returns a helpful narrative summarising performance.
- **TC1.2** Fewer than three orders returns `{ "error": "Insufficient order data for analysis" }`.
- **TC1.3** Invalid order fields (e.g. negative revenue) return HTTP 422.

### 2. Occupancy Insights Endpoint `/api/v1/insights/occupancy`
- **TC2.1** Valid list of `TableOccupancy` objects returns utilization opinions.
- **TC2.2** Fewer than five occupancy records returns `{ "error": "Insufficient occupancy data" }`.
- **TC2.3** Invalid occupancy fields (e.g. hour out of range) return HTTP 422.

### 3. Sentiment Insights Endpoint `/api/v1/insights/sentiment`
- **TC3.1** Valid list of `CustomerReview` objects returns overall sentiment analysis with narrative.
- **TC3.2** Fewer than three reviews returns `{ "error": "Insufficient review data" }`.
- **TC3.3** Invalid review fields (e.g. rating > 5) return HTTP 422.

### 4. Full Insights Endpoint `/api/v1/insights/full`
- **TC4.1** Providing all three data sources produces an `InsightsOutput` with summary, recommendations, risks and opportunities.
- **TC4.2** Supplying only one or two data sources still produces an output, with missing analyses reported as errors in the result.
- **TC4.3** Verify that cached results are reused when the same restaurant and data are submitted again within the TTL.
- **TC4.4** After cache expiry, a new analysis is generated and the cache is updated.
- **TC4.5** Simulate LLM provider failure and confirm the analyzer falls back to the mock provider when `enable_fallback` is true.

### 5. Data Quality Assessment
- **TC5.1** High-quality data from all sources yields `DataQuality.EXCELLENT` and a confidence score close to 1.0.
- **TC5.2** Missing or error-filled sources lower the quality grade accordingly, reaching `DataQuality.POOR` when all sources fail.

### 6. Authentication and Security
- **TC6.1** Accessing any insights endpoint without valid authentication returns HTTP 401 via the middleware.
- **TC6.2** Ensure responses do not expose internal errors or stack traces when processing fails.

### 7. Edge Cases
- **TC7.1** Extremely large datasets are processed without timeouts and return meaningful metrics.
- **TC7.2** Invalid enum values for `order_type` or negative numbers for counts raise validation errors.
- **TC7.3** Mixed valid and invalid data entries result in overall validation failure.

These test cases cover common scenarios and edge conditions for the insights workflow. They can be implemented using a testing framework such as `pytest` alongside HTTP client utilities to simulate authenticated requests and verify caching behaviour.
