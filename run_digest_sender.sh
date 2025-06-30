#!/bin/bash
# Скрипт для запуска отправки дайджеста из контейнера digest_sender

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Подгружаем переменные окружения из .env
export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)

# Запуск контейнера digest_sender
/usr/bin/docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm \
  -e ADMIN_TELEGRAM_BOT_TOKEN \
  -e ADMIN_TELEGRAM_USER_ID \
  digest_sender
