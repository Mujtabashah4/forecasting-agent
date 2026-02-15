"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from app.schemas.request import TokenRequest
from app.schemas.response import TokenResponse
from app.services.auth_service import authenticate_user, create_access_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """
    Get access token with username and password.

    This endpoint authenticates the user and returns a JWT token.
    """
    # Authenticate user
    user = authenticate_user(request.username, request.password)

    if not user:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role")},
        expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {request.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
