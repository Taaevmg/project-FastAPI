#!/bin/sh
echo "Applying migrations..."
cd /app
python -m alembic upgrade head || python -c "from src.application.infrastructure.sqlite.models.users import Base; from src.application.infrastructure.sqlite.database import engine; Base.metadata.create_all(bind=engine)"
echo "Starting FastAPI..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000