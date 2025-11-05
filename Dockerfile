FROM python:3.11-slim

WORKDIR /app

# Устанавливаем cron для режима расписания
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

# Создаем симлинк python -> python3 для совместимости с cron
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python || true

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY main.py .

# Копируем скрипт запуска
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Создаем директорию для конфигурации
RUN mkdir -p /config

# Устанавливаем переменные окружения по умолчанию
ENV CONFIG_PATH=/config/config.yaml
ENV PYTHONUNBUFFERED=1
ENV RUN_MODE=once
ENV CRON_SCHEDULE="0 2 * * *"

# Используем entrypoint скрипт
ENTRYPOINT ["/docker-entrypoint.sh"]

