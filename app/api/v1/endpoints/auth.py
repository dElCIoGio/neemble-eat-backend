from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response, HTTPException, Body
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.dependencies import get_settings
from app.services.user import create_user
from app.utils.auth import (
    set_auth_cookies,
    clear_auth_cookies,
    verify_session_cookie,
    get_token_from_request,
    revoke_user_sessions,
    get_current_user
)
from app.models.user import UserModel
from app.schema.user import User, UserCreate
from firebase_admin import auth

from app.utils.time import now_in_luanda

router = APIRouter()
user_model = UserModel()
settings = get_settings()


@router.post("/login")
async def login(
        response: Response,
        id_token: str = Body(..., embed=True, alias="idToken")
):
    """
    Login endpoints that verifies Firebase ID token and sets session cookies.

    The frontend should authenticate with Firebase and send the ID token to this endpoints.
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=settings.CLOCK_SKEW_SECONDS)
        firebase_uid = decoded_token.get("uid")

        # Set authentication cookies
        set_auth_cookies(response, id_token)

        # Get or create user in our database

        user = await user_model.get_user_by_firebase_uid(firebase_uid)

        await user_model.update(str(user.id), {
            "lastLogged": now_in_luanda()
        })

        # if not user:
        #     # User doesn't exist in our database yet, create them
        #     email = decoded_token.get("email", "")
        #
        #     # Create basic user record
        #     new_user_data = UserCreate(
        #         email=email,
        #         firebase_uid=firebase_uid,
        #         first_name=decoded_token.get("name", "").split()[0] if decoded_token.get("name") else "",
        #         last_name=" ".join(decoded_token.get("name", "").split()[1:]) if decoded_token.get("name") and len(
        #             decoded_token.get("name", "").split()) > 1 else "",
        #         phone=decoded_token.get("phone_number", "")
        #     )
        #
        #     user = await user_model.create_user(new_user_data)

        # Return user data
        return {
            "message": "Login successful",
            "data": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )


@router.post("/logout")
async def logout(
        response: Response,
        uid: str = Depends(get_current_user)
):
    """Logout endpoints that clears session cookies and revokes Firebase sessions."""
    try:
        # Revoke Firebase sessions
        if uid:
            revoke_user_sessions(uid)

        # Clear cookies
        clear_auth_cookies(response)

        return {
            "message": "Logout successful",
            "data": True
        }

    except Exception as e:
        # Even if there's an error, clear cookies
        clear_auth_cookies(response)

        return {
            "message": f"Logout completed with errors: {str(e)}",
            "data": True
        }


@router.get("/me", response_model=User)
async def get_current_user_info(
        request: Request,
        firebase_uid: str = Depends(get_current_user)
):
    """Get current authenticated user information."""

    if not firebase_uid:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = await user_model.get_user_by_firebase_uid(firebase_uid)

    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user.to_response()


@router.post("/refresh")
async def refresh_token(
        request: Request,
        response: Response
):
    """Refresh the authentication token."""
    token = get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided"
        )

    try:
        # Verify the current token
        decoded_claims = verify_session_cookie(token)

        # Get a fresh ID token from Firebase
        # In a real implementation, you would need to handle this differently
        # as the backend can't directly refresh ID tokens
        # This is a simplified version for demonstration

        # Create a custom token
        custom_token = auth.create_custom_token(decoded_claims["uid"])

        # In a real app, the frontend would exchange this custom token for an ID token
        # For demo purposes, we'll just use the current token again

        # Set new cookies with the "refreshed" token
        set_auth_cookies(response, token)

        return {
            "message": "Token refreshed successfully",
            "data": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {str(e)}"
        )


@router.post("/register", response_model=User   )
async def register_user(
        response: Response,
        payload: dict = Body(...)
):
    """
    Register a new user with additional profile information.

    The frontend should create the user with Firebase Authentication first,
    then send the ID token along with additional user data to this endpoints.
    """

    id_token: str = payload.get("idToken")
    user_data: dict = payload.get("userData")

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=settings.CLOCK_SKEW_SECONDS)

        firebase_uid = decoded_token["sub"]

        # Check if user already exists
        existing_user = await user_model.get_user_by_firebase_uid(firebase_uid)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )

        # Create user in our database
        user = await create_user(user_data, firebase_uid)

        # Set authentication cookies
        set_auth_cookies(response, id_token)

        return user.to_response()

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )
