# Telegram Bot for Leasing Insurance Search

Этот проект включает Telegram-бота для поиска информации о страховании лизинговых предметов с встроенной системой дайджестов.

## Компоненты проекта

### Основной бот (`bot.py`)
- Поиск информации о страховании лизинговых предметов по данным из `tariffs_online.csv`
- Логирование пользовательских запросов в `user_queries.log`
- Уведомления администратора о критических ошибках
- Встроенная система дайджестов (команда `/digest`)

## Запуск

### Локальный запуск
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Настройте переменные окружения в файле `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_main_bot_token
   ADMIN_TELEGRAM_USER_ID=your_admin_user_id
   ```

3. Запустите бота:
   ```bash
   python bot.py
   ```

### Запуск через Docker
1. Соберите образ:
   ```bash
   docker build -t insur-lease-bot .
   ```

2. Запустите через docker-compose:
   ```bash
   docker compose up -d
   ```

## Использование
- Отправьте любое слово или фразу — получите информацию по предмету лизинга из базы
- Команда `/start` — приветствие и краткая инструкция
- Команда `/help` — напоминание о функционале
- Команда `/digest` — отправка дайджеста админу (только для администратора)

## Структура проекта

### Основные файлы
- `bot.py` — основной код Telegram-бота с встроенными дайджестами
- `send_digest_once.py` — одноразовый запуск отправки дайджеста (для cron)
- `tariffs_online.csv` — база данных тарифов

### Конфигурация и развертывание
- `requirements.txt` — зависимости Python
- `Dockerfile` — конфигурация Docker-образа
- `docker-compose.yml` — настройки для запуска контейнеров
- `.env` — переменные окружения

### Вспомогательные файлы
- `secrets-examples.txt` — примеры конфигурации секретов
- `user_queries.log` — лог пользовательских запросов
- `tariffs_service_file.ipynb` — Jupyter notebook для анализа данных

## Зависимости
- python-telegram-bot — работа с Telegram Bot API
- pandas — обработка данных из CSV
- python-dotenv — загрузка переменных окружения

## CI/CD
Проект настроен для автоматического развертывания через GitHub Actions на Timeweb Cloud.

## Деплой на Timeweb Cloud

1. Подготовьте сервер (Docker + Docker Compose plugin + Git).
2. Добавьте GitHub Secrets:
   ```
   TIMEWEB_HOST=YOUR_SERVER_IP
   TIMEWEB_USERNAME=deploy
   TIMEWEB_SSH_KEY=YOUR_PRIVATE_SSH_KEY
   TELEGRAM_BOT_TOKEN=your_bot_token
   ADMIN_TELEGRAM_USER_ID=your_admin_user_id
   ```
3. Workflow `.github/workflows/deploy.yml` автоматически:
   - обновляет код на сервере,
   - собирает контейнер,
   - перезапускает сервис через `docker compose up -d --build`.

## Дайджесты

### Ручной запуск
- Используйте команду `/digest` в Telegram (доступно только администратору).

### Автозапуск через cron (опционально)
Важно: команда `sendMessage ... text=/digest` **не запускает** обработчик `/digest` в вашем боте — она просто отправляет вам текст `/digest` как обычное сообщение.

Если нужен внешний запуск дайджеста по cron, вызывайте отдельный скрипт внутри контейнера:

```bash
crontab -e
```

```cron
0 9 * * * cd /home/deploy/insur_lease_bot && docker compose exec -T insur_lease_bot python send_digest_once.py >/dev/null 2>&1
```

Скрипт `send_digest_once.py` использует ту же логику, что и команда `/digest`, и отправляет реальный дайджест администратору.

## Новые возможности

### Оптимизированная архитектура
- Единый контейнер вместо двух отдельных сервисов
- Кеширование данных CSV при запуске
- Встроенная система дайджестов

### Улучшенная надежность
- Healthcheck проверяет наличие токена, доступность и читаемость CSV базы
- Ротация логов (максимум 30MB, 3 файла)
- Улучшенная обработка ошибок
- Запуск от непривилегированного пользователя

### Упрощенное управление
- Команда `/digest` для ручной отправки дайджеста
- Автоматическое создание директорий для логов
- Упрощенный процесс деплоя без Docker Hub
