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

### 4. Close Session `/api/v1/sessions/{session_id}/close`
- **TC4.1** Closing an active session with valid orders generates an invoice, sets the status to `closed` and creates a new session.
- **TC4.2** Closing a session whose orders are all cancelled ends the session without creating an invoice and still creates a new session.
- **TC4.3** Attempting to close a non‑existent or non‑active session returns HTTP 400.

### 5. Cancel Session `/api/v1/sessions/{session_id}/cancel`
- **TC5.1** Cancelling an active session where all orders are already cancelled marks it `cancelled` and starts a new session.
- **TC5.2** Cancelling with any non‑cancelled order returns HTTP 400.
- **TC5.3** Non‑existent or inactive session returns HTTP 400.

### 6. Add Order to Session (Service)
- **TC6.1** Adding a new order ID appends it to the session and broadcasts the update.
- **TC6.2** Adding an order that already exists leaves the list unchanged.
- **TC6.3** Providing an unknown session ID returns `None`.

### 7. Delete Session (Service)
- **TC7.1** Deleting an existing session returns `True`.
- **TC7.2** Deleting a non‑existent session returns `False`.

### 8. General Edge Cases
- **TC8.1** Ensure all endpoints require authentication where applicable.
- **TC8.2** Stress test by rapidly opening and closing sessions to verify that invoices and new sessions are created correctly each time.
- **TC8.3** Validate websocket broadcasts for order additions and session closures reach all connected clients.

These test cases cover typical and edge scenarios for the table session workflow and can be implemented using a testing framework such as `pytest` along with FastAPI's test client to simulate requests.
