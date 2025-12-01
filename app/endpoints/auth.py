from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import UserTable

router = APIRouter(prefix="/auth", tags=["auth"])

# Config via entorno con defaults seguros para desarrollo
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-.env-to-a-long-random-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Seguridad
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None  # NUEVO

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default_factory=lambda: ACCESS_TOKEN_EXPIRE_MINUTES * 60)

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default_factory=lambda: ACCESS_TOKEN_EXPIRE_MINUTES * 60)

class UserInfo(BaseModel):
    username: str
    roles: List[str]

# Helpers

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _validate_phone(phone: str) -> None:
    """Valida teléfono español de exactamente 9 dígitos (si viene)."""
    if phone and (len(phone) != 9 or not phone.isdigit()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teléfono inválido (9 dígitos requeridos)")

def get_user_by_username(session: Session, username: str) -> Optional[UserTable]:
    return session.exec(select(UserTable).where(UserTable.username == username)).first()

def get_user_by_email(session: Session, email: str) -> Optional[UserTable]:
    return session.exec(select(UserTable).where(UserTable.email == email)).first()

def authenticate_user(session: Session, username: str, password: str) -> Optional[UserTable]:
    user = get_user_by_username(session, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def create_token(subject: str, roles: List[str], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(username: str, roles: List[str]) -> str:
    return create_token(username, roles, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(username: str, roles: List[str]) -> str:
    return create_token(username, roles, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    payload = decode_token(token)
    username: str = payload.get("sub")
    roles: List[str] = payload.get("roles") or []
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (sin sub)")
    return UserInfo(username=username, roles=roles)

# Endpoints
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    if get_user_by_username(session, req.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ya existe")
    if req.email and get_user_by_email(session, req.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    if req.phone:
        _validate_phone(req.phone)

    hashed = pwd_context.hash(req.password)
    user = UserTable(
        username=req.username,
        email=req.email,
        name=req.name,
        phone=req.phone,  # NUEVO
        password_hash=hashed,
        roles=["user"],
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access = create_access_token(user.username, user.roles)
    refresh = create_refresh_token(user.username, user.roles)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = authenticate_user(session, req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    access = create_access_token(user.username, user.roles)
    refresh = create_refresh_token(user.username, user.roles)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    username: str = payload.get("sub")
    roles: List[str] = payload.get("roles") or []
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")
    access = create_access_token(username, roles)
    return AccessTokenResponse(access_token=access)

@router.get("/me", response_model=UserInfo)
def me(current: UserInfo = Depends(get_current_user)):
    return current
