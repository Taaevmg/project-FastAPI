import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import os, sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from src.application.api import auth, posts, comments, user
from src.application.api.posts import categories_router, locations_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.application.infrastructure.sqlite.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS post_images (
                id SERIAL PRIMARY KEY,
                url VARCHAR NOT NULL,
                post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE
            )
        '''))
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS likes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                post_id INTEGER NOT NULL REFERENCES posts(id),
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, post_id)
            )
        '''))
        # Добавляем колонку avatar_url, если её ещё нет
        await conn.execute(text('''
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='avatar_url'
                ) THEN
                    ALTER TABLE users ADD COLUMN avatar_url VARCHAR;
                END IF;
            END $$;
        '''))
    yield

app = FastAPI(lifespan=lifespan)   # или явно separate_input_output_schemas=True

# Роутеры
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(comments.router, prefix="/api/v1/posts")
app.include_router(user.router, prefix="/api/v1/users")
app.include_router(categories_router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(locations_router, prefix="/api/v1/locations", tags=["locations"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика (загрузки)
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.isdir(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
async def root():
    return {"message": "Blogicum FastAPI. Use /api/v1/docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)