from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from src.db import AsyncSessionLocal
from src.models import Master, Service, Slot, Booking
from src.states import Booking as BookingState
from src.keyboards import (
    master_kb,
    service_kb,
    date_kb,
    time_kb,
    confirm_kb,
    main_kb,
)
from src.utils import next_dates, free_slots_for
from src.config import SALON_ADDRESS, ADMIN_CHAT_ID
from src.services.admin_notifier import notify_admin
from datetime import datetime as datetime_cls, date as date_cls

router = Router()


@router.callback_query(F.data == "start_booking")
async def start_booking(call: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        masters = (
            await session.execute(select(Master).where(Master.is_active == True))
        ).scalars().all()
    await call.message.edit_text("Выберите мастера:", reply_markup=master_kb(masters))
    await state.set_state(BookingState.master)
    await call.answer()


@router.callback_query(BookingState.master, F.data.startswith("master_"))
async def handle_master(call: CallbackQuery, state: FSMContext):
    raw = call.data.split("_", 1)[1]
    master_id = None if raw == "none" else int(raw)
    await state.update_data(master_id=master_id)

    async with AsyncSessionLocal() as session:
        stmt = select(Service).where(
            Service.master_id == master_id
        ) if master_id is not None else select(Service)
        services = (await session.execute(stmt)).scalars().all()

    await call.message.edit_text("Выберите услугу:", reply_markup=service_kb(services))
    await state.set_state(BookingState.service)
    await call.answer()


@router.callback_query(BookingState.service, F.data == "back_master")
async def back_to_master(call: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        masters = (
            await session.execute(select(Master).where(Master.is_active == True))
        ).scalars().all()
    await call.message.edit_text("Выберите мастера:", reply_markup=master_kb(masters))
    await state.set_state(BookingState.master)
    await call.answer()


@router.callback_query(BookingState.service, F.data.startswith("service_"))
async def handle_service(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data.split("_", 1)[1])
    await state.update_data(service_id=service_id)

    dates = next_dates(5)
    await call.message.edit_text("Выберите дату:", reply_markup=date_kb(dates))
    await state.set_state(BookingState.date)
    await call.answer()


@router.callback_query(BookingState.date, F.data == "back_service")
async def back_to_service(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    master_id = data.get("master_id")
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Service).where(Service.master_id == master_id)
            if master_id is not None
            else select(Service)
        )
        services = (await session.execute(stmt)).scalars().all()
    await call.message.edit_text("Выберите услугу:", reply_markup=service_kb(services))
    await state.set_state(BookingState.service)
    await call.answer()


@router.callback_query(BookingState.date, F.data.startswith("date_"))
async def handle_date(call: CallbackQuery, state: FSMContext):
    date_str = call.data.split("_", 1)[1]
    await state.update_data(date=date_str)

    today = date_cls.today()
    try:
        month, day = map(int, date_str.split("."))
        selected_date = date_cls(today.year, month, day)
        if selected_date < today:
            selected_date = selected_date.replace(year=today.year + 1)
    except ValueError:
        await call.answer("Ошибка даты", show_alert=True)
        return

    data = await state.get_data()
    slots = await free_slots_for(selected_date, data.get("master_id"))

    if not slots:
        await call.answer("Нет свободных слотов. Выберите другую дату.", show_alert=True)
        return

    await call.message.edit_text("Выберите время:", reply_markup=time_kb(slots))
    await state.set_state(BookingState.time)
    await call.answer()


@router.callback_query(BookingState.time, F.data == "back_date")
async def back_to_date(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Выберите дату:", reply_markup=date_kb(next_dates(5)))
    await state.set_state(BookingState.date)
    await call.answer()


@router.callback_query(BookingState.time, F.data.startswith("time_"))
async def handle_time(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    time_str = parts[1]
    master_id = int(parts[2])
    slot_id = int(parts[3])
    await state.update_data(time=time_str, master_id=master_id, slot_id=slot_id)

    await call.message.edit_text("Как вас зовут?")
    await state.set_state(BookingState.name)
    await call.answer()


@router.message(BookingState.name)
async def input_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Пожалуйста, введите ваше имя.")
        return
    await state.update_data(name=name)
    await message.answer("Ваш телефон?")
    await state.set_state(BookingState.phone)


@router.message(BookingState.phone)
async def input_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone:
        await message.answer("Пожалуйста, введите номер телефона.")
        return
    if not (phone.startswith("+") or phone[0].isdigit()):
        await message.answer("Введите номер в формате +7...")
        return
    await state.update_data(phone=phone)

    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        master = await session.get(Master, data["master_id"])
        service = await session.get(Service, data["service_id"])

    master_name = master.name if master else "Любой"
    service_name = service.name if service else "—"

    summary = (
        "Проверьте данные:\n\n"
        f"Мастер: {master_name}\n"
        f"Услуга: {service_name}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n\n"
        "Подтвердить?"
    )
    await message.answer(summary, reply_markup=confirm_kb())
    await state.set_state(BookingState.confirm)


@router.callback_query(BookingState.confirm, F.data == "confirm_yes")
async def confirm_booking(call: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()

    today = date_cls.today()
    month, day = map(int, data["date"].split("."))
    booking_date = date_cls(today.year, month, day)
    if booking_date < today:
        booking_date = booking_date.replace(year=today.year + 1)

    async with AsyncSessionLocal() as session:
        booking = Booking(
            master_id=data["master_id"],
            service_id=data["service_id"],
            slot_id=data.get("slot_id"),
            date=booking_date,
            time=datetime_cls.strptime(data["time"], "%H:%M").time(),
            client_name=data["name"],
            client_phone=data["phone"],
        )
        session.add(booking)
        if data.get("slot_id"):
            slot = await session.get(Slot, data["slot_id"])
            if slot:
                slot.is_booked = True
        await session.commit()

    await call.message.edit_text(
        f"Вы записаны! Ждём вас {data['date']} в {data['time']}.\nАдрес: {SALON_ADDRESS}",
        reply_markup=main_kb(),
    )

    async with AsyncSessionLocal() as session:
        master = await session.get(Master, data["master_id"])
        service = await session.get(Service, data["service_id"])

    notify_data = {
        "master_name": master.name if master else "Любой",
        "service_name": service.name if service else "—",
        "date": data["date"],
        "time": data["time"],
        "name": data["name"],
        "phone": data["phone"],
    }
    await notify_admin(bot, notify_data)

    await call.answer()
    await state.clear()


@router.callback_query(BookingState.confirm, F.data == "confirm_no")
async def cancel_booking(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Запись отменена.", reply_markup=main_kb())
    await call.answer()
    await state.clear()


@router.message(StateFilter("*"), F.text == "/cancel")
async def cancel_any(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        return
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_kb())
