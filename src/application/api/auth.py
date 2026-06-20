from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
import uuid
from dotenv import load_dotenv

from src.application.infrastructure.sqlite.database import get_db
from src.application.infrastructure.sqlite.models.users import User, RefreshToken
from src.application.schemas.posts import Token, UserRead, UserCreate
from passlib.context import CryptContext

from pydantic import BaseModel

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "fju834fjuihfijwur924ri2ru2r9i2rjowihf84rjr2r293rej")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def create_refresh_token(db: AsyncSession, user_id: int) -> str:
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=7)
    db_token = RefreshToken(user_id=user_id, token=token, expires_at=expires)
    db.add(db_token)
    await db.commit()
    return token


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.name == username))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user(db, username)
    if not user or not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user(db, user_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
    hashed = get_password_hash(user_data.password)
    db_user = User(
        name=user_data.name,
        password=hashed,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(db, user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось аутентифицировать пользователя",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user


class RefreshRequest(BaseModel):
    refresh_token: str


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    return result.scalar_one_or_none()


@router.post("/refresh", response_model=Token, tags=["auth"])
async def refresh_access_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    db_token = await verify_refresh_token(db, request.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    await db.delete(db_token)
    await db.commit()

    user = await get_user(db, db_token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(data={"sub": user.name})
    new_refresh = await create_refresh_token(db, user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh,
    }


@router.get("/users/me", response_model=UserRead, tags=["auth"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user