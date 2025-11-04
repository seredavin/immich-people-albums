#!/bin/bash
# Скрипт для проверки и подготовки config.yaml перед запуском Docker Compose

set -e

CONFIG_FILE="config.yaml"
EXAMPLE_FILE="config.example.yaml"

echo "🔍 Checking configuration file..."

# Проверяем, существует ли директория с именем config.yaml
if [ -d "$CONFIG_FILE" ]; then
    echo "❌ ERROR: Found directory '$CONFIG_FILE' instead of file!"
    echo "   This will cause Docker Compose to fail."
    echo ""
    echo "   To fix this:"
    if [ -z "$(ls -A $CONFIG_FILE)" ]; then
        echo "   rmdir $CONFIG_FILE"
    else
        echo "   rm -rf $CONFIG_FILE  # WARNING: This will delete the directory and its contents!"
    fi
    exit 1
fi

# Проверяем, существует ли файл
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  File '$CONFIG_FILE' does not exist."
    
    if [ -f "$EXAMPLE_FILE" ]; then
        echo "📋 Creating '$CONFIG_FILE' from '$EXAMPLE_FILE'..."
        cp "$EXAMPLE_FILE" "$CONFIG_FILE"
        echo "✅ Created '$CONFIG_FILE'"
        echo ""
        echo "⚠️  IMPORTANT: Please edit '$CONFIG_FILE' and fill in your settings:"
        echo "   - Immich server URL"
        echo "   - API key"
        echo "   - Person to album mappings"
        exit 1
    else
        echo "❌ ERROR: Neither '$CONFIG_FILE' nor '$EXAMPLE_FILE' found!"
        echo "   Please create '$CONFIG_FILE' manually."
        exit 1
    fi
fi

# Проверяем, что это действительно файл
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ ERROR: '$CONFIG_FILE' is not a regular file!"
    exit 1
fi

echo "✅ Configuration file '$CONFIG_FILE' exists and is valid"
echo ""

# Проверяем, не пустой ли файл
if [ ! -s "$CONFIG_FILE" ]; then
    echo "⚠️  WARNING: '$CONFIG_FILE' is empty!"
    echo "   Please fill in your configuration."
    exit 1
fi

# Проверяем, содержит ли он хотя бы минимальные настройки
if ! grep -q "immich:" "$CONFIG_FILE"; then
    echo "⚠️  WARNING: '$CONFIG_FILE' doesn't seem to contain 'immich:' section"
    echo "   Please check your configuration."
fi

echo "✅ Configuration check passed!"
echo "   You can now run: docker-compose up -d"

