import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    tap_count = Column(Integer, default=0)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String, unique=True, nullable=False)         
    is_published = Column(Boolean, default=True)              
    created_at = Column(DateTime, default=datetime.datetime.utcnow) 

    posts = relationship("Post", back_populates="category")

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_published = Column(Boolean, default=True) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    posts = relationship("Post", back_populates="location")

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    pub_date = Column(DateTime, nullable=True)
    is_published = Column(Boolean, default=True) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow) 
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)

    author = relationship("User", back_populates="posts")
    location = relationship("Location", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")

class PostImage(Base):
    __tablename__ = 'post_images'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    post = relationship("Post", back_populates="images")

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow) 
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    post = relationship('Post', back_populates='comments')
    author = relationship('User', back_populates='comments')
