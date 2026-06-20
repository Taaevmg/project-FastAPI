from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
import os
import uuid
from datetime import datetime as dt

from src.application.infrastructure.sqlite.models.users import Post, User, Category, Location, PostImage, Comment, Like
from src.application.schemas.posts import PostCreate, PostRead, UserRead, CategoryRead, CategoryCreate, LocationRead, LocationCreate
from src.application.infrastructure.sqlite.database import get_db
from src.application.api.auth import get_current_user
from src.application.core.exceptions.domain_exceptions import PostNotFoundError, WrongUserError
from src.application.core.exceptions.database_exceptions import DatabaseError

from fastapi import Form
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
categories_router = APIRouter(tags=["categories"])
locations_router = APIRouter(tags=["locations"])


async def get_or_create_category(db: AsyncSession, category_name: str) -> Category:
    result = await db.execute(select(Category).filter(Category.title == category_name))
    category = result.scalar_one_or_none()
    if not category:
        slug = category_name.lower().replace(' ', '-')
        category = Category(title=category_name, slug=slug)
        db.add(category)
        await db.commit()
        await db.refresh(category)
    return category


async def get_or_create_location(db: AsyncSession, location_name: str) -> Location:
    result = await db.execute(select(Location).filter(Location.name == location_name))
    location = result.scalar_one_or_none()
    if not location:
        location = Location(name=location_name)
        db.add(location)
        await db.commit()
        await db.refresh(location)
    return location


# ---------- Создание поста ----------
@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...),
    text: str = Form(...),
    category_name: str = Form(""),
    location_name: str = Form(""),
    pub_date: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cat = await get_or_create_category(db, category_name or "Без категории")
        loc = await get_or_create_location(db, location_name or "Без локации")

        parsed_date = None
        if pub_date:
            try:
                parsed_date = dt.fromisoformat(pub_date)
            except ValueError:
                parsed_date = None

        db_post = Post(
            title=title,
            text=text,
            location_id=loc.id,
            category_id=cat.id,
            pub_date=parsed_date,
            author_id=current_user.id,
        )
        db.add(db_post)
        await db.flush()

        saved_images = []
        for img in images:
            if img.filename:
                os.makedirs("uploads", exist_ok=True)
                ext = os.path.splitext(img.filename)[1] if img.filename else ".jpg"
                filename = f"{uuid.uuid4()}{ext}"
                filepath = f"uploads/{filename}"
                with open(filepath, "wb") as buffer:
                    buffer.write(await img.read())
                img_obj = PostImage(url=f"/uploads/{filename}", post_id=db_post.id)
                db.add(img_obj)
                saved_images.append(img_obj)

        await db.commit()

        return {
            "id": db_post.id,
            "title": db_post.title,
            "text": db_post.text,
            "pub_date": db_post.pub_date,
            "image": None,
            "is_published": db_post.is_published,
            "created_at": db_post.created_at,
            "author": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "tap_count": current_user.tap_count,
                "avatar_url": current_user.avatar_url,
            },
            "location": {
                "id": loc.id,
                "name": loc.name,
                "is_published": loc.is_published,
                "created_at": loc.created_at,
            },
            "category": {
                "id": cat.id,
                "title": cat.title,
                "description": cat.description,
                "slug": cat.slug,
                "is_published": cat.is_published,
                "created_at": cat.created_at,
            },
            "images": [{"id": i.id, "url": i.url} for i in saved_images],
            "comment_count": 0,
            "likes_count": 0,
        }

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Получение списка постов ----------
@router.get("/", response_model=List[PostRead])
async def get_posts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.category),
            selectinload(Post.location),
            selectinload(Post.images),
            selectinload(Post.comments),
            selectinload(Post.likes),
        )
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    for post in posts:
        post.comment_count = len(post.comments)
        post.likes_count = len(post.likes)
    return posts


# ---------- Получение одного поста ----------
@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.category),
                selectinload(Post.location),
                selectinload(Post.comments),
                selectinload(Post.images),
                selectinload(Post.likes),
            )
            .filter(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if post is None:
            raise PostNotFoundError(post_id)
        post.comment_count = len(post.comments)
        post.likes_count = len(post.likes)
        return post
    except PostNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Internal server error: {str(e)}")


# ---------- Обновление поста ----------
@router.put("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: int,
    updated_post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Post).options(
                selectinload(Post.author),
                selectinload(Post.category),
                selectinload(Post.location),
                selectinload(Post.comments),
                selectinload(Post.images),
                selectinload(Post.likes),
            ).filter(Post.id == post_id)
        )
        db_post = result.scalar_one_or_none()
        if db_post is None:
            raise PostNotFoundError(post_id)

        if db_post.author_id != current_user.id:
            raise WrongUserError()

        for key, value in updated_post_data.dict(exclude_unset=True).items():
            setattr(db_post, key, value)

        await db.commit()
        await db.refresh(db_post)
        return db_post
    except PostNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except WrongUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=str(e) + ": Вы не можете редактировать чужой пост.")
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Internal server error: {str(e)}")


# ---------- Удаление поста ----------
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Post).options(selectinload(Post.images)).filter(Post.id == post_id)
        )
        db_post = result.scalar_one_or_none()
        if db_post is None:
            raise PostNotFoundError(post_id)

        for img in db_post.images:
            if img.url and os.path.exists(img.url.lstrip('/')):
                os.remove(img.url.lstrip('/'))

        await db.delete(db_post)
        await db.commit()
        return None
    except PostNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Internal server error: {str(e)}")


# ---------- Лайки ----------
@router.post("/{post_id}/like/", status_code=status.HTTP_200_OK)
async def like_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = await db.execute(
        select(Like).filter(Like.user_id == current_user.id, Like.post_id == post_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already liked")

    like = Like(user_id=current_user.id, post_id=post_id)
    db.add(like)
    await db.commit()
    return {"detail": "liked"}


@router.delete("/{post_id}/like/", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Like).filter(Like.user_id == current_user.id, Like.post_id == post_id)
    )
    like = result.scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    await db.delete(like)
    await db.commit()
    return {"detail": "unliked"}


# =================== КАТЕГОРИИ ===================
@categories_router.get("/", response_model=List[CategoryRead])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()


@categories_router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).filter(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@categories_router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_category = Category(**category.dict())
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# =================== ЛОКАЦИИ ===================
@locations_router.get("/", response_model=List[LocationRead])
async def get_locations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location))
    return result.scalars().all()


@locations_router.get("/{location_id}", response_model=LocationRead)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).filter(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@locations_router.post("/", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_location = Location(**location.dict())
        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)
        return db_location
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")