from aiogram.filters.state import State, StatesGroup


class Form(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calories = State()
