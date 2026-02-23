from fastapi import APIRouter, status, HTTPException
from fastapi.responses import FileResponse

from src.schemas.posts import PostRequestSchema, PostResponseSchema


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



@router.get("/")
async def main():
    return FileResponse("src/wwwroot/html/index.html")




