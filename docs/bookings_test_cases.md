# Bookings Module - Test Cases and Requirements

This document outlines the basic requirements and a comprehensive list of test cases for the bookings module implemented in this project. The booking functionality is exposed via FastAPI endpoints in `app/api/v1/endpoints/bookings.py` and the related helper functions in `app/services/booking.py`.

## Basic Requirements

1. **Booking Creation**
   - Create a booking with mandatory fields such as restaurant ID, table ID, start and end times, guest count and customer contact details.
   - Default booking status should be set to `upcoming`.
2. **Retrieval and Listing**
   - Retrieve a single booking by its ID.
   - List bookings for a given restaurant or table.
3. **Modification**
   - Update an existing booking by ID with partial fields.
   - Delete a booking and return confirmation.
4. **Filtering**
   - Provide endpoints to list upcoming bookings and bookings for a specific date.
5. **Error Handling**
   - Invalid booking IDs, restaurant IDs or table IDs should return HTTP 404.
   - Invalid date formats or other validation errors should return HTTP 400 with a meaningful message.

## Test Cases

### 1. Create Booking Endpoint `/api/v1/bookings/`
- **TC1.1** Successful creation with valid payload should return the saved booking with an ID and status `upcoming`.
- **TC1.2** Missing required fields (e.g. `restaurantId` or `tableId`) should return HTTP 400.
- **TC1.3** Start time later than end time should return HTTP 400.

### 2. Get Booking Endpoint `/api/v1/bookings/{booking_id}`
- **TC2.1** Valid ID returns the corresponding booking.
- **TC2.2** Non‑existent ID returns HTTP 404 `Booking not found`.

### 3. Update Booking Endpoint `/api/v1/bookings/{booking_id}`
- **TC3.1** Valid update request modifies the booking and returns the updated values.
- **TC3.2** Update with non‑existent ID returns HTTP 404.
- **TC3.3** Update with invalid fields or types returns HTTP 400.

### 4. Delete Booking Endpoint `/api/v1/bookings/{booking_id}`
- **TC4.1** Valid ID removes the booking and returns `True`.
- **TC4.2** Non‑existent ID returns HTTP 404.

### 5. List Bookings for Restaurant `/api/v1/bookings/restaurant/{restaurant_id}`
- **TC5.1** Existing restaurant returns a list of bookings sorted as stored.
- **TC5.2** Restaurant with no bookings returns an empty list.

### 6. List Bookings for Table `/api/v1/bookings/table/{table_id}`
- **TC6.1** Valid table ID returns all bookings associated with that table.
- **TC6.2** Table with no bookings returns an empty list.

### 7. Upcoming Bookings `/api/v1/bookings/upcoming/{restaurant_id}`
- **TC7.1** Returns bookings with start time greater than the current hour minus one.
- **TC7.2** If no upcoming bookings exist, an empty list is returned.

### 8. Bookings by Date `/api/v1/bookings/date/{restaurant_id}/{day}`
- **TC8.1** Valid date string returns bookings for that day only.
- **TC8.2** Invalid date format returns HTTP 400.
- **TC8.3** Day with no bookings returns an empty list.

### 9. General Edge Cases
- **TC9.1** Ensure all endpoints require authentication where applicable and deny access otherwise.
- **TC9.2** Attempt operations with malformed IDs (not valid ObjectId) and expect HTTP 400.
- **TC9.3** Stress test with a high number of bookings to validate performance and pagination if implemented.

These test cases aim to cover typical scenarios and edge cases for the bookings workflow in this application. They can be implemented using a testing framework such as `pytest` along with HTTP client libraries to simulate requests.
