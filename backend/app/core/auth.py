import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.db.supabase_client import get_supabase_client

security = HTTPBearer()


class RemoteVerificationRequired(Exception):
    """Raised when the token cannot be verified with local JWT settings."""


def _decode_jwt_locally(token: str) -> dict:
    """Verify Supabase JWT with local keys when possible."""
    header = jwt.get_unverified_header(token)
    algorithm = str(header.get("alg") or "")

    if algorithm == "HS256":
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

    if algorithm in {"ES256", "RS256"}:
        if not settings.JWT_PUBLIC_KEY:
            raise RemoteVerificationRequired
        return jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[algorithm],
            audience="authenticated",
        )

    raise jwt.InvalidAlgorithmError(f"Unsupported JWT algorithm: {algorithm}")


def _verify_with_supabase(token: str) -> dict:
    """Ask Supabase Auth to verify asymmetric JWTs when no public key is set."""
    try:
        result = get_supabase_client().auth.get_user(token)
    except Exception as e:
        print(f"Supabase token verification error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = getattr(result, "user", None)
    user_id = getattr(user, "id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {"id": str(user_id), "email": getattr(user, "email", None)}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify Supabase JWT and return user payload."""
    token = credentials.credentials
    try:
        payload = _decode_jwt_locally(token)
    except RemoteVerificationRequired:
        return _verify_with_supabase(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except ValueError as e:
        print(f"JWT key error: {type(e).__name__}: {e}")
        return _verify_with_supabase(token)
    except jwt.InvalidTokenError as e:
        print(f"JWT decode error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {"id": user_id, "email": payload.get("email")}
