import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from api import get_product_info
from config import logger, BOT_TOKEN
from states import Form
from utils import trainigs_calories

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher()

users = {}


@dp.message(Command('start'))
async def bot_start(message: types.Message):
    await message.answer(
        'Привет! Это бот для расчета и контроля калорий и потребления воды!\n'
        'Для начала расскажи о себе при помощи команды "/set_profile"'
    )


@dp.message(Command('help'))
async def get_help(message: types.Message):
    await message.answer(
        'Бот для учета воды, еды и физических нагрузок.\n'
        'Нажмите /set_profile для настройки профиля\n'
        'Вносите количество воды командой '
        '/log_water <количество воды в мл>\n'
        'Вносите еду командой /log_food <продукт> <грамм>\n'
        'Вносите тренировки командой /log_workout <тренировка> '
        '<длительность в минутах>.\n'
        'Получите свой прогресс командой /check_progress'
    )


@dp.message(Command('set_profile'))
async def set_profile(message: types.Message, state: FSMContext):
    global users
    user_id = message.from_user.id
    users[user_id] = {}
    await state.set_state(Form.weight)
    await message.answer(
        'Введите Ваш вес в килограммах:'
    )


@dp.message(Form.weight)
async def get_weight(message: types.Message, state: FSMContext):
    global users
    try:
        weight = float(message.text)
        if weight < 10 or weight >= 350:
            raise ValueError('Введите реалистичный вес!')
        users[message.from_user.id]['weight'] = weight
        await state.update_data(weight=weight)
        await state.set_state(Form.height)
        await message.answer('Введите Ваш рост в сантиметрах:')
    except ValueError:
        await message.answer(
            'Вес должен быть численным значением от 10 до 350!'
        )


@dp.message(Form.height)
async def get_height(message: types.Message, state: FSMContext):
    global users
    try:
        height = float(message.text)
        if height < 70 or height > 250:
            raise ValueError('Введите реалистичный рост!')
        users[message.from_user.id]['height'] = height
        await state.update_data(height=height)
        await state.set_state(Form.age)
        await message.answer('Введите ваш возраст:')
    except ValueError:
        await message.answer(
            'Рост должен быть численным значением от 70 до 250!'
        )


@dp.message(Form.age)
async def get_age(message: types.Message, state: FSMContext):
    global users
    try:
        age = int(message.text)
        if age < 5 or age > 130:
            raise ValueError('Введите реалистичный возраст!')
        users[message.from_user.id]['age'] = age
        await state.update_data(age=age)
        await state.set_state(Form.activity)
        await message.answer(
            'Сколько минут активности у вас в день?'
        )
    except ValueError:
        await message.answer(
            'Возраст должен быть целым числом от 5 до 130!'
        )


@dp.message(Form.activity)
async def get_activity(message: types.Message, state: FSMContext):
    try:
        activity = int(message.text)
        users[message.from_user.id]['activity'] = activity
        await state.update_data(activity=activity)
        await state.set_state(Form.city)
        await message.answer(
            'Введите свой город:'
        )
    except ValueError:
        await message.answer(
            'Время активность должно быть целым числом,'
            'отражающим минуты в день!'
        )


@dp.message(Form.city)
async def get_city(message: types.Message, state: FSMContext):
    city = message.text
    users[message.from_user.id]['city'] = city
    await state.update_data(city=city)
    await state.set_state(Form.calories)
    await message.answer(
        'Введите желаемую дневную цель калорий или нажмите /skip '
        'для автоматического расчета'
    )


@dp.message(Form.calories)
async def get_calories(message: types.Message, state: FSMContext):
    if message.text == '/skip':
        data = await state.get_data()
        cal = (data.get('weight') * 10) + (data.get('height') * 6.25) - (
            data.get('age') * 5
        )
        await state.update_data(calories=cal)
    else:
        try:
            cal = int(message.text)
            await state.update_data(calories=cal)
        except ValueError:
            await message.answer(
                'Калории должны быть целым чилом!'
            )
    profile_data = await state.get_data()
    weight = profile_data.get("weight")
    height = profile_data.get("height")
    activity = profile_data.get("activity")
    bmi = weight / ((height / 100) ** 2)
    water_goal = weight * 30 + (activity / 30) * 500
    users[message.from_user.id]['water_goal'] = water_goal
    users[message.from_user.id]['calories_goal'] = cal
    await state.clear()
    await message.answer(
        f'Ваш профиль сохранен!\n'
        f'Ваш вес: {weight} кг.\n'
        f'Ваш рост: {height} см.\n'
        f'Индекс массы тела: {bmi:.2f}.\n'
        f'Возраст: {profile_data.get("age")}.\n'
        f'Активность в сутки: {profile_data.get("activity")} мин.\n'
        f'Город: {profile_data.get("city")}.\n'
        f'Цель по калориям: {profile_data.get("calories")} ккал.\n'
    )


@dp.message(Command('log_water'))
async def log_water(message: types.Message):
    global users
    try:
        amount = int(message.text.split()[1])
        user_id = message.from_user.id
        if user_id not in users:
            await message.answer(
                'Пользователь не найден. Пожалуйста, настройте свой профиль '
                'командой /set_profile'
            )
        if 'logged_water' not in users[user_id]:
            users[user_id]['logged_water'] = amount
        else:
            users[user_id]['logged_water'] += amount
        water_to_do = users[
            user_id
        ]['water_goal'] - users[user_id]['logged_water']

        await message.answer(
            f'Записано {amount} мл воды. Всего выпито: '
            f'{users[user_id]["logged_water"]} мл жидкости.\n'
            f'Осталось до выполнения нормы: {water_to_do:.1f} мл.'
        )
    except (IndexError, ValueError):
        await message.reply(
            "Введите количество воды в мл: /log_water 250"
        )


@dp.message(Command('log_food'))
async def log_food(message: types.Message):
    global users
    try:
        query = message.text.split()
        prod_name = ' '.join(query[1:-1])
        weight = int(query[-1])
        product = await get_product_info(prod_name)
        user_id = message.from_user.id
        if product:
            cals = product['calories_100g'] * (weight / 100)
            if user_id not in users:
                await message.answer(
                    'Пользователь не найден. Пожалуйста, настройте свой '
                    'профиль командой /set_profile'
                )
            if 'logged_calories' not in users[user_id]:
                users[user_id]['logged_calories'] = cals
            else:
                users[user_id]['logged_calories'] += cals

            cals_to_eat = users[
                user_id
            ]['calories_goal'] - users[user_id]['logged_calories']
            await message.answer(
                f"🍏 {product['name']} ({weight} г) — {cals:.1f} ккал. "
                f"Всего: {users[user_id]['logged_calories']:.1f} ккал. "
                f"Осталось калорий на день: "
                f"{max(cals_to_eat, 0):.1f} ккал."
            )
        else:
            await message.answer(
                'Продукт не найден. Попробуйте написать название латиницей'
            )
    except (IndexError, ValueError):
        message.answer(
            'Ошибка обработки запроса. Используйте формат: \n'
            '/log_food <название продукта латиницей> '
            '<масса в граммах (только число)>'
        )


@dp.message(Command('log_workout'))
async def log_workout(message: types.Message):
    global users
    try:
        query = message.text.split()
        workout_name = ' '.join(query[1:-1]).lower()
        duration = int(query[-1])
        user_id = message.from_user.id
        if user_id not in users:
            await message.answer(
                'Пользователь не найден. Пожалуйста, настройте свой '
                'профиль командой /set_profile'
            )
        water_loss = (duration / 30) * 200
        weight = users[user_id]['weight']
        users[user_id]['water_goal'] += water_loss
        if workout_name not in trainigs_calories:
            await message.answer(
                f'Тип тренировки неизвестен. Доступные для выбора тренировки:'
                f' {", ".join(trainigs_calories.keys())}'
            )
        spent_calories = (duration / 60) * trainigs_calories[
            workout_name
        ] * weight

        if 'burned_calories' not in users[user_id]:
            users[user_id]['burned_calories'] = spent_calories
        else:
            users[user_id]['burned_calories'] += spent_calories

        await message.answer(
            f"🏋️‍♂️ {workout_name.capitalize()} ({duration} мин) — "
            f"{spent_calories:.1f} ккал. Дополнительно: выпейте "
            f"{water_loss:.1f} мл воды.\n"
            f"Всего потрачено: {users[user_id]['burned_calories']:.1f} ккал."
        )
    except (IndexError, ValueError):
        await message.answer(
            'Используйте формат: /log_workout <тип> <время (мин)>'
        )


@dp.message(Command('check_progress'))
async def get_progress(message: types.Message):
    global users
    user_id = message.from_user.id
    if user_id not in users:
        await message.answer(
            'Пользователь не найден. Воспользуйтесь /set_profile, '
            'чтобы настроить профиль для оценки потребностей воды и калорий'
        )
    water_goal = users[user_id].get('water_goal', 0)
    calories_goal = users[user_id].get('calories_goal', 0)
    logged_water = users[user_id].get('logged_water', 0)
    logged_calories = users[user_id].get('logged_calories', 0)
    burned_calories = users[user_id].get('burned_calories', 0)
    water_left = water_goal - logged_water
    cal_balance = calories_goal - logged_calories + burned_calories

    if cal_balance >= 0:
        text = f'Баланс: {cal_balance:.1f} ккал.'
    else:
        text = f'Баланс отрицательный, вы съели на {abs(cal_balance):.1f} ккал больше!'

    await message.answer(
        f'📊 Прогресс:\n'
        f'Вода:\n'
        f'- Выпито {logged_water} мл из {water_goal} мл.\n'
        f'- Осталось выпить: {water_left:.1f}.\n\n'
        f'Калории:\n'
        f'- Потреблено: {logged_calories:.1f} ккал из {calories_goal:.1f}'
        f' ккал.\n'
        f'- Сожжено: {burned_calories:.1f} ккал.\n'
        f'- {text}'
    )


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
