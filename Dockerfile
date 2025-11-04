FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY main.py .

# Создаем директорию для конфигурации
RUN mkdir -p /config

# Устанавливаем переменные окружения по умолчанию
ENV CONFIG_PATH=/config/config.yaml
ENV PYTHONUNBUFFERED=1

# Запускаем скрипт
CMD ["python", "main.py"]

