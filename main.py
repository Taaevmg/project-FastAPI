import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os
import logging
import time
import sys
import asyncio

# Добавляем корень проекта в путь, чтобы работали импорты src...
sys.path.insert(0, os.path.dirname(__file__))

from src.application.api import auth, posts, comments, user

app = FastAPI()

# API роутеры
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(comments.router, prefix="/api/v1/posts")
app.include_router(user.router, prefix="/api/v1/users")

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

# Корневой эндпоинт
@app.get("/")
async def root():
    return {"message": "Blogicum FastAPI. Use /api/v1/docs"}

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(f"{request.method} {request.url} - {response.status_code} ({duration:.2f}s)")
        return response

app.add_middleware(LoggingMiddleware)

# Тестовые эндпоинты (потом можно удалить)
@app.get("/async-test")
async def async_test():
    await asyncio.sleep(5)
    return {"message": "done after 5 seconds"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# Middleware для запрета кэширования Swagger
class NoCacheSwaggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path in ["/docs", "/openapi.json"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheSwaggerMiddleware)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)