from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid

from src.application.infrastructure.sqlite.database import get_db
from src.application.infrastructure.sqlite.models.users import User
from src.application.schemas.posts import UserRead
from src.application.api.auth import get_current_user

router = APIRouter(tags=["users"])


@router.get("/{username}", response_model=UserRead)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).filter(User.name == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{username}/tap", response_model=UserRead)
async def tap_user(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).filter(User.name == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.tap_count += 1
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    os.makedirs("uploads/avatars", exist_ok=True)
    ext = os.path.splitext(image.filename)[1] if image.filename else ".png"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = f"uploads/avatars/{filename}"
    with open(filepath, "wb") as buffer:
        buffer.write(await image.read())

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(current_user)
    return current_user