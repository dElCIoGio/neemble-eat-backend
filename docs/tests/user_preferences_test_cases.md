# User Preferences Endpoint `/api/v1/users/preferences`

- **TC1** Providing valid preferences updates the current user and returns the updated user document.
- **TC2** If the authenticated user no longer exists, the endpoint returns HTTP 404 `User not found`.
