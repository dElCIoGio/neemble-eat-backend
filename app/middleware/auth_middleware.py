from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from app.utils.auth import (
    get_token_from_request,
    verify_session_cookie,
    get_refresh_token_from_request,
    set_auth_cookies
)
from app.core.dependencies import get_logger, get_settings
from firebase_admin import auth

logger = get_logger()
settings = get_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:


        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Get token from request
        token = get_token_from_request(request)

        if not token:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "status": HTTP_401_UNAUTHORIZED,
                    "success": False,
                    "message": "Authentication required",
                    "data": None,
                    "error": {
                        "code": HTTP_401_UNAUTHORIZED,
                        "message": "Authentication required"
                    },
                    "meta": None
                }
            )

        try:
            # Verify token
            decoded_claims = verify_session_cookie(token)

            # Add user info to request state
            request.state.user = decoded_claims
            request.state.user_id = decoded_claims.get("uid")

            # Continue with the request
            response = await call_next(request)
            return response

        except auth.ExpiredSessionCookieError:
            # Session cookie has expired
            logger.warning("Session cookie expired.")
        except auth.RevokedSessionCookieError:
            # Session cookie has been revoked
            logger.warning("Revoked session cookie.")
        except auth.InvalidSessionCookieError:
            # Session cookie is invalid
            logger.warning("Invalid session cookie.")

        except ValueError as e:
            # Try to refresh the token if session is invalid
            refresh_token = get_refresh_token_from_request(request)
            if refresh_token:
                try:
                    # Verify refresh token (Note: Firebase doesn't officially support backend refresh via ID token)
                    decoded_token = auth.verify_id_token(refresh_token, clock_skew_seconds=settings.CLOCK_SKEW_SECONDS)

                    # Issue new custom token (this should be sent back to client to re-authenticate)
                    new_custom_token = auth.create_custom_token(decoded_token["uid"])

                    response = await call_next(request)
                    set_auth_cookies(response, refresh_token)
                    return response

                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {str(refresh_error)}")

            # If we get here, authentication failed
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "status": HTTP_401_UNAUTHORIZED,
                    "success": False,
                    "message": str(e),
                    "data": None,
                    "error": {
                        "code": HTTP_401_UNAUTHORIZED,
                        "message": str(e)
                    },
                    "meta": None
                }
            )

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the endpoint is public (doesn't require authentication)."""
        public_paths = [
            "/api/health",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/invitations",
            "/api/v1/blog/",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        return any(path.startswith(public_path) for public_path in public_paths)
