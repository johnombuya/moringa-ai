# auth.py - login, tokens, and the lock on the door
import os
import time
import jwt
import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "dev-only-secret-please-change-me-32chars!")
TOKEN_LIFETIME_SECONDS = 30 * 60  # 30 minutes

# Two demo users. Passwords are hashed, never stored as plain text.
USERS = {
    "mercy": {
        "password_hash": bcrypt.hashpw(b"logistics2026", bcrypt.gensalt()),
        "role": "coordinator",
    },
    "viewer": {
        "password_hash": bcrypt.hashpw(b"readonly2026", bcrypt.gensalt()),
        "role": "viewer",
    },
}


def check_password(username: str, password: str) -> bool:
    """Verify a username/password pair against stored hashes."""
    user = USERS.get(username)
    if user is None:
        return False
    return bcrypt.checkpw(password.encode(), user["password_hash"])


def create_token(username: str) -> str:
    """Issue a signed JWT with sub, role, and 30-minute expiry."""
    payload = {
        "sub": username,
        "role": USERS[username]["role"],
        "exp": int(time.time()) + TOKEN_LIFETIME_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


bearer = HTTPBearer()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """FastAPI dependency: verify the JWT and return the payload.

    Raises 401 on missing, expired, or invalid tokens.
    """
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return payload


def require_role(required: str):
    """Return a dependency that checks the caller's role.

    Usage: user = Depends(require_role("coordinator"))
    Returns 403 if the token is valid but the role does not match.
    """
    def _check(user: dict = Depends(current_user)) -> dict:
        if user.get("role") != required:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required}' required. You have '{user.get('role')}'.",
            )
        return user
    return _check
