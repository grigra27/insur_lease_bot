import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from useful_data import search_in_our_base, get_welcome_phrase
import os
import traceback
import datetime
import requests

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

USER_LOG_FILE = 'user_queries.log'
ADMIN_BOT_TOKEN = os.getenv('ADMIN_TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_TELEGRAM_USER_ID')


def log_user_query(user_id, username, text):
    with open(USER_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now().isoformat()} | {user_id} | {username} | {text}\n")


def notify_admin(message):
    if not ADMIN_BOT_TOKEN or not ADMIN_USER_ID:
        logger.warning('Admin bot token or user id not set, cannot notify admin!')
        return
    url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_USER_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")


def send_daily_digest():
    """
    Читает user_queries.log и отправляет дайджест админу. Запускать отдельно (например, по cron).
    """
    if not ADMIN_BOT_TOKEN or not ADMIN_USER_ID:
        logger.warning('Admin bot token or user id not set, cannot send digest!')
        return
    if not os.path.exists(USER_LOG_FILE):
        notify_admin('Дайджест: за сутки не было запросов.')
        return
    with open(USER_LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        notify_admin('Дайджест: за сутки не было запросов.')
        return
    # Можно фильтровать по дате, если файл не очищается
    digest = ''.join(lines[-50:])  # последние 50 запросов
    message = f'Дайджест запросов пользователей за сутки:\n{digest}'
    url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_USER_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=15)
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_welcome_phrase())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = [
        '/start — приветствие',
        '/help — список команд',
        'Отправьте название предмета лизинга — получите информацию из базы',
    ]
    help_text = 'Доступные команды:\n' + '\n'.join(commands)
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    query = update.message.text.strip()
    log_user_query(user.id, user.username, query)
    if not query:
        await update.message.reply_text('Пожалуйста, введите корректный запрос.')
        return
    try:
        result = await search_in_our_base(query)
        await update.message.reply_text(result, parse_mode='Markdown')
    except Exception as e:
        err_msg = f"Ошибка при обработке запроса пользователя {user.id} ({user.username}): {e}\n{traceback.format_exc()}"
        notify_admin(f"Срочно! Бот не смог обработать запрос: {err_msg}")
        await update.message.reply_text('Произошла ошибка при обработке запроса. Администратор уведомлен.')

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN env variable is not set!")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
