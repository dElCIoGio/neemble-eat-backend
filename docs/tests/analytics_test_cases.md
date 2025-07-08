# Analytics Module - Test Cases and Requirements

This document outlines the basic requirements and a comprehensive list of test cases for the analytics module in this project. The analytics layer is implemented primarily through FastAPI endpoints located at `app/api/v1/endpoints/analytics.py` and the helper functions defined in `app/services/analytics.py`.

## Basic Requirements

1. **Sales Summary Calculations**
   - Retrieve all invoices for the given restaurant and date range and compute overall sales metrics.
   - Calculate percentage growth for each metric compared with the previous equal period.
2. **Invoice Counting**
   - Count invoices created within the specified range for a restaurant.
3. **Order Aggregations**
   - Provide counts for total orders, cancelled orders and the most ordered menu items.
4. **Session Statistics**
   - Calculate active sessions and average session duration based on table session documents.
5. **Recent Trends**
   - Return order counts for the last seven days to show recent activity.
6. **Error Handling**
   - All endpoints should handle missing or invalid query parameters gracefully and return JSON errors with HTTP 400 or 404 status as appropriate.

## Test Cases

### 1. Sales Summary Endpoint `/api/v1/analytics/sales-summary`
- **TC1.1** Call without `fromDate` and `toDate` parameters and verify the endpoint defaults to today's range.
- **TC1.2** Provide a valid date range and confirm the response includes total sales, invoice count, average invoice value, distinct tables and revenue per table.
- **TC1.3** Ensure the response also returns growth rates for each metric compared to the preceding period.
- **TC1.4** Use a range with no invoices and expect all fields in the response to be zero.
- **TC1.5** Supply an invalid date format and expect HTTP 400.

### 2. Invoice Count Endpoint `/api/v1/analytics/invoices`
- **TC2.1** Request with a valid date range and verify the invoice count matches the documents in the database.
- **TC2.2** Omitting the date range should default to the current day.
- **TC2.3** If the restaurant has no invoices in the range, the count should be zero.

### 3. Order Count Endpoint `/api/v1/analytics/orders`
- **TC3.1** Provide a valid range and expect the correct number of orders returned.
- **TC3.2** Missing date parameters should default to today.
- **TC3.3** Invalid restaurant ID should return HTTP 404 or appropriate error.

### 4. Top Items Endpoint `/api/v1/analytics/top-items`
- **TC4.1** Call with valid parameters and confirm the response lists items sorted by quantity.
- **TC4.2** Verify that the `topN` query parameter respects its bounds (1–20) and defaults to 5.
- **TC4.3** If there are no orders in the period, the endpoint should return an empty list.

### 5. Cancelled Orders Endpoint `/api/v1/analytics/cancelled-orders`
- **TC5.1** Valid request should return the count of orders with status `cancelled` in the range.
- **TC5.2** Requests with no cancelled orders should return `0`.

### 6. Cancelled Sessions Endpoint `/api/v1/analytics/cancelled-sessions`
- **TC6.1** Valid request returns the number of sessions marked `cancelled` within the date range.
- **TC6.2** If there are no cancelled sessions, the endpoint returns `0`.

### 7. Session Duration Endpoint `/api/v1/analytics/session-duration`
- **TC7.1** Ensure the average session duration is calculated using closed table sessions from today.
- **TC7.2** If there are no closed sessions, the endpoint should return `0` minutes.

### 8. Active Sessions Endpoint `/api/v1/analytics/active-sessions`
- **TC8.1** When active sessions exist, verify the count matches table sessions with status `active` and at least one order.
- **TC8.2** No active sessions should return count `0`.

### 9. Recent Orders Endpoint `/api/v1/analytics/recent-orders`
- **TC9.1** Should return a list with seven entries representing each of the last seven days.
- **TC9.2** Each entry should include the ISO date string, weekday name and order count for that day.

### 10. General Edge Cases
- **TC10.1** Verify all endpoints require authentication and deny access otherwise.
- **TC10.2** Ensure that invalid restaurant IDs or dates return meaningful errors without exposing internals.
- **TC10.3** Stress test with a large volume of orders and invoices to validate performance and correct aggregation.

These test cases cover the typical and edge scenarios for the analytics workflows and can be implemented using a testing framework such as `pytest` along with HTTP client libraries to simulate requests.
