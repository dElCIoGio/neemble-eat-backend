# Authentication Module - Test Cases and Requirements

This document outlines the basic requirements and an extensive list of test cases for the authentication module implemented in this project. The authentication layer is primarily handled through Firebase session cookies and the FastAPI endpoints located under `app/api/v1/endpoints/auth.py` with supporting utilities in `app/utils/auth.py`.

## Basic Requirements

1. **Firebase Initialization**
   - The application must initialize Firebase using service account credentials on startup. [`initialize_firebase` in `app/auth/firebase.py`]
2. **Session Cookie Management**
   - Session cookies must be created from a valid Firebase ID token and stored in an HTTP-only cookie (`AUTH_COOKIE_NAME`).
   - A refresh token cookie (`REFRESH_COOKIE_NAME`) should be stored with a longer expiration period.
3. **Middleware Protection**
   - The `AuthMiddleware` should enforce authentication for all non-public endpoints and attach the user information to the request state once verified.
4. **Public Endpoints**
   - Login, register, refresh and other explicitly listed routes must remain publicly accessible without authentication checks.
5. **Error Handling**
   - All authentication failures must return consistent JSON errors with HTTP 401 status.

## Test Cases

### 1. Firebase Initialization
- **TC1.1** Start the application without previously initializing Firebase and verify that `initialize_firebase` successfully initializes the app.
- **TC1.2** Start the application after Firebase was already initialized and confirm it does not reinitialize (no error raised).

### 2. Login Endpoint `/api/v1/auth/login`
- **TC2.1** Successful login with a valid Firebase ID token should return status 200 and set both `auth_token` and `refresh_token` cookies.
- **TC2.2** Login with an invalid ID token should return HTTP 401 with an error message.
- **TC2.3** Login with an expired ID token should return HTTP 401.
- **TC2.4** Verify that an existing user record is updated with the latest `lastLogged` timestamp after login.

### 3. Register Endpoint `/api/v1/auth/register`
- **TC3.1** Register a new user with a valid ID token and additional user data—expect creation of the user and cookies set.
- **TC3.2** Attempt to register using an ID token for a user that already exists—expect HTTP 400 "User already exists".
- **TC3.3** Register with malformed payload or missing fields—expect HTTP 400 with descriptive error.

### 4. Logout Endpoint `/api/v1/auth/logout`
- **TC4.1** Logout with a valid session should revoke Firebase tokens, clear both cookies and return success message.
- **TC4.2** Logout without authentication cookies should still respond with success while clearing any present cookies.

### 5. Refresh Endpoint `/api/v1/auth/refresh`
- **TC5.1** Refresh with a valid session cookie should return status 200 and reset cookies.
- **TC5.2** Refresh with an expired or invalid session cookie but valid refresh token should create a new session cookie and set it in the response.
- **TC5.3** Refresh without any token should return HTTP 401 "No authentication token provided".

### 6. Get Current User `/api/v1/auth/me`
- **TC6.1** Request with valid session cookie should return the authenticated user profile.
- **TC6.2** Request with invalid or expired session cookie should return HTTP 401.
- **TC6.3** If the user is not found in the database, the endpoint should return HTTP 401 "User not found".

### 7. Middleware Authentication
- **TC7.1** Access a protected endpoint with a valid session cookie and ensure the request succeeds.
- **TC7.2** Access a protected endpoint without cookies should return HTTP 401 via the middleware.
- **TC7.3** Access a protected endpoint with an expired cookie and valid refresh token should trigger token refresh and proceed.
- **TC7.4** Verify that public endpoints listed in `_is_public_endpoint` bypass the middleware authentication check.

### 8. Cookie Settings
- **TC8.1** Ensure cookies are set with `HttpOnly` flag and appropriate `secure` and `SameSite` attributes depending on the environment.
- **TC8.2** Verify that cookie expiration times correspond to `SESSION_COOKIE_MAX_AGE` and `REFRESH_COOKIE_MAX_AGE` constants.

### 9. Token Verification Utilities
- **TC9.1** `create_session_cookie` should throw an error when given an invalid ID token.
- **TC9.2** `verify_session_cookie` should raise appropriate errors for invalid, revoked, or expired cookies.
- **TC9.3** `revoke_user_sessions` should revoke all sessions for a user and subsequent verification attempts should fail.

### 10. Security and Edge Cases
- **TC10.1** Attempt login or register with tampered ID tokens to ensure verification rejects them.
- **TC10.2** Attempt to use session cookies from another domain and verify they are rejected because of the cookie settings.
- **TC10.3** Validate that CORS settings allow only configured origins.
- **TC10.4** Confirm that failed authentication does not expose sensitive error details to the client.

These test cases aim to cover typical and edge scenarios for the authentication workflow in this application. They can be implemented using a testing framework such as `pytest` along with HTTP client libraries to simulate requests.
