import logging
import os
import datetime
import traceback
import re
from difflib import SequenceMatcher
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pandas as pd
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
USER_LOG_FILE = 'user_queries.log'
CSV_FILE = 'tariffs_online.csv'

class InsuranceLeasingBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_user_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN env variable is not set!")
        
        # Загружаем данные один раз при инициализации
        self.df = self._load_data()
        
        # Инициализируем планировщик
        self.scheduler = AsyncIOScheduler()
        
        # Сохраняем ссылку на application для отправки сообщений
        self.application = None
        
    def _load_data(self):
        """Загружает данные из CSV файла с кешированием"""
        try:
            df = pd.read_csv(CSV_FILE, sep=';')
            df['property_normalized'] = df['property'].fillna('').astype(str).map(self._normalize_text)
            logger.info(f"Loaded {len(df)} records from {CSV_FILE}")
            return df
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Нормализует текст для устойчивого поиска"""
        char_map = str.maketrans({
            'а': 'a', 'в': 'b', 'е': 'e', 'к': 'k', 'м': 'm', 'н': 'h',
            'о': 'o', 'р': 'p', 'с': 'c', 'т': 't', 'у': 'y', 'х': 'x',
        })
        normalized = str(text).strip().lower().translate(char_map)
        normalized = re.sub(r'[^\w\s-]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def _find_fuzzy_matches(self, normalized_phrase: str, limit: int = 5):
        """Находит похожие модели при опечатках"""
        if not normalized_phrase:
            return []

        unique_values = self.df['property_normalized'].dropna().unique()
        scored = []
        for value in unique_values:
            score = SequenceMatcher(a=normalized_phrase, b=value).ratio()
            if score >= 0.62:
                scored.append((value, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [value for value, _ in scored[:limit]]
    
    def _log_user_query(self, user, text):
        """Логирует запрос пользователя"""
        now = datetime.datetime.now()
        iso_time = now.isoformat()
        user_id = user.id
        username = user.username or '-'
        first_name = user.first_name or '-'
        last_name = user.last_name or '-'
        
        log_line = (f"{iso_time} | user_id: {user_id} | username: {username} | "
                   f"имя: {first_name} | фамилия: {last_name} | запрос: {text}\n")
        
        try:
            with open(USER_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            logger.error(f"Failed to log user query: {e}")
    
    async def _notify_admin(self, message):
        """Отправляет уведомление администратору"""
        if not self.admin_user_id:
            logger.warning('Admin user id not set, cannot notify admin!')
            return
        
        if not self.application:
            logger.warning('Application not initialized, cannot notify admin!')
            return
        
        try:
            await self.application.bot.send_message(
                chat_id=self.admin_user_id,
                text=message
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    async def _search_in_base(self, search_phrase):
        """Поиск в базе данных"""
        if self.df.empty:
            return "❗️ База данных недоступна. Попробуйте позже."

        normalized_phrase = self._normalize_text(search_phrase)
        if not normalized_phrase:
            return "Пожалуйста, введите корректный запрос."
        
        # Точное вхождение после нормализации
        used_df = self.df[
            self.df['property_normalized'].str.contains(normalized_phrase, regex=False, na=False)
        ]

        # Если точного нет - пробуем нечеткий поиск по близким строкам
        if len(used_df) == 0:
            fuzzy_matches = self._find_fuzzy_matches(normalized_phrase)
            if fuzzy_matches:
                used_df = self.df[self.df['property_normalized'].isin(fuzzy_matches)]
        
        if len(used_df) == 0:
            return (
                f"❗️ Ничего не найдено по запросу «{search_phrase}».\n\n"
                "🔍 Проверьте написание или попробуйте другой вариант названия.\n\n"
                "💡 Примеры запросов:\n"
                "- Haval Jolion\n"
                "- sitrak\n"
                "- BMW X5"
            )
        
        records_count = len(used_df)
        property_min = round((used_df['property_value'].min()) / 1000000, 3)
        property_median = round((used_df['property_value'].median()) / 1000000, 3)
        property_max = round((used_df['property_value'].max()) / 1000000, 3)
        tarif_min = round(used_df['tarif'].min(), 2)
        tarif_median = round(used_df['tarif'].median(), 2)
        tarif_max = round(used_df['tarif'].max(), 2)
        insurance_type = used_df['type'].mode()[0] if not used_df['type'].empty else "Не указано"
        insurance_company = used_df['insurer'].mode()[0] if not used_df['insurer'].empty else "Не указано"
        
        return (
            f"🔍 Результаты по запросу: \"{search_phrase}\"\n\n"
            f"📄 Найдено {records_count} запис{'ь' if records_count == 1 else 'и'} о таком предмете лизинга.\n\n"
            "💰 Цена предмета лизинга:\n"
            f"• Медианная цена: {property_median} млн ₽\n"
            f"• Диапазон: от {property_min} млн ₽ до {property_max} млн ₽\n\n"
            "🛡 Страховой тариф:\n"
            f"• Медианный тариф: {tarif_median}%\n"
            f"• Диапазон: от {tarif_min}% до {tarif_max}%\n\n"
            f"🏷 Чаще всего страхуется как: \"{insurance_type}\"\n"
            f"🏙 Чаще всего страхуется в страховой компании: \"{insurance_company}\""
        )
    
    def _get_welcome_phrase(self):
        """Возвращает приветственное сообщение"""
        return (
            f"👋 Добро пожаловать!\n\n"
            f"📊 Вы можете найти информацию о страховании лизингового имущества. "
            f"В нашей базе сейчас {len(self.df)} записей.\n\n"
            f"🔎 Просто введите название интересующего вас предмета лизинга, "
            f"например 'Haval Dargo' или 'sitrak'."
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(self._get_welcome_phrase())
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        commands = [
            '/start — приветствие',
            '/help — список команд',
            '/digest — отправить дайджест админу (только для админа)',
            'Отправьте название предмета лизинга — получите информацию из базы',
        ]
        help_text = 'Доступные команды:\n' + '\n'.join(commands)
        await update.message.reply_text(help_text)
    
    async def digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /digest - отправка дайджеста"""
        user_id = str(update.effective_user.id)
        if user_id != self.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        try:
            await self._send_digest()
            await update.message.reply_text("✅ Дайджест отправлен!")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при отправке дайджеста: {e}")
    
    async def _send_digest(self):
        """Отправляет дайджест администратору"""
        if not os.path.exists(USER_LOG_FILE):
            await self._notify_admin('Дайджест: за последние 24 часа не было запросов.')
            return
        
        with open(USER_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            await self._notify_admin('Дайджест: за последние 24 часа не было запросов.')
            return
        
        # Фильтруем записи за последние 24 часа
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        
        recent_lines = []
        for line in lines:
            if line and len(line) > 19:  # Проверяем, что строка содержит дату
                try:
                    # Извлекаем дату из строки лога (формат: 2026-01-01T18:43:29.811)
                    log_time_str = line[:19]  # Берем первые 19 символов
                    log_time = datetime.datetime.fromisoformat(log_time_str)
                    
                    # Если запись за последние 24 часа
                    if log_time >= yesterday:
                        recent_lines.append(line)
                except (ValueError, IndexError):
                    # Если не удалось распарсить дату, пропускаем строку
                    continue
        
        # Если нет записей за 24 часа, сообщаем об этом
        if not recent_lines:
            await self._notify_admin('Дайджест: за последние 24 часа не было запросов.')
            return
        
        digest = ''.join(recent_lines)
        message = f'Дайджест запросов пользователей в leasing bot за последние 24 часа ({len(recent_lines)} запросов):\n\n{digest}'
        
        # Разбиваем длинные сообщения
        if len(message) > 4000:
            message = message[:4000] + "\n... (сообщение обрезано)"
        
        await self._notify_admin(message)
        logger.info(f"Daily digest sent successfully: {len(recent_lines)} queries")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        query = update.message.text.strip()
        
        self._log_user_query(user, query)
        
        if not query:
            await update.message.reply_text('Пожалуйста, введите корректный запрос.')
            return
        
        try:
            result = await self._search_in_base(query)
            await update.message.reply_text(result)
        except Exception as e:
            err_msg = f"Срочно! Бот не смог обработать запрос:\nОшибка при обработке запроса пользователя {user.id} ({user.username}): {e}\n{traceback.format_exc()}"
            await self._notify_admin(err_msg)
            await update.message.reply_text('Произошла ошибка при обработке запроса. Администратор уведомлен.')
    
    def _setup_scheduler(self):
        """Настройка планировщика для автоматических дайджестов"""
        # Отправка дайджеста каждый день в 2:00 UTC
        self.scheduler.add_job(
            self._send_digest,
            CronTrigger(hour=2, minute=0),
            id='daily_digest',
            name='Daily Digest',
            replace_existing=True
        )
        logger.info("Scheduler configured for daily digest at 2:00 UTC")
    
    def run(self):
        """Запуск бота"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('digest', self.digest_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Настраиваем планировщик
        self._setup_scheduler()
        self.scheduler.start()
        
        logger.info("Starting bot with daily digest scheduler...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = InsuranceLeasingBot()
    bot.run()
