from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase_auth.errors import AuthApiError

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.supabase_client import get_supabase_client
from app.models.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(request: Request, body: RegisterRequest) -> AuthResponse:
    """Register a new user via Supabase Auth and create users row."""
    client = get_supabase_client()
    try:
        result = client.auth.sign_up(
            {"email": body.email, "password": body.password}
        )
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    session = result.session
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed — email may be in use",
        )

    user_id = result.user.id if result.user else session.user.id

    # Create corresponding row in the users table
    try:
        client.table("users").insert(
            {"id": str(user_id)}
        ).execute()
    except Exception:
        # Row may already exist if trigger handles it
        pass

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=str(user_id),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login(request: Request, body: LoginRequest) -> AuthResponse:
    """Sign in with email and password."""
    client = get_supabase_client()
    try:
        result = client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    session = result.session
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=str(result.user.id),
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def refresh(request: Request, body: RefreshRequest) -> AuthResponse:
    """Exchange a refresh token for a new access + refresh token pair."""
    client = get_supabase_client()
    try:
        result = client.auth.refresh_session(body.refresh_token)
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    session = result.session
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh session",
        )

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=str(result.user.id),
    )


@router.post("/logout", status_code=200)
async def logout(
    _user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """Sign out the current user."""
    client = get_supabase_client()
    try:
        client.auth.sign_out()
    except Exception:
        pass
    return {"message": "Logged out successfully"}
