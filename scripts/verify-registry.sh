#!/bin/bash
# Скрипт для проверки образа в GitHub Container Registry

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-kirillseredavin}"
IMAGE_NAME="immich-people-albums"
TAG="${1:-latest}"
FULL_IMAGE="ghcr.io/${REPO_OWNER}/${IMAGE_NAME}:${TAG}"

echo "🔍 Checking Docker image: ${FULL_IMAGE}"
echo ""

# Проверка наличия GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN не установлен. Некоторые проверки будут пропущены.${NC}"
    echo "   Установите: export GITHUB_TOKEN=your_token"
    echo ""
fi

# 1. Проверка через API (если есть токен)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "📋 Checking image metadata via API..."
    
    # Проверка манифеста
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "https://ghcr.io/v2/${REPO_OWNER}/${IMAGE_NAME}/manifests/${TAG}")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Image manifest found (HTTP ${HTTP_CODE})${NC}"
    else
        echo -e "${RED}❌ Image manifest not found (HTTP ${HTTP_CODE})${NC}"
        exit 1
    fi
    
    # Список тегов
    echo ""
    echo "📋 Available tags:"
    curl -s -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "https://ghcr.io/v2/${REPO_OWNER}/${IMAGE_NAME}/tags/list" \
        | jq -r '.tags[]' 2>/dev/null | head -10 || echo "Could not fetch tags"
    echo ""
fi

# 2. Проверка через Docker
echo "🐳 Pulling image from registry..."
if docker pull "${FULL_IMAGE}"; then
    echo -e "${GREEN}✅ Image successfully pulled${NC}"
else
    echo -e "${RED}❌ Failed to pull image${NC}"
    exit 1
fi

echo ""

# 3. Проверка версии Python
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(docker run --rm "${FULL_IMAGE}" python --version 2>&1)
echo -e "${GREEN}✅ ${PYTHON_VERSION}${NC}"

# 4. Проверка зависимостей
echo ""
echo "📦 Checking dependencies..."
if docker run --rm "${FULL_IMAGE}" python -c "import requests; import yaml; print('✅ All dependencies OK')" 2>&1; then
    echo -e "${GREEN}✅ Dependencies verified${NC}"
else
    echo -e "${RED}❌ Dependencies check failed${NC}"
    exit 1
fi

# 5. Проверка размера образа
echo ""
echo "📊 Image information:"
docker images "${FULL_IMAGE}" --format "Size: {{.Size}}"

# 6. Проверка наличия main.py
echo ""
echo "📄 Checking main.py..."
if docker run --rm "${FULL_IMAGE}" test -f /app/main.py; then
    echo -e "${GREEN}✅ main.py found${NC}"
    docker run --rm "${FULL_IMAGE}" ls -lh /app/main.py
else
    echo -e "${RED}❌ main.py not found${NC}"
    exit 1
fi

# 7. Тестовый запуск (без реального подключения)
echo ""
echo "🧪 Testing startup (should fail without config, but that's OK)..."
docker run --rm "${FULL_IMAGE}" python main.py 2>&1 | head -5 || echo -e "${GREEN}✅ Script can be executed (config error expected)${NC}"

echo ""
echo -e "${GREEN}✅ All checks passed! Image is ready to use.${NC}"
echo ""
echo "Usage:"
echo "  docker pull ${FULL_IMAGE}"
echo "  docker run --rm -v \$(pwd)/config.yaml:/config/config.yaml:ro ${FULL_IMAGE}"

