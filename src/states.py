from aiogram.fsm.state import State, StatesGroup


class Booking(StatesGroup):
    master = State()
    service = State()
    date = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()
