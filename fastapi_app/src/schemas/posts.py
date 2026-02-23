from pydantic import BaseModel, Field

from src.schemas.users import User


class PostRequestSchema(BaseModel):
    author: User
    text: str = Field(max_length=80)


class PostResponseSchema(BaseModel):
    post_text: str
    author_name: str
