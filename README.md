# Immich People Albums Sync

[![CI](https://github.com/kirillseredavin/immich-people-albums/actions/workflows/ci.yml/badge.svg)](https://github.com/kirillseredavin/immich-people-albums/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Автоматическая синхронизация фотографий распознанных людей в альбомы Immich.

## Описание

Эта программа автоматически добавляет фотографии распознанных людей в соответствующие альбомы в Immich. Соответствие между людьми и альбомами настраивается через конфигурационный файл.

## Возможности

- ✅ Автоматическое добавление фотографий людей в альбомы
- ✅ Поиск людей по имени или ID
- ✅ Автоматическое создание альбомов, если они не существуют
- ✅ Пропуск уже существующих в альбоме фотографий
- ✅ Работа через Docker контейнер
- ✅ Поддержка расписания (cron)
- ✅ Подробное логирование

## Требования

- Python 3.11+ (для локального запуска)
- Docker и Docker Compose (для запуска в контейнере)
- Immich сервер с API доступом
- API ключ Immich или email/password для аутентификации

## Установка

### 1. Получение API ключа Immich

1. Войдите в Immich веб-интерфейс
2. Перейдите в Settings → API Keys
3. Создайте новый API ключ с необходимыми разрешениями:
   - `person.read` - для чтения информации о людях
   - `asset.read` - для поиска активов
   - `album.read` - для чтения альбомов
   - `album.create` - для создания альбомов
   - `albumAsset.create` - для добавления активов в альбомы

### 2. Настройка конфигурации

Откройте файл `config.yaml` и настройте:

```yaml
immich:
  url: "http://immich-server:3001"  # URL вашего Immich сервера
  api_key: "YOUR_API_KEY_HERE"      # Ваш API ключ

mappings:
  - person_name: "Иван Иванов"
    album_name: "Альбом Ивана"
  - person_name: "Мария Петрова"
    album_name: "Фото с Марией"
```

**Важно:** 
- Если Immich работает в Docker, используйте имя сервиса (например, `immich-server`)
- Если Immich на другом хосте, используйте полный URL (например, `https://immich.example.com`)
- Для локального доступа к Immich из контейнера используйте `host.docker.internal:3001` (на macOS/Windows) или IP адрес хоста (на Linux)

### 3. Запуск

#### Вариант A: Через Docker Compose (рекомендуется)

1. Убедитесь, что `docker-compose.yml` настроен правильно
2. Обновите сеть в `docker-compose.yml`, если Immich использует другую сеть
3. Запустите:

```bash
docker-compose up -d
```

#### Вариант B: Сборка и запуск Docker образа

```bash
# Сборка образа
docker build -t immich-people-albums .

# Запуск контейнера
docker run --rm \
  -v $(pwd)/config.yaml:/config/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  --network immich-network \
  immich-people-albums
```

#### Вариант C: Локальный запуск (без Docker)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py
```

## Настройка расписания

### Вариант 1: Cron на хосте

Если запускаете контейнер без cron, можно настроить cron на хосте:

```bash
# Добавить в crontab (crontab -e)
0 2 * * * docker run --rm -v /path/to/config.yaml:/config/config.yaml:ro immich-people-albums
```

### Вариант 2: Cron в контейнере

Используйте сервис `immich-people-albums-cron` из `docker-compose.yml`:

```bash
docker-compose up -d immich-people-albums-cron
```

Расписание настраивается через переменную окружения `CRON_SCHEDULE` или в `config.yaml` (параметр `schedule`, но он пока не используется в коде).

### Вариант 3: Systemd timer (Linux)

Создайте файл `/etc/systemd/system/immich-people-albums.service`:

```ini
[Unit]
Description=Immich People Albums Sync

[Service]
Type=oneshot
ExecStart=/usr/bin/docker run --rm \
  -v /path/to/config.yaml:/config/config.yaml:ro \
  immich-people-albums
```

И `/etc/systemd/system/immich-people-albums.timer`:

```ini
[Unit]
Description=Run Immich People Albums Sync daily

[Timer]
OnCalendar=daily
OnCalendar=02:00

[Install]
WantedBy=timers.target
```

Запустите:
```bash
sudo systemctl enable immich-people-albums.timer
sudo systemctl start immich-people-albums.timer
```

## Структура конфигурации

```yaml
immich:
  url: "http://immich-server:3001"  # URL сервера Immich
  api_key: "..."                    # API ключ (предпочтительно)
  # email: "..."                    # Альтернатива: email
  # password: "..."                 # Альтернатива: password

schedule: "0 2 * * *"               # Расписание (для справки)

mappings:
  - person_name: "Имя человека"     # Имя в Immich
    person_id: null                  # UUID (если известен, опционально)
    album_name: "Название альбома"   # Название альбома
    album_id: null                   # UUID альбома (если известен, опционально)

options:
  skip_existing: true                # Пропускать уже добавленные
  max_assets_per_run: 0              # Макс. активов за запуск (0 = без ограничений)
  log_level: "INFO"                 # Уровень логирования
```

## Логирование

Логи сохраняются в:
- Консоль (stdout)
- Файл `immich-people-albums.log` (если запускается локально)
- В Docker: логи доступны через `docker logs`

## Устранение проблем

### Ошибка подключения к Immich

- Проверьте URL в `config.yaml`
- Убедитесь, что контейнер может достичь Immich сервер (проверьте сеть Docker)
- Для доступа к Immich на хосте из контейнера используйте `host.docker.internal:3001` (macOS/Windows)

### Человек не найден

- Проверьте точное имя человека в Immich (регистр важен)
- Используйте `person_id` вместо `person_name` для большей надежности
- Убедитесь, что у API ключа есть разрешение `person.read`

### Альбом не создается

- Проверьте разрешения API ключа (`album.create`)
- Проверьте логи на наличие ошибок

### Активы не добавляются

- Проверьте разрешения API ключа (`albumAsset.create`)
- Убедитесь, что у человека есть распознанные фотографии
- Проверьте логи на детали ошибок

## Разрешения API ключа

Минимально необходимые разрешения:
- `person.read` - чтение информации о людях
- `asset.read` - поиск и чтение активов
- `album.read` - чтение альбомов
- `album.create` - создание альбомов
- `albumAsset.create` - добавление активов в альбомы

## Тестирование

Проект включает набор автоматических тестов. Для запуска тестов:

```bash
# Установка зависимостей (если еще не установлены)
pip install -r requirements.txt

# Запуск всех тестов
pytest

# Запуск с покрытием кода
pytest --cov=. --cov-report=html

# Запуск конкретного теста
pytest tests/test_main.py::TestImmichClient::test_get_all_people -v
```

Текущее покрытие кода: **81%** основных компонентов.

## CI/CD

Проект использует GitHub Actions для автоматической сборки и тестирования.

### Доступные workflows:

1. **CI** (`.github/workflows/ci.yml`):
   - Запускается при push и pull requests
   - Тестирование на Python 3.11, 3.12, 3.13
   - Тестирование на Ubuntu и macOS
   - Линтинг кода (flake8, pylint, mypy)
   - Сборка Docker образа
   - Проверка безопасности (Safety, Bandit)
   - Загрузка отчетов о покрытии кода

2. **Docker Build** (`.github/workflows/docker-build.yml`):
   - Простая сборка и проверка Docker образа
   - Запускается при изменении main ветки

3. **Release** (`.github/workflows/release.yml`):
   - Сборка и публикация Docker образа в GitHub Container Registry
   - Создание GitHub Release
   - Запускается при создании тега `v*.*.*` или вручную через workflow_dispatch

### Использование:

```bash
# Локальная проверка перед коммитом
pytest
flake8 .
docker build -t immich-people-albums .

# Создание релиза
git tag v1.0.0
git push origin v1.0.0
```

После создания тега, GitHub Actions автоматически:
- Соберет Docker образ
- Опубликует его в `ghcr.io/USERNAME/immich-people-albums`
- Создаст GitHub Release

## Лицензия

MIT

## Поддержка

При возникновении проблем:
1. Проверьте логи
2. Убедитесь, что все настройки в `config.yaml` корректны
3. Проверьте разрешения API ключа
4. Убедитесь, что Immich сервер доступен
