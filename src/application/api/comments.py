from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.application.infrastructure.sqlite.database import get_db
from src.application.infrastructure.sqlite.models.users import Post, Comment, User
from src.application.schemas.posts import CommentCreate, CommentRead
from src.application.api.auth import get_current_user

router = APIRouter()


@router.get("/{post_id}/comments/", response_model=list[CommentRead], tags=["comments"])
async def get_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post)
        .options(joinedload(Post.comments).joinedload(Comment.author))
        .filter(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post.comments


@router.post("/{post_id}/comments/", response_model=CommentRead, status_code=status.HTTP_201_CREATED, tags=["comments"])
async def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post).filter(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_comment = Comment(
        text=comment.text,
        post_id=post_id,
        author_id=current_user.id,
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment, attribute_names=["author"])
    return db_comment