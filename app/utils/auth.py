from datetime import timedelta
from typing import Optional, Dict, Any
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi import Request, Response, HTTPException, Depends
from firebase_admin import auth
from app.core.dependencies import get_settings

settings = get_settings()

# Constants for cookie settings
AUTH_COOKIE_NAME = "auth_token"
REFRESH_COOKIE_NAME = "refresh_token"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days in seconds


def create_session_cookie(id_token: str, max_age: int = SESSION_COOKIE_MAX_AGE) -> str:
    """Create a session cookie from a Firebase ID token."""
    try:
        # Create a session cookie using Firebase Admin SDK
        session_cookie = auth.create_session_cookie(
            id_token,
            expires_in=timedelta(seconds=max_age)
        )
        return session_cookie
    except Exception as e:
        raise ValueError(f"Failed to create session cookie: {str(e)}")


def verify_session_cookie(session_cookie: str) -> Dict[str, Any]:
    """Verify a Firebase session cookie and return the decoded claims."""
    try:
        # Verify the session cookie using Firebase Admin SDK
        decoded_claims = auth.verify_session_cookie(
            session_cookie, clock_skew_seconds=settings.CLOCK_SKEW_SECONDS
        )
        return decoded_claims
    except auth.InvalidSessionCookieError:
        raise ValueError("Invalid session cookie")
    except auth.SessionCookieRevokedError:
        raise ValueError("Session cookie has been revoked")
    except Exception as e:
        raise ValueError(f"Failed to verify session cookie: {str(e)}")


def set_auth_cookies(response: Response, id_token: str) -> None:
    """Set authentication cookies in the response."""
    # Create session cookie
    session_cookie = create_session_cookie(id_token)

    # Set secure HTTP-only cookies
    is_production = settings.ENVIRONMENT == "production" # This is returning False

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=session_cookie,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax"
    )

    # Set refresh token cookie with longer expiration
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=id_token,  # Store the original ID token for refresh
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax"
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies from the response."""

    is_production = settings.ENVIRONMENT == "production"

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax"
    )
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax"
    )


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract the authentication token from request headers or cookies."""
    token = request.cookies.get(AUTH_COOKIE_NAME)

    return token


def get_refresh_token_from_request(request: Request) -> Optional[str]:
    """Extract the refresh token from request cookies."""
    return request.cookies.get(REFRESH_COOKIE_NAME)


def revoke_user_sessions(uid: str) -> None:
    """Revoke all sessions for a user."""
    try:
        auth.revoke_refresh_tokens(uid)
    except Exception as e:
        raise ValueError(f"Failed to revoke user sessions: {str(e)}")


async def get_current_user(request: Request):
    token = get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    try:
        # Verify the session cookie
        decoded_claims = verify_session_cookie(token)
        uid = decoded_claims['sub']  # Firebase stores the UID in the 'sub' claim
        return uid
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

def admin_required(user = Depends(get_current_user)):
    if user.is_admin is not True:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user