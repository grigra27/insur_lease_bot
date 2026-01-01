# Миграция на Timeweb Cloud

## Подготовка сервера Timeweb Cloud

### 1. Создание VPS
1. Войдите в панель управления Timeweb Cloud
2. Создайте новый VPS с параметрами:
   - ОС: Ubuntu 22.04 LTS
   - Минимум: 1 CPU, 1GB RAM, 10GB SSD
   - Рекомендуется: 1 CPU, 2GB RAM, 20GB SSD

### 2. Первоначальная настройка сервера

```bash
# Подключение к серверу
ssh root@YOUR_SERVER_IP

# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install docker-compose-plugin -y

# Установка Git
apt install git -y

# Создание пользователя для деплоя (опционально)
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
```

### 3. Настройка SSH ключей

```bash
# На вашем локальном компьютере
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Копирование ключа на сервер
ssh-copy-id root@YOUR_SERVER_IP
# или
ssh-copy-id deploy@YOUR_SERVER_IP
```

### 4. Клонирование проекта

```bash
# На сервере
cd /home/deploy  # или /root
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git insur_lease_bot
cd insur_lease_bot
```

## Настройка GitHub Secrets

В настройках репозитория GitHub добавьте следующие секреты:

```
TIMEWEB_HOST=YOUR_SERVER_IP
TIMEWEB_USERNAME=deploy  # или root
TIMEWEB_SSH_KEY=YOUR_PRIVATE_SSH_KEY
TIMEWEB_PORT=22  # если используется стандартный порт

# Токены бота (те же, что и раньше)
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_BOT_TOKEN=your_admin_bot_token
ADMIN_TELEGRAM_USER_ID=your_admin_user_id
```

## Ручной запуск на сервере

```bash
# Переход в директорию проекта
cd /home/deploy/insur_lease_bot

# Создание .env файла
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_BOT_TOKEN=your_admin_bot_token
ADMIN_TELEGRAM_USER_ID=your_admin_user_id
EOF

# Создание директории для логов
mkdir -p logs

# Запуск
docker compose up -d --build

# Проверка статуса
docker compose ps
docker compose logs -f
```

## Мониторинг и обслуживание

### Просмотр логов
```bash
# Логи контейнера
docker compose logs -f

# Логи пользовательских запросов
tail -f user_queries.log
```

### Перезапуск бота
```bash
docker compose restart
```

### Обновление
```bash
git pull origin main
docker compose up -d --build
```

### Отправка дайджеста
Теперь дайджест отправляется командой `/digest` прямо в боте (только для администратора).

## Настройка автоматических дайджестов (опционально)

```bash
# Добавить в crontab для ежедневной отправки дайджеста в 9:00
crontab -e

# Добавить строку:
0 9 * * * curl -X POST "https://api.telegram.org/bot$(grep TELEGRAM_BOT_TOKEN /home/deploy/insur_lease_bot/.env | cut -d'=' -f2)/sendMessage" -d "chat_id=$(grep ADMIN_TELEGRAM_USER_ID /home/deploy/insur_lease_bot/.env | cut -d'=' -f2)" -d "text=/digest"
```

## Преимущества оптимизированной версии

1. **Единый контейнер** - упрощенная архитектура
2. **Встроенные дайджесты** - команда `/digest` в боте
3. **Улучшенная обработка ошибок** - более надежная работа
4. **Кеширование данных** - CSV загружается один раз
5. **Healthcheck** - автоматическая проверка работоспособности
6. **Логирование** - ротация логов
7. **Безопасность** - запуск от непривилегированного пользователя

## Отличия от Digital Ocean

- Более простая настройка
- Нет необходимости в Docker Hub
- Прямой деплой через SSH
- Меньше зависимостей в CI/CD
- Единый контейнер вместо двух сервисов