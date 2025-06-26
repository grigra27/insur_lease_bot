import os
import datetime
import requests

USER_LOG_FILE = 'user_queries.log'

def load_env():
    """Загружает переменные окружения из .env, если используется python-dotenv."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Если не установлен dotenv, пропускаем

def notify_admin(message, bot_token, user_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": user_id, "text": message}
    try:
        requests.post(url, data=data, timeout=15)
    except Exception as e:
        print(f"Failed to send digest: {e}")

def send_daily_digest():
    load_env()
    admin_bot_token = os.getenv('ADMIN_TELEGRAM_BOT_TOKEN')
    admin_user_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
    if not admin_bot_token or not admin_user_id:
        print("ADMIN_TELEGRAM_BOT_TOKEN or ADMIN_TELEGRAM_USER_ID is not set in environment!")
        return

    if not os.path.exists(USER_LOG_FILE):
        notify_admin('Дайджест: за сутки не было запросов.', admin_bot_token, admin_user_id)
        return

    with open(USER_LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        notify_admin('Дайджест: за сутки не было запросов.', admin_bot_token, admin_user_id)
        return

    # Можно фильтровать только за последние сутки, если файл не очищается
    today = datetime.datetime.now().date()
    today_lines = [
        line for line in lines
        if line and line[:10] == today.isoformat()
    ]
    digest_lines = today_lines if today_lines else lines[-50:]  # fallback: последние 50

    digest = ''.join(digest_lines)
    message = f'Дайджест запросов пользователей в leasing bot за {today}:\n{digest}'
    notify_admin(message, admin_bot_token, admin_user_id)

if __name__ == '__main__':
    send_daily_digest()
