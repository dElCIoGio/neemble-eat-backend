# Notifications Module - Test Cases and Requirements

This document records test cases for the notifications module implemented in
`app/api/v1/endpoints/notifications.py` using helper functions in
`app/services/notification.py`.

## Basic Requirements

1. **Listing**
   - Retrieve notifications for the authenticated user.
   - Support filtering by type, read status and free text search on title or message.
   - Pagination is done using the `page` query parameter with a default page size of 10.
2. **Unread Count**
   - Provide an endpoint to return the total number of unread notifications for the user.
3. **Retrieval**
   - Fetch a single notification by its ID and ensure it belongs to the current user.
4. **Creation**
   - Allow creation of a notification document for a user.
5. **Status Updates**
   - Provide endpoints to mark a notification read or unread and mark all as read.
6. **Deletion**
   - Delete a notification by ID with proper ownership checks.

## Test Cases

### 1. List Notifications `/api/v1/notifications`
- **TC1.1** No filters returns the first page of notifications for the user.
- **TC1.2** `type` and `is_read` filter the results accordingly.
- **TC1.3** `search` performs a case-insensitive match on title and message.
- **TC1.4** Invalid authentication returns HTTP 401.

### 2. Unread Count `/api/v1/notifications/unread-count`
- **TC2.1** Returns the correct number of unread notifications.
- **TC2.2** If none are unread, returns `0`.

### 3. Get Notification `/api/v1/notifications/{id}`
- **TC3.1** Valid ID belonging to the user returns the notification document.
- **TC3.2** Non-existent or foreign IDs return HTTP 404.

### 4. Create Notification `/api/v1/notifications`
- **TC4.1** Valid payload creates a notification for the specified user.
- **TC4.2** Missing required fields returns HTTP 400 validation error.

### 5. Mark Read `/api/v1/notifications/{id}/read`
- **TC5.1** Marks the notification as read and sets `readOn` timestamp.
- **TC5.2** Foreign IDs return HTTP 404.

### 6. Mark Unread `/api/v1/notifications/{id}/unread`
- **TC6.1** Marks the notification as unread and clears `readOn`.
- **TC6.2** Foreign IDs return HTTP 404.

### 7. Mark All Read `/api/v1/notifications/read-all`
- **TC7.1** Updates all unread notifications for the user and returns the count.

### 8. Delete Notification `/api/v1/notifications/{id}`
- **TC8.1** Valid ID deletes the notification and returns `True`.
- **TC8.2** Foreign IDs return HTTP 404.
