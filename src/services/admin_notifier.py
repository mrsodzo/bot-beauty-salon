from __future__ import annotations

from aiogram import Bot

from src.config import ADMIN_CHAT_ID, SALON_NAME


async def notify_admin(bot: Bot, data: dict) -> None:
    if not ADMIN_CHAT_ID:
        return
    text = (
        f"Новая запись в {SALON_NAME}:\n\n"
        f"Мастер: {data.get('master_name', 'Любой')}\n"
        f"Услуга: {data.get('service_name', '—')}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}"
    )
    await bot.send_message(ADMIN_CHAT_ID, text)
