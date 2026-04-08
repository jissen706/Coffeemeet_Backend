import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
TOKEN_EXPIRE_HOURS_CUSTOMER = 24 * 30  # 30 days — customers have no admin power

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def create_token(data: dict) -> str:
    payload = data.copy()
    hours = TOKEN_EXPIRE_HOURS_CUSTOMER if data.get("role") == "customer" else TOKEN_EXPIRE_HOURS
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_token(credentials.credentials)


def require_barista(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("barista", "owner"):
        raise HTTPException(status_code=403, detail="Barista access required")
    return user


def require_owner(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return user


def require_customer(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(optional_security),
) -> dict | None:
    if credentials is None:
        return None
    return decode_token(credentials.credentials)
