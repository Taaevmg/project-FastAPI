from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List

# ---------- User ----------
class UserCreate(BaseModel):
    name: str
    password: str

class UserRead(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    tap_count: int = 0

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str = Field(..., alias="username")
    password: str

# ---------- Token ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

# ---------- Category ----------
class CategoryBase(BaseModel):
    title: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    slug: str

class CategoryRead(CategoryBase):
    id: int
    slug: str
    is_published: bool
    created_at: datetime
    model_config = {"from_attributes": True}

# ---------- Location ----------
class LocationBase(BaseModel):
    name: str

class LocationCreate(LocationBase):
    pass

class LocationRead(LocationBase):
    id: int
    is_published: bool
    created_at: datetime
    model_config = {"from_attributes": True}

# ---------- Post ----------
class PostBase(BaseModel):
    title: str
    text: str
    pub_date: Optional[datetime] = None
    image: Optional[str] = None

class PostImageRead(BaseModel):
    id: int
    url: str
    model_config = {"from_attributes": True}

class PostCreate(PostBase):
    category_name: str = ""
    location_name: str = ""

class PostRead(PostBase):
    id: int
    author: UserRead
    location: Optional[LocationRead] = None
    category: Optional[CategoryRead] = None
    is_published: bool
    created_at: datetime
    images: List[PostImageRead] = []
    comment_count: int = 0
    likes_count: int = 0
    model_config = {"from_attributes": True}

# ---------- Comment ----------
class CommentCreate(BaseModel):
    text: str

class CommentRead(BaseModel):
    id: int
    text: str
    created_at: datetime
    author: UserRead
    post_id: int
    model_config = {"from_attributes": True}