from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from src.keyboards import main_kb
from src.config import SALON_NAME, SALON_ADDRESS, SALON_PHONE
from src.db import AsyncSessionLocal
from src.models import Service

router = Router()


@router.message(StateFilter("*"), F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Добро пожаловать в {SALON_NAME}! Помогу записаться на услугу.",
        reply_markup=main_kb(),
    )


@router.callback_query(StateFilter("*"), F.data == "services")
async def show_services(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        services = (await session.execute(select(Service))).scalars().all()
    text = "Наши услуги:\n\n" + "\n".join([f"{s.name} — {s.price}₽" for s in services])
    await call.message.edit_text(text, reply_markup=main_kb())
    await call.answer()


@router.callback_query(StateFilter("*"), F.data == "contacts")
async def show_contacts(call: CallbackQuery):
    text = f"{SALON_NAME}\n\nАдрес: {SALON_ADDRESS}\nТелефон: {SALON_PHONE}"
    await call.message.edit_text(text, reply_markup=main_kb())
    await call.answer()


@router.callback_query(StateFilter("*"), F.data == "start_booking")
async def start_booking_restarter(call: CallbackQuery, state: FSMContext):
    from src.handlers.booking import start_booking

    await state.clear()
    await start_booking(call, state)
