FROM python:3.10-alpine

# Устанавливаем рабочую директорию и PYTHONPATH
WORKDIR /application
ENV PYTHONPATH=/application

# Устанавливаем системные зависимости (для сборки bcrypt и др.)
RUN apk add --no-cache gcc musl-dev python3-dev

# Копируем и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Даём права на выполнение start.sh
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]