#!/bin/sh
# Запускать из контейнера cron: вызывает send_daily_digest раз в сутки
# Добавляет cron-правило и стартует демон crond

echo "0 9 * * * cd /app && python3 -c 'from digest_sender import send_daily_digest; send_daily_digest()'" > /etc/crontabs/root
crond -f
