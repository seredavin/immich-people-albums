#!/bin/bash
set -e

# Режим работы: once (один раз) или cron (по расписанию)
RUN_MODE=${RUN_MODE:-once}

if [ "$RUN_MODE" = "cron" ]; then
    echo "🕐 Starting in cron mode with schedule: ${CRON_SCHEDULE:-0 2 * * *}"
    
    # Создаем cron задачу
    echo "${CRON_SCHEDULE:-0 2 * * *} python /app/main.py >> /proc/1/fd/1 2>&1" > /etc/cron.d/immich-sync
    chmod 0644 /etc/cron.d/immich-sync
    
    # Применяем cron задачи
    crontab /etc/cron.d/immich-sync
    
    # Запускаем cron в foreground режиме
    echo "✅ Cron started. Waiting for scheduled runs..."
    exec cron -f
else
    echo "▶️  Starting in one-time mode"
    echo "Running sync once..."
    exec python /app/main.py
fi

