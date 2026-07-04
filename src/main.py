import logging
import asyncio

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src.config import BOT_TOKEN, PORT, WEBHOOK_PATH, WEBHOOK_URL
from src.db import engine
from src.models import Base
from src.handlers import start, booking
from scripts.seed_demo import seed as seed_demo

dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(booking.router)


async def on_startup(bot: Bot) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_demo()
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=False)
        print(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=False)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    app = web.Application()

    async def health(request: web.Request) -> web.Response:
        return web.Response(text="OK")

    app.router.add_get("/", health)

    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=WEBHOOK_PATH)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    print(f"Bot started on port {PORT}, webhook path: {WEBHOOK_PATH}")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())