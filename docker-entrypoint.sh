#!/bin/bash
set -e

# Режим работы: once (один раз) или cron (по расписанию)
RUN_MODE=${RUN_MODE:-once}

# Определяем команду Python (python3 по умолчанию в контейнере)
# Находим полный путь к python3 для использования в cron (где PATH ограничен)
PYTHON_CMD=$(which python3 || which python || echo "python3")
PYTHON_PATH=$(which python3 || which python || echo "/usr/local/bin/python3")

if [ "$RUN_MODE" = "cron" ]; then
    echo "🕐 Starting in cron mode with schedule: ${CRON_SCHEDULE:-0 2 * * *}"
    echo "🐍 Using Python: ${PYTHON_PATH}"
    
    # Создаем cron задачу
    # В cron используем полный путь к python3 и настраиваем PATH для окружения
    # Также добавляем переменные окружения, которые могут понадобиться
    cat > /etc/cron.d/immich-sync << EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CONFIG_PATH=${CONFIG_PATH:-/config/config.yaml}
PYTHONUNBUFFERED=1
${CRON_SCHEDULE:-0 2 * * *} root ${PYTHON_PATH} /app/main.py >> /proc/1/fd/1 2>>/proc/1/fd/2
EOF
    chmod 0644 /etc/cron.d/immich-sync
    
    # Применяем cron задачи
    crontab /etc/cron.d/immich-sync
    
    # Запускаем cron в foreground режиме
    echo "✅ Cron started. Waiting for scheduled runs..."
    exec cron -f
else
    echo "▶️  Starting in one-time mode"
    echo "Running sync once..."
    exec ${PYTHON_CMD} /app/main.py
fi

