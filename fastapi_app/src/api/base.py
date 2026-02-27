from fastapi import APIRouter, status, HTTPException
from fastapi.responses import FileResponse

from src.schemas.posts import PostRequestSchema, PostResponseSchema

from fastapi import APIRouter, HTTPException
from typing import List
from src.schemas.model import Post

router = APIRouter()


@router.get("/hello_world", status_code=status.HTTP_200_OK)
async def get_hello_world() -> dict:
    response = {"text": "Hello, World!"}

    return response


@router.post("/test_json", status_code=status.HTTP_201_CREATED, response_model=PostResponseSchema)
async def test_json(post: PostRequestSchema) -> dict:
    if len(post.text) < 3:
        raise HTTPException(
            detail="Длина поста должна быть не меньше 3 символов",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    response = {
        "post_text": post.text,
        "author_name": post.author.login
    }
    return PostResponseSchema.model_validate(obj=response)

router = APIRouter()
posts = []

@router.get("/", response_model=List[Post])
async def get_posts():
    return posts

@router.post("/", response_model=Post)
async def create_post(post: Post):
    posts.append(post)
    return post

@router.put("/{post_id}", response_model=Post)
async def update_post(post_id: int, updated_post: Post):
    for i, post in enumerate(posts):
        if post_id == i:
            posts[i] = updated_post
            return updated_post
    raise HTTPException(status_code=404, detail="Post not found")

@router.delete("/{post_id}")
async def delete_post(post_id: int):
    for i, post in enumerate(posts):
        if post_id == i:
            posts.pop(i)
            return {"message": "Post deleted"}
    raise HTTPException(status_code=404, detail="Post not found")
#
# @router.get("/")
# async def main():
#     return FileResponse("src/wwwroot/html/index.html")




