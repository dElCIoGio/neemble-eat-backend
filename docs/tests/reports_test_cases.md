# Sales Reports Endpoint Test Cases

This document lists suggested test scenarios for the `/api/v1/reports/sales/paginate` endpoint.

### Basic Behaviour
- **TC1.1** Provide a valid `restaurantId`, `fromDate` and `toDate` and expect a paginated list of `SalesReport` items ordered by day.
- **TC1.2** Verify that `limit` restricts the number of returned items and `nextCursor` is provided when more data is available.
- **TC1.3** Using the returned `nextCursor` should fetch the next page of results.

### Edge Cases
- **TC2.1** If no invoices exist for the period, the endpoint should return an empty list with `totalCount` set to `0`.
- **TC2.2** Supplying an invalid cursor should default to the first page.
- **TC2.3** Invalid restaurant IDs or malformed dates should return HTTP 400 errors.
