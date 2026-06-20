FROM python:3.10-alpine

# Переменные окружения
ENV PATH="${PATH}:/root/.local/bin"
ENV PYTHONPATH=/app/src

# Копируем код и конфигурацию
COPY ./src /app/src
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/
COPY ./requirements.txt /app/
COPY ./start.sh /app/

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости
# RUN apk add --no-cache gcc musl-dev python3-dev
RUN pip install --no-cache-dir -r ./requirements.txt

# Права на запуск start.sh
RUN chmod +x ./start.sh

EXPOSE 8000
CMD ["./start.sh"]