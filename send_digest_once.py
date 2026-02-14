import asyncio

from telegram.ext import Application

from bot import InsuranceLeasingBot


async def main() -> None:
    bot = InsuranceLeasingBot()
    bot.application = Application.builder().token(bot.bot_token).build()
    await bot._send_digest()


if __name__ == '__main__':
    asyncio.run(main())
