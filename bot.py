import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
import requests
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, EXCHANGE_RATES_API
from googletrans import Translator

import sqlite3

bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

button_register = KeyboardButton(text='Зарегистрироваться в боте')
button_exchange_rates = KeyboardButton(text='Курс валют')
button_tips = KeyboardButton(text='Советы по экономии')
button_finance = KeyboardButton(text='Личные финансы')
button_BD = KeyboardButton(text='Посмотреть БД')

keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_register, button_exchange_rates],
    [button_tips, button_finance],
    [button_BD]
    ], resize_keyboard=True)

conn = sqlite3.connect('user.db')
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expenses1 REAL, 
    expenses2 REAL,
    expenses3 REAL
    )""")
# expenses расходы

conn.commit()

class FinancesForm(StatesGroup):
    category1 = State()
    category2 = State()
    category3 = State()
    expenses1 = State()
    expenses2 = State()
    expenses3 = State()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'Привет, {message.from_user.full_name}! Я ваш финансовый помощник', reply_markup=keyboards)

@dp.message(F.text == 'Зарегистрироваться в боте')
async def cmd_register(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    # проверка на уже зарегистрированного пользователя
    user = cursor.fetchone()
    if user:
        await message.answer('Вы уже зарегистрированы в боте')
    else:
        cursor.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()
        await message.answer('Вы успешно зарегистрированы в боте')

@dp.message(F.text == 'Курс валют')
async def cmd_exchange_rates(message: Message):
    url = f'https://v6.exchangerate-api.com/v6/{EXCHANGE_RATES_API}/latest/USD'
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            await message.answer('Не удалось получить курс валют')
            return
        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']
        cny_to_usd = data['conversion_rates']['CNY']
        eur_to_rub = usd_to_rub / eur_to_usd
        cny_to_rub = usd_to_rub / cny_to_usd
        await message.answer(f'1 USD = {usd_to_rub:.2f} RUB\n'
                             f'1 EUR = {eur_to_rub:.2f} RUB\n'
                             f'1 CNY = {cny_to_rub:.2f} RUB')
    except:
        await message.answer('Произошла ошибка')

@dp.message(F.text == 'Советы по экономии')
async def cmd_tips(message: Message):
    tips = [
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и акционным ценам.",
    ]
    tip = random.choice(tips)
    await message.answer(tip)

@dp.message(F.text == 'Личные финансы')
async def cmd_finance(message: Message, state: FSMContext):
    await state.set_state(FinancesForm.category1)
    await message.answer('Выберите 1/3 категорию расходов: ')

@dp.message(FinancesForm.category1)
async def category1(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.answer('Введите расходы для категории 1: ')

@dp.message(FinancesForm.expenses1)
async def expenses1(message: Message, state: FSMContext):
    await state.update_data(expenses1=float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.answer('Выберите 2/3 категорию расходов: ')

@dp.message(FinancesForm.category2)
async def category2(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.answer('Введите расходы для категории 2: ')

@dp.message(FinancesForm.expenses2)
async def expenses2(message: Message, state: FSMContext):
    await state.update_data(expenses2=float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.answer('Выберите 3/3 категорию расходов: ')

@dp.message(FinancesForm.category3)
async def category3(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.answer('Введите расходы для категории 3: ')

@dp.message(FinancesForm.expenses3)
async def expenses3(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id
    cursor.execute('''UPDATE users SET category1 = ?, category2 = ?, category3 = ?,
     expenses1 = ?, expenses2 = ?, expenses3 = ? WHERE telegram_id = ?''',
                   (data['category1'], data['category2'], data['category3'],
                    data['expenses1'], data['expenses2'], float(message.text), telegram_id))
    conn.commit()
    await state.clear()
    await message.answer('Расходы сохранены')

@dp.message(F.text == 'Посмотреть БД')
async def cmd_BD(message: Message):
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        user_info = ','.join(map(str, user))
        await message.answer(user_info)

async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())