# Table Sessions Module - Test Cases and Requirements

This document outlines the basic requirements and comprehensive test cases for the table sessions module. Table session functionality is implemented primarily in `app/services/table_session.py` with corresponding API endpoints defined in `app/api/v1/endpoints/table_sessions.py`.

## Basic Requirements

1. **Session Creation and Linking**
   - A new session should be created for a table when it is first added or when an order is placed without an active session.
   - The created session must be linked to the table's `currentSessionId` field.
2. **Active Session Retrieval**
   - The system must provide endpoints to retrieve the active session by table ID or by restaurant ID and table number.
   - Retrieving by restaurant ID and table number should create a session when none exists.
3. **Order Tracking**
   - Orders added to a session must be stored in the `orders` list and broadcast via websockets.
4. **Closing and Cancelling Sessions**
   - Closing a session should mark it `closed`, set `endTime`, generate an invoice when appropriate and create the next active session for the table.
   - Cancelling a session should mark it `cancelled` only when all orders are cancelled and also create the next session.
5. **Listing and Deletion**
   - Sessions can be listed per table and removed when necessary (e.g. when deleting a table).
6. **Error Handling**
   - Invalid IDs or attempts to operate on a non‑active session must return an error without modifying data.
  
## Test Cases

### 1. Get Active Session by Table Number `/api/v1/sessions/active/{restaurant_id}/{table_number}`
- **TC1.1** Existing active session returns the session document.
- **TC1.2** When no session exists, a new one is created and returned.
- **TC1.3** Invalid restaurant or table number returns HTTP 404.

### 2. Get Active Session by Table ID `/api/v1/sessions/active/{table_id}`
- **TC2.1** Valid table ID with an active session returns that session.
- **TC2.2** If no active session exists, the endpoint returns HTTP 404.
- **TC2.3** Malformed or unknown table ID returns HTTP 404.

### 3. List Sessions for Table `/api/v1/sessions/table/{table_id}`
- **TC3.1** Table with existing sessions returns them as a list.
- **TC3.2** Table with no sessions returns an empty list.
- **TC3.3** Invalid table ID yields an empty list.

### 4. List Today's Sessions With Orders `/api/v1/sessions/table/{table_id}/today`
- **TC4.1** Returns sessions from midnight to now that have at least one order.
- **TC4.2** Sessions without orders are omitted from the results.
- **TC4.3** Invalid table ID returns an empty list.

### 5. List Active Sessions for Restaurant `/api/v1/sessions/restaurant/{restaurant_id}/active`
- **TC5.1** Returns a list of sessions with status `active` for the restaurant.
- **TC5.2** If no tables have active sessions, the endpoint returns an empty list.
- **TC5.3** Invalid restaurant ID results in an empty list.

### 6. Close Session `/api/v1/sessions/{session_id}/close`
- **TC6.1** Closing an active session with valid orders generates an invoice, sets the status to `closed` and creates a new session.
- **TC6.2** Closing a session whose orders are all cancelled ends the session without creating an invoice and still creates a new session.
- **TC6.3** Attempting to close a non‑existent or non‑active session returns HTTP 400.

### 7. Cancel Session `/api/v1/sessions/{session_id}/cancel`
- **TC7.1** Cancelling an active session where all orders are already cancelled marks it `cancelled` and starts a new session.
- **TC7.2** Cancelling with any non‑cancelled order returns HTTP 400.
- **TC7.3** Non‑existent or inactive session returns HTTP 400.

### 8. Mark Session Paid `/api/v1/sessions/{session_id}/paid`
- **TC8.1** Creates a new invoice marked `paid`, updates the session status and sets the `endTime`.
- **TC8.2** Unknown session IDs return HTTP 404 without modifying data.

### 9. Mark Session Needs Bill `/api/v1/sessions/{session_id}/needs-bill`
- **TC9.1** Updates the session status to `needs bill`.
- **TC9.2** Unknown session IDs return HTTP 404.
### 10. Cancel Checkout `/api/v1/sessions/{session_id}/cancel-checkout`
- **TC10.1** Reverts the session status back to `active` when currently `needs bill`.
- **TC10.2** Unknown session IDs return HTTP 404.


### 11. Add Order to Session (Service)
- **TC11.1** Adding a new order ID appends it to the session and broadcasts the update.
- **TC11.2** Adding an order that already exists leaves the list unchanged.
- **TC11.3** Providing an unknown session ID returns `None`.

### 12. Delete Session (Service)
- **TC12.1** Deleting an existing session returns `True`.
- **TC12.2** Deleting a non‑existent session returns `False`.

### 13. Clean Table `/api/v1/tables/{table_id}/clean`
- **TC13.1** Cancels all orders for the active session and marks the session `cancelled`.
- **TC13.2** A new empty session is created and linked to the table.
- **TC13.3** Invalid table IDs return HTTP 404 without modifying data.

### 14. Delete Unlinked Sessions `/api/v1/sessions/restaurant/{restaurant_id}/cleanup`
- **TC14.1** Returns the number of sessions removed that were not linked to any table.
- **TC14.2** When all sessions are linked, the endpoint returns `0`.
- **TC14.3** Unknown restaurant IDs result in `0` deletions.

### 15. General Edge Cases
- **TC15.1** Ensure all endpoints require authentication where applicable.
- **TC15.2** Stress test by rapidly opening and closing sessions to verify that invoices and new sessions are created correctly each time.
- **TC15.3** Validate websocket broadcasts for order additions and session closures reach all connected clients.

### 16. Request Assistance `/api/v1/sessions/{session_id}/request-assistance`
- **TC16.1** Marks the session as needing assistance.
- **TC16.2** Unknown session IDs return HTTP 404.

### 17. Cancel Assistance `/api/v1/sessions/{session_id}/cancel-assistance`
- **TC17.1** Clears the assistance flag for the session.
- **TC17.2** Unknown session IDs return HTTP 404.

These test cases cover typical and edge scenarios for the table session workflow and can be implemented using a testing framework such as `pytest` along with FastAPI's test client to simulate requests.
