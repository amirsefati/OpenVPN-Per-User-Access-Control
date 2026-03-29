from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import create_access_token, verify_password
from backend.config import settings
from backend.database import get_db
from backend.models import AdminConfig
from backend.schemas import LoginRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    admin_hash = db.get(AdminConfig, "admin_password_hash")
    if (
        not admin_hash
        or payload.username != settings.admin_username
        or not verify_password(payload.password, admin_hash.value)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(subject=payload.username))
