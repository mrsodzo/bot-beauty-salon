from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.config import SALON_NAME


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться", callback_data="start_booking")],
        [InlineKeyboardButton(text="Наши услуги", callback_data="services")],
        [InlineKeyboardButton(text="Контакты", callback_data="contacts")],
    ])


def master_kb(masters: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=m.name, callback_data=f"master_{m.id}")]
        for m in masters
    ] + [
        [InlineKeyboardButton(text="Не важно", callback_data="master_none")]
    ])


def service_kb(services: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{s.name} — {s.price}₽", callback_data=f"service_{s.id}")]
        for s in services
    ] + [
        [InlineKeyboardButton(text="Назад", callback_data="back_master")]
    ])


def date_kb(dates: list[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=d, callback_data=f"date_{d}")]
        for d in dates
    ] + [
        [InlineKeyboardButton(text="Назад", callback_data="back_service")]
    ])


def time_kb(slots: list[tuple]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{t} — {m}", callback_data=f"time_{t}_{mid}_{sid}")]
        for t, m, mid, sid in slots
    ]
    rows.append([InlineKeyboardButton(text="Назад", callback_data="back_date")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="Отменить", callback_data="confirm_no")],
    ])
